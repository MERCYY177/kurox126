#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C13: localize every web-usable merchandise image into assets/images.

Only the display-layer fields `image` / `fallbackImage` and the static image-count
copy are changed. Evidence/source URLs are retained as metadata.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
IMG_DIR = ROOT / "assets" / "images"
REPORT = ROOT / "C13_六张定点修复_全本地图片审计.txt"

EXPECTED_MISSING = {
    "KR-MER-0010", "KR-MER-0223", "KR-MER-0333", "KR-MER-0603",
    "KR-MER-0624", "KR-MER-0627", "KR-MER-0653", "KR-MER-0668",
    "KR-MER-0669", "KR-MER-0711", "KR-MER-0783", "KR-MER-0798",
    "KR-MER-0828",
}

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36"
)


def load_items(html: str):
    m = re.search(r"const ITEMS=(\[.*?\]);\n", html, re.S)
    if not m:
        raise RuntimeError("找不到 const ITEMS 数据块")
    return m, json.loads(m.group(1))


def sniff_ext(data: bytes, content_type: str = "") -> str | None:
    c = (content_type or "").lower().split(";", 1)[0].strip()
    if data[:12].startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if len(data) > 12 and data[4:12] in (b"ftypavif", b"ftypavis"):
        return ".avif"
    by_ct = {
        "image/webp": ".webp", "image/jpeg": ".jpg", "image/jpg": ".jpg",
        "image/png": ".png", "image/gif": ".gif", "image/avif": ".avif",
    }
    if c in by_ct and len(data) > 512:
        return by_ct[c]
    return None


def is_imageish_url(url: str) -> bool:
    if not url or not url.startswith(("http://", "https://")):
        return False
    low = url.lower()
    return any(x in low for x in (
        ".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif",
        "photo.php", "resize_image.php", "/images/", "/img/", "/upload/"
    ))


def suruga_id(item: dict, url: str) -> str | None:
    candidates = [item.get("sourceUrl", ""), url, item.get("imageSourceUrl", "")]
    for s in candidates:
        if not s:
            continue
        m = re.search(r"/(?:detail|kaitori_detail)/(\d{6,12})", s)
        if m:
            return m.group(1)
        m = re.search(r"(?:game/|shinaban=)(\d{6,12})", s)
        if m:
            return m.group(1)
        m = re.search(r"/(\d{6,12})m?\.jpg", s)
        if m:
            return m.group(1)
    return None


def proxy(url: str) -> str:
    # wsrv fetches the origin server-side, useful when a source blocks hotlinks/regions.
    return "https://images.weserv.nl/?url=" + urllib.parse.quote(url, safe="") + "&output=webp&q=90"


def candidates(item: dict) -> list[str]:
    primary = item.get("fallbackImage", "") or item.get("imageSourceUrl", "")
    out: list[str] = []

    def add(u: str):
        if u and u.startswith(("http://", "https://")) and u not in out:
            out.append(u)

    add(primary)
    isu = item.get("imageSourceUrl", "")
    if is_imageish_url(isu):
        add(isu)

    pid = suruga_id(item, primary)
    if pid:
        add(f"https://cdn.suruga-ya.jp/database/pics_webp/game/{pid}.jpg.webp")
        add(f"https://www.suruga-ya.jp/database/pics_light/game/{pid}.jpg")
        add(f"https://www.suruga-ya.jp/database/photo.php?shinaban={pid}&size=m")

    # Proxy mirrors are retries, not display URLs. Final HTML never points at them.
    originals = list(out)
    for u in originals:
        add(proxy(u))
    return out


def fetch(url: str, referer: str = "", timeout: int = 35) -> tuple[bytes, str]:
    headers = {
        "User-Agent": UA,
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.8,en;q=0.6",
    }
    if referer and referer.startswith("http"):
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(20 * 1024 * 1024 + 1)
        if len(data) > 20 * 1024 * 1024:
            raise RuntimeError("图片超过20MB安全上限")
        return data, r.headers.get("Content-Type", "")


def find_existing(item_id: str) -> Path | None:
    for ext in (".webp", ".jpg", ".jpeg", ".png", ".gif", ".avif"):
        p = IMG_DIR / f"{item_id}{ext}"
        if p.exists() and p.stat().st_size > 300:
            try:
                data = p.read_bytes()[:64]
                if sniff_ext(data, ""):
                    return p
            except OSError:
                pass
    return None


def download_item(item: dict) -> tuple[Path | None, str]:
    iid = item["id"]
    existing = find_existing(iid)
    if existing:
        return existing, "已有本地文件"

    errs = []
    referer = item.get("sourceUrl", "")
    for u in candidates(item):
        for attempt in range(2):
            try:
                data, ctype = fetch(u, referer=referer)
                ext = sniff_ext(data, ctype)
                if not ext:
                    head = data[:120].decode("utf-8", "ignore").replace("\n", " ")
                    raise RuntimeError(f"返回内容不是图片: {ctype} {head[:60]}")
                IMG_DIR.mkdir(parents=True, exist_ok=True)
                p = IMG_DIR / f"{iid}{ext}"
                tmp = p.with_suffix(p.suffix + ".part")
                tmp.write_bytes(data)
                os.replace(tmp, p)
                return p, u
            except Exception as e:
                errs.append(f"{u} -> {type(e).__name__}: {e}")
                if attempt == 0:
                    time.sleep(1.2)
    return None, " | ".join(errs[-6:])


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def audit(items: list[dict]) -> list[str]:
    errors = []
    if len(items) != 863:
        errors.append(f"商品总数异常：{len(items)}，预期863")

    blank = {i["id"] for i in items if not i.get("image") and not i.get("fallbackImage")}
    if blank != EXPECTED_MISSING:
        errors.append("结构性空图ID不等于冻结13项：" + ", ".join(sorted(blank)))

    remote_display = [i["id"] for i in items if str(i.get("image", "")).startswith("http") or i.get("fallbackImage")]
    if remote_display:
        errors.append(f"仍有外链展示源 {len(remote_display)} 条：" + ", ".join(remote_display[:30]))

    locals_ = [i for i in items if str(i.get("image", "")).startswith("assets/images/")]
    if len(locals_) != 850:
        errors.append(f"本地图片节点={len(locals_)}，预期850")

    missing_files = []
    for i in locals_:
        p = ROOT / i["image"]
        if not p.is_file() or p.stat().st_size <= 300:
            missing_files.append(f"{i['id']}:{i['image']}")
    if missing_files:
        errors.append(f"本地路径缺文件 {len(missing_files)} 条：" + ", ".join(missing_files[:30]))
    return errors


def main() -> int:
    html = INDEX.read_text(encoding="utf-8")
    m, items = load_items(html)

    # Guard the frozen true-missing pool before any mutation.
    pre_blank = {i["id"] for i in items if not i.get("image") and not i.get("fallbackImage")}
    if pre_blank != EXPECTED_MISSING:
        REPORT.write_text(
            "C13中止：输入版本的真实待补图集合与冻结13项不一致。\n"
            f"实际：{', '.join(sorted(pre_blank))}\n",
            encoding="utf-8",
        )
        print(REPORT.read_text(encoding="utf-8"), file=sys.stderr)
        return 3

    todo = [i for i in items if not i.get("image") and i.get("fallbackImage")]
    print(f"C13：待本地化外链节点 {len(todo)}；已有本地 {sum(bool(i.get('image')) for i in items)}；真缺图 {len(pre_blank)}")

    successes: dict[str, Path] = {}
    source_used: dict[str, str] = {}
    failures: dict[str, str] = {}

    # Parallelism keeps a 453-image build practical on GitHub Actions while
    # staying conservative enough not to hammer any single origin too hard.
    workers = max(1, min(int(os.environ.get("C13_WORKERS", "8")), 12))
    print(f"并发下载线程：{workers}")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(download_item, item): item for item in todo}
        done = 0
        for fut in as_completed(futures):
            item = futures[fut]
            iid = item["id"]
            done += 1
            try:
                p, used = fut.result()
            except Exception as e:
                p, used = None, f"线程异常 {type(e).__name__}: {e}"
            if p:
                successes[iid] = p
                source_used[iid] = used
                print(f"[{done:03d}/{len(todo)}] OK   {iid} -> {p.name}")
            else:
                failures[iid] = used
                print(f"[{done:03d}/{len(todo)}] FAIL {iid}", file=sys.stderr)

    lines = [
        "鬼龍紅郎 周边图鉴 C13 六张定点修复・全本地图片审计",
        "=" * 56,
        f"商品总数：{len(items)}",
        f"输入已有本地节点：{sum(bool(i.get('image')) for i in items)}",
        f"本轮需要下载：{len(todo)}",
        f"本轮下载成功：{len(successes)}",
        f"本轮下载失败：{len(failures)}",
        f"冻结真缺图：{len(EXPECTED_MISSING)}",
        "真缺图ID：" + " / ".join(sorted(EXPECTED_MISSING)),
    ]

    if failures:
        lines += ["", "失败项（未改写index.html；可直接重跑，已成功文件会复用）："]
        for iid, err in failures.items():
            lines.append(f"- {iid}: {err}")
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n有 {len(failures)} 条下载失败。index.html 未改写；详见 {REPORT.name}", file=sys.stderr)
        return 2

    # Only after every remote image has been captured do we switch the display layer.
    for item in items:
        iid = item["id"]
        if iid in successes:
            item["image"] = rel(successes[iid])
        if item.get("image"):
            item["fallbackImage"] = ""

    new_json = json.dumps(items, ensure_ascii=False, separators=(",", ":"))
    new_html = html[:m.start(1)] + new_json + html[m.end(1):]
    new_html = re.sub(
        r"<section class=\"intro\"><div><h1>鬼龍紅郎</h1><p>.*?</p>",
        '<section class="intro"><div><h1>鬼龍紅郎</h1><p>863 款 Active · 850 款本地图片 · 外链展示 0 · 最终待补 13 款</p>',
        new_html,
        count=1,
        flags=re.S,
    )
    INDEX.write_text(new_html, encoding="utf-8")

    # Reparse the written HTML and audit the actual output.
    _, final_items = load_items(INDEX.read_text(encoding="utf-8"))
    errors = audit(final_items)
    lines += [
        "",
        "最终验收：",
        f"- 本地图片节点：{sum(str(i.get('image','')).startswith('assets/images/') for i in final_items)}",
        f"- 外链展示源：{sum(str(i.get('image','')).startswith('http') or bool(i.get('fallbackImage')) for i in final_items)}",
        f"- 结构性空图：{sum(not i.get('image') and not i.get('fallbackImage') for i in final_items)}",
        f"- 本地路径缺文件：{sum(str(i.get('image','')).startswith('assets/images/') and not (ROOT / i['image']).is_file() for i in final_items)}",
    ]
    if errors:
        lines += ["", "验收失败："] + ["- " + x for x in errors]
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(errors), file=sys.stderr)
        return 4

    lines += [
        "- 结果：PASS",
        "",
        "说明：sourceUrl / imageSourceUrl 作为证据元数据继续保留；网页展示不再依赖这些外链。",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("C13全本地化完成：850本地图 / 0外链展示 / 13真缺图。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

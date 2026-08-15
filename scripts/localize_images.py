#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; INDEX=ROOT/'index.html'; IMG_DIR=ROOT/'assets/images'; REPORT=ROOT/'C13.2_图片归集审计.txt'
EXPECTED_MISSING={"KR-MER-0010","KR-MER-0223","KR-MER-0333","KR-MER-0603","KR-MER-0624","KR-MER-0627","KR-MER-0653","KR-MER-0668","KR-MER-0669","KR-MER-0711","KR-MER-0783","KR-MER-0798","KR-MER-0828"}
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36'
def load(s):
 m=re.search(r'const ITEMS=(\[.*?\]);\n',s,re.S)
 if not m: raise RuntimeError('ITEMS not found')
 return m,json.loads(m.group(1))
def ext(data,ct=''):
 if data[:12].startswith(b'RIFF') and data[8:12]==b'WEBP': return '.webp'
 if data.startswith(b'\xff\xd8\xff'): return '.jpg'
 if data.startswith(b'\x89PNG\r\n\x1a\n'): return '.png'
 if data[:6] in (b'GIF87a',b'GIF89a'): return '.gif'
 c=(ct or '').lower()
 if 'image/jpeg' in c and len(data)>512:return '.jpg'
 if 'image/png' in c and len(data)>512:return '.png'
 if 'image/webp' in c and len(data)>512:return '.webp'
 return None
def add(lst,u):
 if u and u.startswith(('http://','https://')) and u not in lst: lst.append(u)
def suruga_id(it):
 for s in (it.get('fallbackImage',''),it.get('imageSourceUrl',''),it.get('sourceUrl','')):
  for pat in (r'/(?:detail|kaitori_detail)/(\d{6,12})',r'(?:game/|shinaban=)(\d{6,12})',r'/(\d{6,12})m?\.jpg'):
   m=re.search(pat,s or '')
   if m:return m.group(1)
def candidates(it):
 out=[]; add(out,it.get('fallbackImage','')); add(out,it.get('imageSourceUrl',''))
 pid=suruga_id(it)
 if pid:
  add(out,f'https://cdn.suruga-ya.jp/database/pics_webp/game/{pid}.jpg.webp')
  add(out,f'https://www.suruga-ya.jp/database/pics_light/game/{pid}.jpg')
  add(out,f'https://www.suruga-ya.jp/database/photo.php?shinaban={pid}&size=m')
 originals=list(out)
 for u in originals:
  q=urllib.parse.quote(u,safe='')
  add(out,'https://images.weserv.nl/?url='+q+'&output=webp&q=92')
  add(out,'https://wsrv.nl/?url='+q+'&output=webp&q=92')
 return out
def fetch(u,referer=''):
 h={'User-Agent':UA,'Accept':'image/avif,image/webp,image/apng,image/*,*/*;q=0.8','Accept-Language':'ja,en-US;q=0.8,en;q=0.6'}
 if referer.startswith('http'):h['Referer']=referer
 req=urllib.request.Request(u,headers=h)
 with urllib.request.urlopen(req,timeout=35) as r:
  b=r.read(20*1024*1024+1)
  if len(b)>20*1024*1024:raise RuntimeError('too large')
  return b,r.headers.get('Content-Type','')
def scrape_page_candidates(it):
 u=it.get('sourceUrl','')
 if not u.startswith('http'):return []
 try:
  req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept-Language':'ja,en;q=0.7'})
  with urllib.request.urlopen(req,timeout=25) as r: raw=r.read(4*1024*1024).decode('utf-8','ignore')
 except Exception:return []
 vals=[]
 for pat in [r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',r'<img[^>]+src=["\']([^"\']+)["\']']:
  for x in re.findall(pat,raw,re.I):
   x=urllib.parse.urljoin(u,x.replace('&amp;','&'))
   if re.search(r'\.(?:jpg|jpeg|png|webp|gif)(?:[?&#]|$)',x,re.I) and x not in vals:vals.append(x)
   if len(vals)>=15:return vals
 return vals
def existing(iid):
 for p in IMG_DIR.glob(iid+'.*'):
  if p.is_file() and p.stat().st_size>300:return p
 return None
def get_one(it):
 iid=it['id']; p=existing(iid)
 if p:return p,'existing'
 errs=[]; cands=candidates(it)
 # direct/proxy candidates, then scrape source page once if needed
 for phase in range(2):
  if phase==1:
   for u in scrape_page_candidates(it): add(cands,u)
  for u in list(cands):
   for attempt in range(3):
    try:
     b,ct=fetch(u,it.get('sourceUrl','')); e=ext(b,ct)
     if not e:raise RuntimeError('not image')
     IMG_DIR.mkdir(parents=True,exist_ok=True); p=IMG_DIR/(iid+e); tmp=Path(str(p)+'.part');tmp.write_bytes(b);os.replace(tmp,p);return p,u
    except Exception as ex:
     errs.append(type(ex).__name__+':'+str(ex)[:100]); time.sleep(0.6*(attempt+1))
 return None,' | '.join(errs[-8:])
def main():
 html=INDEX.read_text('utf-8');m,items=load(html)
 blank={i['id'] for i in items if not i.get('image') and not i.get('fallbackImage')}
 if blank!=EXPECTED_MISSING:
  REPORT.write_text('输入真缺图集合异常：'+','.join(sorted(blank)),encoding='utf-8');return 3
 todo=[i for i in items if not i.get('image') and i.get('fallbackImage')]
 success={};fail={};workers=max(1,min(int(os.environ.get('C132_WORKERS','8')),12))
 with ThreadPoolExecutor(max_workers=workers) as pool:
  fs={pool.submit(get_one,it):it for it in todo}
  for fut in as_completed(fs):
   it=fs[fut];iid=it['id']
   try:p,src=fut.result()
   except Exception as e:p,src=None,repr(e)
   if p:success[iid]=p
   else:fail[iid]=src
 # IMPORTANT: commit every success even if a few sources remain unavailable.
 for it in items:
  iid=it['id']
  if iid in success:
   it['image']='assets/images/'+success[iid].name;it['fallbackImage']=''
 newjson=json.dumps(items,ensure_ascii=False,separators=(',',':'))
 newhtml=html[:m.start(1)]+newjson+html[m.end(1):]
 local=sum(str(i.get('image','')).startswith('assets/images/') for i in items);remote=sum(not i.get('image') and bool(i.get('fallbackImage')) for i in items)
 newhtml=re.sub(r'<section class="intro"><div><h1>鬼龍紅郎</h1><p>.*?</p>',f'<section class="intro"><div><h1>鬼龍紅郎</h1><p>862 款 Active · 已本地 {local} 款 · 待自动归集 {remote} 款 · 真缺图 13 款</p>',newhtml,count=1,flags=re.S)
 INDEX.write_text(newhtml,'utf-8')
 lines=[f'本轮输入远程：{len(todo)}',f'成功本地化：{len(success)}',f'仍待重试：{len(fail)}',f'最终本地：{local}',f'最终外链：{remote}','真缺图：13']
 if fail:
  lines+=['','仍待重试ID：']+[f'- {k}: {v}' for k,v in sorted(fail.items())]
 REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 # Returning success deliberately allows GitHub to commit all recovered images.
 print('\n'.join(lines[:6]));return 0
if __name__=='__main__':raise SystemExit(main())

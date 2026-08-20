$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$imgDir = Join-Path $root "assets\images"
New-Item -ItemType Directory -Force -Path $imgDir | Out-Null
$headers = @{ "Referer" = "https://qiandao.com/"; "User-Agent" = "Mozilla/5.0" }
$items = @(
  @{ Id="KR-MER-1047"; Url="https://treasure.qiandaocdn.com/treasure/images/f6gv0yhdaVM.png"; File="KR-MER-1047.png" },
  @{ Id="KR-MER-1052"; Url="https://treasure.qiandaocdn.com/treasure/images/f6gv0vbdag3.png"; File="KR-MER-1052.png" },
  @{ Id="KR-MER-1054"; Url="https://treasure.qiandaocdn.com/treasure/images/f6gv0rrDunF.png"; File="KR-MER-1054.png" },
  @{ Id="KR-MER-1055"; Url="https://treasure.qiandaocdn.com/treasure/images/8818378ed44dfb755823f87e5e192730.png"; File="KR-MER-1055.png" },
  @{ Id="KR-MER-1056"; Url="https://treasure.qiandaocdn.com/treasure/images/b22536039425f63acff495bd67a9f662.png"; File="KR-MER-1056.png" },
  @{ Id="KR-MER-1057"; Url="https://treasure.qiandaocdn.com/treasure/images/901f6a5acf18994d6bf2979e840b03a2.png"; File="KR-MER-1057.png" },
  @{ Id="KR-MER-1058"; Url="https://public.qiandaocdn.com/interior/images/gcn5M4ya6V.png"; File="KR-MER-1058.png" },
  @{ Id="KR-MER-1059"; Url="https://public.qiandaocdn.com/interior/images/gcgrNP9FUZ.png"; File="KR-MER-1059.png" },
  @{ Id="KR-MER-1060"; Url="https://public.qiandaocdn.com/interior/images/gPocbQwONa.png"; File="KR-MER-1060.png" },
  @{ Id="KR-MER-1061"; Url="https://public.qiandaocdn.com/interior/images/gPftnnIDCK.png"; File="KR-MER-1061.png" },
  @{ Id="KR-MER-1062"; Url="https://public.qiandaocdn.com/interior/images/nrRBl4ugy3.png"; File="KR-MER-1062.png" },
  @{ Id="KR-MER-1063"; Url="https://public.qiandaocdn.com/interior/images/nrta6EFUcx.png"; File="KR-MER-1063.png" },
  @{ Id="KR-MER-1066"; Url="https://treasure.qiandaocdn.com/treasure/images/fv4vlELkQai.png"; File="KR-MER-1066.png" },
  @{ Id="KR-MER-1067"; Url="https://treasure.qiandaocdn.com/treasure/images/a8fdd8b6b8fa69a20b5734b9f8d2ba5d.png"; File="KR-MER-1067.png" },
  @{ Id="KR-MER-1068"; Url="https://treasure.qiandaocdn.com/treasure/images/2688469b6378b02eaecc48bac79e8837.png"; File="KR-MER-1068.png" },
  @{ Id="KR-MER-1074"; Url="https://treasure.qiandaocdn.com/treasure/images/6392df58cdd2e0e5ccb3bb32f9b8ec08.png"; File="KR-MER-1074.png" },
  @{ Id="KR-MER-1078"; Url="https://treasure.qiandaocdn.com/treasure/images/fvy4UidFF1l.png"; File="KR-MER-1078.png" },
  @{ Id="KR-MER-1092"; Url="https://treasure.qiandaocdn.com/treasure/images/f6zSGUEgUMF.png"; File="KR-MER-1092.png" },
  @{ Id="KR-MER-1107"; Url="https://treasure.qiandaocdn.com/treasure/images/firzqKq0LuS.png"; File="KR-MER-1107.png" },
  @{ Id="KR-MER-1115"; Url="https://treasure.qiandaocdn.com/treasure/images/f8U6pMVf0lG.png"; File="KR-MER-1115.png" },
  @{ Id="KR-MER-1116"; Url="https://treasure.qiandaocdn.com/treasure/images/f8U6pMVf0lW.png"; File="KR-MER-1116.png" },
  @{ Id="KR-MER-1120"; Url="https://treasure.qiandaocdn.com/treasure/images/86eda7f1b88d9eeca321a981a8574bfd.png"; File="KR-MER-1120.png" },
  @{ Id="KR-MER-1123"; Url="https://treasure.qiandaocdn.com/treasure/images/81628B39DAEEF62F0D3C5F9861730879.jpeg"; File="KR-MER-1123.jpeg" },
  @{ Id="KR-MER-1125"; Url="https://treasure.qiandaocdn.com/treasure/images/7e9d20402a5854e934ae70f36e77358b.png"; File="KR-MER-1125.png" },
  @{ Id="KR-MER-1126"; Url="https://treasure.qiandaocdn.com/treasure/images/e8f2808744d2d3b1b5152b8bd9d161ae.png"; File="KR-MER-1126.png" },
  @{ Id="KR-MER-1127"; Url="https://public.qiandaocdn.com/interior/images/gzJpn4NK8X.png"; File="KR-MER-1127.png" },
  @{ Id="KR-MER-1128"; Url="https://treasure.qiandaocdn.com/treasure/images/aa5cca1027ac5bf53915a2bf67e10a2e.png"; File="KR-MER-1128.png" },
  @{ Id="KR-MER-1129"; Url="https://treasure.qiandaocdn.com/treasure/images/1de65dd3d32862c77d2b23ca820d9872.png"; File="KR-MER-1129.png" },
  @{ Id="KR-MER-1130"; Url="https://treasure.qiandaocdn.com/treasure/images/ffyMaFpXMDO.png"; File="KR-MER-1130.png" },
  @{ Id="KR-MER-1131"; Url="https://treasure.qiandaocdn.com/treasure/images/fiIYpjJo4wc.png"; File="KR-MER-1131.png" },
  @{ Id="KR-MER-1132"; Url="https://treasure.qiandaocdn.com/treasure/images/Ewd90RQOMe.png"; File="KR-MER-1132.png" },
  @{ Id="KR-MER-1134"; Url="https://treasure.qiandaocdn.com/treasure/images/frIRFABIg5r.png"; File="KR-MER-1134.png" },
  @{ Id="KR-MER-1135"; Url="https://treasure.qiandaocdn.com/treasure/images/IMEgLhgvSC.png"; File="KR-MER-1135.png" },
  @{ Id="KR-MER-1136"; Url="https://treasure.qiandaocdn.com/treasure/images/f8U6zXogYO1.png"; File="KR-MER-1136.png" },
  @{ Id="KR-MER-1137"; Url="https://treasure.qiandaocdn.com/treasure/images/43871dc09ecfb3404303c214e6923f91.png"; File="KR-MER-1137.png" },
  @{ Id="KR-MER-1138"; Url="https://treasure.qiandaocdn.com/treasure/images/fBFpea0NZap.png"; File="KR-MER-1138.png" },
  @{ Id="KR-MER-1139"; Url="https://treasure.qiandaocdn.com/treasure/images/fiEeU5j1mqD.png"; File="KR-MER-1139.png" },
  @{ Id="KR-MER-1140"; Url="https://treasure.qiandaocdn.com/treasure/images/f56LO8beMXh.png"; File="KR-MER-1140.png" }
)
$ok = 0; $failed = @()
foreach ($x in $items) {
  $dest = Join-Path $imgDir $x.File
  try {
    Invoke-WebRequest -Uri $x.Url -OutFile $dest -Headers $headers -UseBasicParsing
    $ok++
    Write-Host ("OK  " + $x.Id + " -> " + $x.File)
  } catch {
    $failed += $x.Id
    Write-Warning ("FAIL " + $x.Id + ": " + $_.Exception.Message)
  }
}
Write-Host ""
Write-Host ("Downloaded: " + $ok + "/" + $items.Count)
if ($failed.Count -gt 0) { Write-Host ("Failed: " + ($failed -join ", ")) }
Write-Host "The website prefers these local files and automatically falls back to Qiandao remote images if a local file is missing."
Read-Host "Press Enter to close"
$base = "http://18.215.143.250:3000"

Write-Output "=== Wayback availability with http:// prefix ==="
try { $r = Invoke-WebRequest -Uri "https://archive.org/wayback/available?url=http://18.215.143.250:3000&timestamp=20241201" -TimeoutSec 15 -UseBasicParsing; Write-Output $r.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Wayback availability 20250101 ==="
try { $r2 = Invoke-WebRequest -Uri "https://archive.org/wayback/available?url=http://18.215.143.250:3000&timestamp=20250101" -TimeoutSec 15 -UseBasicParsing; Write-Output $r2.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Wayback availability 20251001 ==="
try { $r3 = Invoke-WebRequest -Uri "https://archive.org/wayback/available?url=http://18.215.143.250:3000&timestamp=20251001" -TimeoutSec 15 -UseBasicParsing; Write-Output $r3.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Wayback availability 20261001 ==="
try { $r4 = Invoke-WebRequest -Uri "https://archive.org/wayback/available?url=http://18.215.143.250:3000&timestamp=20261001" -TimeoutSec 15 -UseBasicParsing; Write-Output $r4.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== crt.sh ==="
try { $r5 = Invoke-WebRequest -Uri "https://crt.sh/?q=18.215.143.250&output=json" -TimeoutSec 15 -UseBasicParsing; Write-Output $r5.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== middleware-manifest ==="
try { $r7 = Invoke-WebRequest -Uri "$base/_next/static/qyfJNY9j0_iFz3SifWy5m/middleware-manifest.js" -TimeoutSec 8 -UseBasicParsing; Write-Output $r7.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== pages-manifest ==="
try { $r15 = Invoke-WebRequest -Uri "$base/_next/static/qyfJNY9j0_iFz3SifWy5m/pages-manifest.json" -TimeoutSec 8 -UseBasicParsing; Write-Output $r15.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== HEAD request ==="
try { $r25 = Invoke-WebRequest -Uri "$base/" -Method HEAD -TimeoutSec 8 -UseBasicParsing; $r25.Headers | Format-List } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Last-Modified for page chunk ==="
try { $r26 = Invoke-WebRequest -Uri "$base/_next/static/chunks/app/page-dcea1cd040fd23a5.js" -TimeoutSec 8 -UseBasicParsing; $r26.Headers | Format-List } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Last-Modified for 445 chunk ==="
try { $r27 = Invoke-WebRequest -Uri "$base/_next/static/chunks/445-e015270e866f7521.js" -TimeoutSec 8 -UseBasicParsing; $r27.Headers | Format-List } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Last-Modified for 517 chunk ==="
try { $r28 = Invoke-WebRequest -Uri "$base/_next/static/chunks/517-4e633ead85d0d9a9.js" -TimeoutSec 8 -UseBasicParsing; $r28.Headers | Format-List } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Last-Modified for main-app chunk ==="
try { $r29 = Invoke-WebRequest -Uri "$base/_next/static/chunks/main-app-1dd263df69101e7e.js" -TimeoutSec 8 -UseBasicParsing; $r29.Headers | Format-List } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Last-Modified for polyfills ==="
try { $r30 = Invoke-WebRequest -Uri "$base/_next/static/chunks/polyfills-42372ed130431b0a.js" -TimeoutSec 8 -UseBasicParsing; $r30.Headers | Format-List } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Last-Modified for stock detail chunk ==="
try { $r31 = Invoke-WebRequest -Uri "$base/_next/static/chunks/app/stock/%5Bsymbol%5D/page-6608109a205873bb.js" -TimeoutSec 8 -UseBasicParsing; $r31.Headers | Format-List } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Last-Modified for 4bd1b696 ==="
try { $r32 = Invoke-WebRequest -Uri "$base/_next/static/chunks/4bd1b696-e3d95b76f82505a1.js" -TimeoutSec 8 -UseBasicParsing; $r32.Headers | Format-List } catch { Write-Output $_.Exception.Message }

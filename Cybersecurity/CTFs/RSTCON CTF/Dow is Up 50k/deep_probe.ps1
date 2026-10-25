$base = "http://18.215.143.250:3000"

# Get full stock detail page
Write-Output "=== /stock/AAPL full content ==="
try { $r = Invoke-WebRequest -Uri "$base/stock/AAPL" -TimeoutSec 10 -UseBasicParsing; Write-Output $r.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /stock/FLAG ==="
try { $r2 = Invoke-WebRequest -Uri "$base/stock/FLAG" -TimeoutSec 10 -UseBasicParsing; Write-Output $r2.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /flag ==="
try { $r3 = Invoke-WebRequest -Uri "$base/flag" -TimeoutSec 10 -UseBasicParsing; Write-Output $r3.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /admin ==="
try { $r4 = Invoke-WebRequest -Uri "$base/admin" -TimeoutSec 10 -UseBasicParsing; Write-Output $r4.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /secret ==="
try { $r5 = Invoke-WebRequest -Uri "$base/secret" -TimeoutSec 10 -UseBasicParsing; Write-Output $r5.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /api/stock/AAPL ==="
try { $r6 = Invoke-WebRequest -Uri "$base/api/stock/AAPL" -TimeoutSec 10 -UseBasicParsing; Write-Output $r6.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /api/stock ==="
try { $r7 = Invoke-WebRequest -Uri "$base/api/stock" -TimeoutSec 10 -UseBasicParsing; Write-Output $r7.Content } catch { Write-Output $_.Exception.Message }

# Check for the stock detail page chunk
Write-Output "`n=== stock detail chunk ==="
try { $r8 = Invoke-WebRequest -Uri "$base/_next/static/chunks/app/stock/%5Bsymbol%5D/page-6608109a205873bb.js" -TimeoutSec 10 -UseBasicParsing; Write-Output $r8.Content } catch { Write-Output $_.Exception.Message }

# Check for common Next.js routes
Write-Output "`n=== /_next/static/chunks/app/layout ==="
try { $r9 = Invoke-WebRequest -Uri "$base/_next/static/chunks/app/layout.js" -TimeoutSec 10 -UseBasicParsing; Write-Output $r9.Content } catch { Write-Output $_.Exception.Message }

# Check for 445 chunk (loaded on stock page)
Write-Output "`n=== 445 chunk ==="
try { $r10 = Invoke-WebRequest -Uri "$base/_next/static/chunks/445-e015270e866f7521.js" -TimeoutSec 10 -UseBasicParsing; Write-Output $r10.Content } catch { Write-Output $_.Exception.Message }

# Try the 517 chunk
Write-Output "`n=== 517 chunk ==="
try { $r11 = Invoke-WebRequest -Uri "$base/_next/static/chunks/517-4e633ead85d0d9a9.js" -TimeoutSec 10 -UseBasicParsing; Write-Output $r11.Content.Substring(0, [Math]::Min(2000, $r11.Content.Length)) } catch { Write-Output $_.Exception.Message }

# Try main-app chunk
Write-Output "`n=== main-app chunk ==="
try { $r12 = Invoke-WebRequest -Uri "$base/_next/static/chunks/main-app-1dd263df69101e7e.js" -TimeoutSec 10 -UseBasicParsing; Write-Output $r12.Content.Substring(0, [Math]::Min(2000, $r12.Content.Length)) } catch { Write-Output $_.Exception.Message }

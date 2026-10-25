$base = "http://18.215.143.250:3000"

# Check for git exposure
Write-Output "=== /.git/HEAD ==="
try { $r = Invoke-WebRequest -Uri "$base/.git/HEAD" -TimeoutSec 10 -UseBasicParsing; Write-Output $r.Content } catch { Write-Output $_.Exception.Message }

# Check for source maps
Write-Output "`n=== webpack JS chunk (first 500 chars) ==="
try { $r2 = Invoke-WebRequest -Uri "$base/_next/static/chunks/webpack-06b7f1618a9e9933.js" -TimeoutSec 10 -UseBasicParsing; Write-Output $r2.Content.Substring(0, [Math]::Min(500, $r2.Content.Length)) } catch { Write-Output $_.Exception.Message }

# Check for build manifest
Write-Output "`n=== /_next/static/chunks/ ==="
try { $r3 = Invoke-WebRequest -Uri "$base/_next/static/chunks/" -TimeoutSec 10 -UseBasicParsing; Write-Output $r3.Content.Substring(0, [Math]::Min(1000, $r3.Content.Length)) } catch { Write-Output $_.Exception.Message }

# Check for BUILD_ID
Write-Output "`n=== /_next/BUILD_ID ==="
try { $r4 = Invoke-WebRequest -Uri "$base/_next/BUILD_ID" -TimeoutSec 10 -UseBasicParsing; Write-Output $r4.Content } catch { Write-Output $_.Exception.Message }

# Check for build manifest
Write-Output "`n=== /_next/static/buildManifest.json ==="
try { $r5 = Invoke-WebRequest -Uri "$base/_next/static/buildManifest.json" -TimeoutSec 10 -UseBasicParsing; Write-Output $r5.Content } catch { Write-Output $_.Exception.Message }

# Check for source map
Write-Output "`n=== webpack source map ==="
try { $r6 = Invoke-WebRequest -Uri "$base/_next/static/chunks/webpack-06b7f1618a9e9933.js.map" -TimeoutSec 10 -UseBasicParsing; Write-Output $r6.Content.Substring(0, [Math]::Min(500, $r6.Content.Length)) } catch { Write-Output $_.Exception.Message }

# Check for the page chunk
Write-Output "`n=== page chunk ==="
try { $r7 = Invoke-WebRequest -Uri "$base/_next/static/chunks/app/page-dcea1cd040fd23a5.js" -TimeoutSec 10 -UseBasicParsing; Write-Output $r7.Content.Substring(0, [Math]::Min(2000, $r7.Content.Length)) } catch { Write-Output $_.Exception.Message }

# Check for api routes
Write-Output "`n=== /api/stocks ==="
try { $r8 = Invoke-WebRequest -Uri "$base/api/stocks" -TimeoutSec 10 -UseBasicParsing; Write-Output $r8.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /api/stocks/ ==="
try { $r9 = Invoke-WebRequest -Uri "$base/api/stocks/" -TimeoutSec 10 -UseBasicParsing; Write-Output $r9.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /api/portfolio ==="
try { $r10 = Invoke-WebRequest -Uri "$base/api/portfolio" -TimeoutSec 10 -UseBasicParsing; Write-Output $r10.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /api/watchlist ==="
try { $r11 = Invoke-WebRequest -Uri "$base/api/watchlist" -TimeoutSec 10 -UseBasicParsing; Write-Output $r11.Content } catch { Write-Output $_.Exception.Message }

# Check stock detail page
Write-Output "`n=== /stock/AAPL (first 1000 chars) ==="
try { $r12 = Invoke-WebRequest -Uri "$base/stock/AAPL" -TimeoutSec 10 -UseBasicParsing; Write-Output $r12.Content.Substring(0, [Math]::Min(1000, $r12.Content.Length)) } catch { Write-Output $_.Exception.Message }

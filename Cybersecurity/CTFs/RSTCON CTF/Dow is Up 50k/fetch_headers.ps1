$base = "http://18.215.143.250:3000"

# Get headers from main page
Write-Output "=== MAIN PAGE HEADERS ==="
$r = Invoke-WebRequest -Uri $base -TimeoutSec 15 -UseBasicParsing
$r.Headers | Format-List

# Try common Next.js API routes
Write-Output "`n=== /api/flag ==="
try { $r2 = Invoke-WebRequest -Uri "$base/api/flag" -TimeoutSec 10 -UseBasicParsing; Write-Output $r2.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /api ==="
try { $r3 = Invoke-WebRequest -Uri "$base/api" -TimeoutSec 10 -UseBasicParsing; Write-Output $r3.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /robots.txt ==="
try { $r4 = Invoke-WebRequest -Uri "$base/robots.txt" -TimeoutSec 10 -UseBasicParsing; Write-Output $r4.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /sitemap.xml ==="
try { $r5 = Invoke-WebRequest -Uri "$base/sitemap.xml" -TimeoutSec 10 -UseBasicParsing; Write-Output $r5.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /_next/data ==="
try { $r6 = Invoke-WebRequest -Uri "$base/_next/data" -TimeoutSec 10 -UseBasicParsing; Write-Output $r6.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /portfolio ==="
try { $r7 = Invoke-WebRequest -Uri "$base/portfolio" -TimeoutSec 10 -UseBasicParsing; Write-Output $r7.Content.Substring(0, [Math]::Min(2000, $r7.Content.Length)) } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /watchlist ==="
try { $r8 = Invoke-WebRequest -Uri "$base/watchlist" -TimeoutSec 10 -UseBasicParsing; Write-Output $r8.Content.Substring(0, [Math]::Min(2000, $r8.Content.Length)) } catch { Write-Output $_.Exception.Message }

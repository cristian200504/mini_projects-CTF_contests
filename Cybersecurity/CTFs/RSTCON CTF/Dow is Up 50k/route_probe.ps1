$base = "http://18.215.143.250:3000"

# Try routes from the description: SHOP NOW, PAY later, DASH home, cry in the BOX
$routes = @("/shop", "/pay", "/dash", "/box", "/dashboard", "/buy", "/cart", "/checkout", "/secret", "/admin", "/flag", "/hidden", "/api/flag", "/api/secret", "/api/hidden", "/api/admin")

foreach ($route in $routes) {
    Write-Output "=== $route ==="
    try {
        $r = Invoke-WebRequest -Uri "$base$route" -TimeoutSec 8 -UseBasicParsing
        $content = $r.Content
        if ($content.Length -gt 2000) {
            Write-Output $content.Substring(0, 2000)
        } else {
            Write-Output $content
        }
    } catch {
        Write-Output $_.Exception.Message
    }
    Write-Output ""
}

# Get the stock detail page JS chunk
Write-Output "=== stock detail page JS chunk ==="
try {
    $r2 = Invoke-WebRequest -Uri "$base/_next/static/chunks/app/stock/%5Bsymbol%5D/page-6608109a205873bb.js" -TimeoutSec 10 -UseBasicParsing
    Write-Output $r2.Content
} catch { Write-Output $_.Exception.Message }

# Try to call the searchStocks server action with "flag"
Write-Output "`n=== Search for 'flag' via Next.js RSC ==="
try {
    $headers = @{
        "Content-Type" = "text/plain;charset=UTF-8"
        "Next-Action" = "40881a01be516941afc21e3145707ceff4a34545af"
    }
    $body = '["flag"]'
    $r3 = Invoke-WebRequest -Uri "$base" -Method POST -Headers $headers -Body $body -TimeoutSec 10 -UseBasicParsing
    Write-Output $r3.Content
} catch { Write-Output $_.Exception.Message }

# Try Wayback Machine with different URL formats
Write-Output "`n=== Wayback CDX with port ==="
try {
    $r4 = Invoke-WebRequest -Uri "https://web.archive.org/cdx/search/cdx?url=18.215.143.250:3000/*&output=json&limit=20" -TimeoutSec 15 -UseBasicParsing
    Write-Output $r4.Content
} catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Wayback CDX mirror 2 ==="
try {
    $r5 = Invoke-WebRequest -Uri "https://web.archive.org/cdx/search/cdx?url=18.145.136.91:3000&output=json&limit=20" -TimeoutSec 15 -UseBasicParsing
    Write-Output $r5.Content
} catch { Write-Output $_.Exception.Message }

# Try to search for the site on Wayback Machine by IP without port
Write-Output "`n=== Wayback CDX no port ==="
try {
    $r6 = Invoke-WebRequest -Uri "https://web.archive.org/cdx/search/cdx?url=18.215.143.250&output=json&limit=20" -TimeoutSec 15 -UseBasicParsing
    Write-Output $r6.Content
} catch { Write-Output $_.Exception.Message }

# Check for package.json or other config files
Write-Output "`n=== /package.json ==="
try { $r7 = Invoke-WebRequest -Uri "$base/package.json" -TimeoutSec 8 -UseBasicParsing; Write-Output $r7.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /next.config ==="
try { $r8 = Invoke-WebRequest -Uri "$base/next.config" -TimeoutSec 8 -UseBasicParsing; Write-Output $r8.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /next.config.js ==="
try { $r9 = Invoke-WebRequest -Uri "$base/next.config.js" -TimeoutSec 8 -UseBasicParsing; Write-Output $r9.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /next.config.mjs ==="
try { $r10 = Invoke-WebRequest -Uri "$base/next.config.mjs" -TimeoutSec 8 -UseBasicParsing; Write-Output $r10.Content } catch { Write-Output $_.Exception.Message }

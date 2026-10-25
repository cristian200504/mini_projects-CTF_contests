$base = "http://18.215.143.250:3000"

# Get full stock detail page for AAPL
Write-Output "=== /stock/AAPL full ==="
try { 
    $r = Invoke-WebRequest -Uri "$base/stock/AAPL" -TimeoutSec 10 -UseBasicParsing
    # Extract all text content between script tags
    $content = $r.Content
    # Look for flag or interesting strings
    $matches = [regex]::Matches($content, '(?:flag|rstcon|RSTCON|FLAG|secret|hidden|date|created|built|modified)(?i)[^<]{0,200}')
    foreach ($m in $matches) { Write-Output "MATCH: $($m.Value)" }
    
    # Also get the stock detail chunk
    Write-Output "`n=== stock detail page JS ==="
    $r2 = Invoke-WebRequest -Uri "$base/_next/static/chunks/app/stock/%5Bsymbol%5D/page-6608109a205873bb.js" -TimeoutSec 10 -UseBasicParsing
    Write-Output $r2.Content
} catch { Write-Output $_.Exception.Message }

# Try to find server actions or API endpoints
Write-Output "`n=== /api/searchStocks ==="
try { 
    $r3 = Invoke-WebRequest -Uri "$base/api/searchStocks" -TimeoutSec 10 -UseBasicParsing
    Write-Output $r3.Content 
} catch { Write-Output $_.Exception.Message }

# Check for 445 chunk (loaded on stock detail)
Write-Output "`n=== 445 chunk ==="
try {
    $r4 = Invoke-WebRequest -Uri "$base/_next/static/chunks/445-e015270e866f7521.js" -TimeoutSec 10 -UseBasicParsing
    Write-Output $r4.Content
} catch { Write-Output $_.Exception.Message }

# Check for the 4bd1b696 chunk
Write-Output "`n=== 4bd1b696 chunk ==="
try {
    $r5 = Invoke-WebRequest -Uri "$base/_next/static/chunks/4bd1b696-e3d95b76f82505a1.js" -TimeoutSec 10 -UseBasicParsing
    Write-Output $r5.Content.Substring(0, [Math]::Min(3000, $r5.Content.Length))
} catch { Write-Output $_.Exception.Message }

# Try common hidden endpoints
Write-Output "`n=== /api/search ==="
try { $r6 = Invoke-WebRequest -Uri "$base/api/search" -TimeoutSec 10 -UseBasicParsing; Write-Output $r6.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /api/stock/FLAG ==="
try { $r7 = Invoke-WebRequest -Uri "$base/api/stock/FLAG" -TimeoutSec 10 -UseBasicParsing; Write-Output $r7.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /api/stock/flag ==="
try { $r8 = Invoke-WebRequest -Uri "$base/api/stock/flag" -TimeoutSec 10 -UseBasicParsing; Write-Output $r8.Content } catch { Write-Output $_.Exception.Message }

# Try the Wayback Machine API
Write-Output "`n=== Wayback Machine check ==="
try {
    $r9 = Invoke-WebRequest -Uri "https://web.archive.org/web/2025*/http://18.215.143.250:3000" -TimeoutSec 15 -UseBasicParsing
    Write-Output $r9.Content.Substring(0, [Math]::Min(2000, $r9.Content.Length))
} catch { Write-Output $_.Exception.Message }

# Try CDX API
Write-Output "`n=== CDX API ==="
try {
    $r10 = Invoke-WebRequest -Uri "https://web.archive.org/cdx/search/cdx?url=18.215.143.250:3000&output=json&limit=10" -TimeoutSec 15 -UseBasicParsing
    Write-Output $r10.Content
} catch { Write-Output $_.Exception.Message }

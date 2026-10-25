$base = "http://18.215.143.250:3000"
$r = Invoke-WebRequest -Uri $base -TimeoutSec 10 -UseBasicParsing
$m = [regex]::Matches($r.Content, 'RSTCON\{[^}]*\}')
if ($m.Count -gt 0) {
    foreach ($x in $m) { Write-Output "FLAG: $($x.Value)" }
} else {
    Write-Output "No RSTCON flag in main page"
}

# Check stock pages
$stocks = @("AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","JPM","V","WMT","NFLX","DIS")
foreach ($stock in $stocks) {
    try {
        $r2 = Invoke-WebRequest -Uri "$base/stock/$stock" -TimeoutSec 10 -UseBasicParsing
        $m2 = [regex]::Matches($r2.Content, 'RSTCON\{[^}]*\}')
        if ($m2.Count -gt 0) {
            foreach ($x in $m2) { Write-Output "FLAG in ${stock}: $($x.Value)" }
        }
    } catch {}
}

# Check portfolio and watchlist
try {
    $r3 = Invoke-WebRequest -Uri "$base/portfolio" -TimeoutSec 10 -UseBasicParsing
    $m3 = [regex]::Matches($r3.Content, 'RSTCON\{[^}]*\}')
    if ($m3.Count -gt 0) { foreach ($x in $m3) { Write-Output "FLAG in portfolio: $($x.Value)" } }
} catch {}

try {
    $r4 = Invoke-WebRequest -Uri "$base/watchlist" -TimeoutSec 10 -UseBasicParsing
    $m4 = [regex]::Matches($r4.Content, 'RSTCON\{[^}]*\}')
    if ($m4.Count -gt 0) { foreach ($x in $m4) { Write-Output "FLAG in watchlist: $($x.Value)" } }
} catch {}

# Try RSC flight data
try {
    $headers = @{ "Accept" = "text/x-component" }
    $r5 = Invoke-WebRequest -Uri "$base/" -Headers $headers -TimeoutSec 10 -UseBasicParsing
    Write-Output "RSC main page (first 1000 chars):"
    Write-Output $r5.Content.Substring(0, [Math]::Min(1000, $r5.Content.Length))
} catch { Write-Output "RSC error: $($_.Exception.Message)" }

try {
    $headers = @{ "Accept" = "text/x-component" }
    $r6 = Invoke-WebRequest -Uri "$base/stock/AAPL" -Headers $headers -TimeoutSec 10 -UseBasicParsing
    Write-Output "RSC stock page (first 1000 chars):"
    Write-Output $r6.Content.Substring(0, [Math]::Min(1000, $r6.Content.Length))
} catch { Write-Output "RSC stock error: $($_.Exception.Message)" }

# Try _next/data routes
try {
    $r7 = Invoke-WebRequest -Uri "$base/_next/data/qyfJNY9j0_iFz3SifWy5m/stock/AAPL.json" -TimeoutSec 8 -UseBasicParsing
    Write-Output "_next/data stock AAPL:"
    Write-Output $r7.Content.Substring(0, [Math]::Min(1000, $r7.Content.Length))
} catch { Write-Output "_next/data error: $($_.Exception.Message)" }

Write-Output "Done."

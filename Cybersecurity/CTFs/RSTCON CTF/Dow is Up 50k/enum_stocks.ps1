$base = "http://18.215.143.250:3000"
$ErrorActionPreference = "Continue"

# 1. Enumerate ALL stocks via searchStocks server action (single letters)
Write-Output "=== ENUMERATING ALL STOCKS ==="
$allStocks = @{}
$letters = @("a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z")
foreach ($letter in $letters) {
    try {
        $headers = @{ "Content-Type" = "text/plain;charset=UTF-8"; "Next-Action" = "40881a01be516941afc21e3145707ceff4a34545af" }
        $body = "[`"$letter`"]"
        $r = Invoke-WebRequest -Uri "$base" -Method POST -Headers $headers -Body $body -TimeoutSec 10 -UseBasicParsing
        $lines = $r.Content -split "`n"
        foreach ($line in $lines) {
            if ($line -match '^\d:') {
                $jsonPart = $line.Substring($line.IndexOf(':') + 1)
                try {
                    $data = $jsonPart | ConvertFrom-Json
                    if ($data -is [array]) {
                        foreach ($stock in $data) {
                            if (-not $allStocks.ContainsKey($stock.symbol)) {
                                $allStocks[$stock.symbol] = $stock
                                Write-Output "STOCK: $($stock.symbol) - $($stock.name) - $($stock.sector)"
                            }
                        }
                    }
                } catch {}
            }
        }
    } catch {
        Write-Output "Search $letter error: $($_.Exception.Message)"
    }
}

Write-Output "`n=== TOTAL STOCKS FOUND: $($allStocks.Count) ==="

# 2. Dump full data for hint tickers
Write-Output "`n=== HINT TICKER FULL SEARCH RESULTS ==="
$hints = @("SHOP", "NOW", "PAY", "DASH", "BOX")
foreach ($ticker in $hints) {
    try {
        $headers = @{ "Content-Type" = "text/plain;charset=UTF-8"; "Next-Action" = "40881a01be516941afc21e3145707ceff4a34545af" }
        $body = "[`"$ticker`"]"
        $r = Invoke-WebRequest -Uri "$base" -Method POST -Headers $headers -Body $body -TimeoutSec 10 -UseBasicParsing
        Write-Output "=== $ticker ==="
        Write-Output $r.Content
    } catch {
        Write-Output "$ticker error: $($_.Exception.Message)"
    }
}

# 3. Check stock pages for hint tickers - full content search
Write-Output "`n=== STOCK PAGES FULL SEARCH ==="
foreach ($ticker in $hints) {
    try {
        $r = Invoke-WebRequest -Uri "$base/stock/$ticker" -TimeoutSec 10 -UseBasicParsing
        # Search for flag patterns
        $flagMatches = [regex]::Matches($r.Content, "(?i)(rstcon|flag)\{[^}]*\}")
        foreach ($m in $flagMatches) { Write-Output "FLAG in /stock/${ticker}: $($m.Value)" }
        # Search for date patterns
        $dateMatches = [regex]::Matches($r.Content, "(Dec|January|February|March|April|May|June|July|August|September|October|November)\s+\d+,\s+\d{4}")
        foreach ($m in $dateMatches) { Write-Output "DATE in /stock/${ticker}: $($m.Value)" }
        # Search for built/created/modified
        $builtMatches = [regex]::Matches($r.Content, "(?i)(built|created|modified|date|deploy)[^<]{0,40}")
        foreach ($m in $builtMatches) { Write-Output "META in /stock/${ticker}: $($m.Value)" }
    } catch {
        Write-Output "/stock/$ticker error: $($_.Exception.Message)"
    }
}

Write-Output "`nDone."
$base = "http://18.215.143.250:3000"

Write-Output "=== MAIN PAGE - Searching for date patterns ==="
try {
    $r = Invoke-WebRequest -Uri $base -TimeoutSec 10 -UseBasicParsing
    $content = $r.Content
    
    # Search for flag patterns
    $flagMatches = [regex]::Matches($content, "rstcon\{[^}]+\}")
    foreach ($m in $flagMatches) { Write-Output "FLAG FOUND: $($m.Value)" }
    
    # Search for date patterns
    $dateMatches = [regex]::Matches($content, "Dec\s+\d+,\s+\d{4}")
    foreach ($m in $dateMatches) { Write-Output "DATE FOUND: $($m.Value)" }
    
    # Search for 2024, 2025, 2026
    $yearMatches = [regex]::Matches($content, "202[456]")
    foreach ($m in $yearMatches) { Write-Output "YEAR: $($m.Value)" }
    
    # Search for built date
    $builtMatches = [regex]::Matches($content, "Built[^<]{0,30}")
    foreach ($m in $builtMatches) { Write-Output "BUILT: $($m.Value)" }
} catch { 
    Write-Output "Error: $($_.Exception.Message)" 
}

Write-Output "`n=== CHECKING RESPONSE HEADERS ==="
try {
    $r2 = Invoke-WebRequest -Uri "$base/_next/static/chunks/app/page-dcea1cd040fd23a5.js" -TimeoutSec 10 -UseBasicParsing -Method Head
    $r2.Headers | Format-Table -AutoSize
} catch {
    Write-Output "Error: $($_.Exception.Message)"
}

Write-Output "`n=== ROOT PAGE RAW (first 3000 chars) ==="
try {
    $r3 = Invoke-WebRequest -Uri $base -TimeoutSec 10 -UseBasicParsing
    Write-Output $r3.Content.Substring(0, [Math]::Min(3000, $r3.Content.Length))
} catch {
    Write-Output "Error: $($_.Exception.Message)"
}
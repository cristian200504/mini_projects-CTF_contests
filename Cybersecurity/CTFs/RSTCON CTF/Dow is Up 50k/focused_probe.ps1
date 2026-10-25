$base = "http://18.215.143.250:3000"
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
$outDir = "C:\Users\crist\OneDrive\Desktop\RSTCON CTF\Dow is Up 50k\recon"

if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

# 1. Save RSC flight data for all routes
Write-Output "Saving RSC flight data..."
$rscRoutes = @("/", "/portfolio", "/watchlist", "/stock/AAPL")
foreach ($route in $rscRoutes) {
    try {
        $headers = @{ "RSC" = "1" }
        $r = Invoke-WebRequest -Uri "$base$route" -Headers $headers -TimeoutSec 10 -UseBasicParsing
        $safeName = $route -replace '[/]', '_'
        $r.Content | Out-File -FilePath "$outDir\rsc${safeName}.txt" -Encoding UTF8
        Write-Output "Saved RSC for $route ($($r.Content.Length) chars)"
    } catch {
        Write-Output "RSC $route error: $($_.Exception.Message)"
    }
}

# 2. Save full HTML for all routes
Write-Output "`nSaving HTML..."
foreach ($route in $rscRoutes) {
    try {
        $r = Invoke-WebRequest -Uri "$base$route" -TimeoutSec 10 -UseBasicParsing
        $safeName = $route -replace '[/]', '_'
        $r.Content | Out-File -FilePath "$outDir\html${safeName}.txt" -Encoding UTF8
        Write-Output "Saved HTML for $route ($($r.Content.Length) chars)"
    } catch {
        Write-Output "HTML $route error: $($_.Exception.Message)"
    }
}

# 3. Save webpack runtime chunk
Write-Output "`nSaving webpack chunk..."
try {
    $r = Invoke-WebRequest -Uri "$base/_next/static/chunks/webpack-06b7f1618a9e9933.js" -TimeoutSec 10 -UseBasicParsing
    $r.Content | Out-File -FilePath "$outDir\webpack.js" -Encoding UTF8
    Write-Output "Saved webpack chunk ($($r.Content.Length) chars)"
} catch {
    Write-Output "webpack error: $($_.Exception.Message)"
}

# 4. Save main page chunk
Write-Output "`nSaving page chunk..."
try {
    $r = Invoke-WebRequest -Uri "$base/_next/static/chunks/app/page-dcea1cd040fd23a5.js" -TimeoutSec 10 -UseBasicParsing
    $r.Content | Out-File -FilePath "$outDir\page.js" -Encoding UTF8
    Write-Output "Saved page chunk ($($r.Content.Length) chars)"
} catch {
    Write-Output "page error: $($_.Exception.Message)"
}

# 5. Save the 445 chunk and other chunks
Write-Output "`nSaving 445 chunk..."
try {
    $r = Invoke-WebRequest -Uri "$base/_next/static/chunks/445-e015270e866f7521.js" -TimeoutSec 10 -UseBasicParsing
    $r.Content | Out-File -FilePath "$outDir\445.js" -Encoding UTF8
    Write-Output "Saved 445 chunk ($($r.Content.Length) chars)"
} catch {
    Write-Output "445 error: $($_.Exception.Message)"
}

# 6. Save the build manifest
Write-Output "`nSaving build manifest..."
try {
    $r = Invoke-WebRequest -Uri "$base/_next/static/qyfJNY9j0_iFz3SifWy5m/_buildManifest.js" -TimeoutSec 10 -UseBasicParsing
    $r.Content | Out-File -FilePath "$outDir\buildManifest.js" -Encoding UTF8
    Write-Output "Saved build manifest"
    Write-Output $r.Content
} catch {
    Write-Output "buildManifest error: $($_.Exception.Message)"
}

# 7. Try to find ALL JS chunks from the HTML
Write-Output "`nExtracting all chunk URLs from main page..."
try {
    $r = Invoke-WebRequest -Uri "$base" -TimeoutSec 10 -UseBasicParsing
    $chunkMatches = [regex]::Matches($r.Content, '/_next/static/chunks/[a-zA-Z0-9_./-]+\.js')
    $chunks = $chunkMatches | ForEach-Object { $_.Value } | Sort-Object -Unique
    Write-Output "Found $($chunks.Count) chunk URLs:"
    foreach ($c in $chunks) { Write-Output "  $c" }
    # Save them
    $chunks | Out-File -FilePath "$outDir\chunk_urls.txt" -Encoding UTF8
} catch {
    Write-Output "chunk extraction error: $($_.Exception.Message)"
}

Write-Output "`nDone saving. Now search for flags in saved files."
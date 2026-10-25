$base = "http://18.215.143.250:3000"
$ErrorActionPreference = "Continue"

# 1. Dump FULL RSC flight data for main page (look for hidden data/flags)
Write-Output "=== RSC FLIGHT DATA - MAIN PAGE (FULL) ==="
try {
    $headers = @{ "RSC" = "1" }
    $r = Invoke-WebRequest -Uri "$base/" -Headers $headers -TimeoutSec 10 -UseBasicParsing
    Write-Output $r.Content
} catch {
    Write-Output "RSC error: $($_.Exception.Message)"
}

# 2. Get the webpack runtime chunk and look for route mappings
Write-Output "`n=== WEBPACK RUNTIME CHUNK ==="
try {
    $r2 = Invoke-WebRequest -Uri "$base/_next/static/chunks/webpack-06b7f1618a9e9933.js" -TimeoutSec 10 -UseBasicParsing
    Write-Output $r2.Content
} catch {
    Write-Output "webpack error: $($_.Exception.Message)"
}

# 3. Check the main page chunk for hidden routes/server actions
Write-Output "`n=== MAIN PAGE CHUNK ==="
try {
    $r3 = Invoke-WebRequest -Uri "$base/_next/static/chunks/app/page-dcea1cd040fd23a5.js" -TimeoutSec 10 -UseBasicParsing
    Write-Output $r3.Content
} catch {
    Write-Output "page chunk error: $($_.Exception.Message)"
}

# 4. Look for hidden routes - try common paths
Write-Output "`n=== HIDDEN ROUTE CHECK ==="
$routes = @("/admin", "/flag", "/secret", "/api/flag", "/api/secret", "/dashboard", "/settings", 
             "/api", "/_next/static/chunks/app/", "/flag.txt", "/robots.txt", "/sitemap.xml",
             "/api/health", "/api/version", "/api/build", "/api/date", "/api/metadata",
             "/dashboard/flag", "/.env", "/package.json", "/next.config.js",
             "/api/search", "/api/stocks", "/api/portfolio", "/api/watchlist",
             "/.next", "/.next/server", "/.next/server/server-reference-manifest.json",
             "/_next/static/chunks/app/portfolio/", "/_next/static/chunks/app/watchlist/",
             "/_next/static/chunks/app/stock/")
foreach ($route in $routes) {
    try {
        $r4 = Invoke-WebRequest -Uri "$base$route" -TimeoutSec 5 -UseBasicParsing
        $preview = $r4.Content.Substring(0, [Math]::Min(200, $r4.Content.Length))
        Write-Output "FOUND $route (200): $preview"
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code -ne 404 -and $code -ne 405) {
            Write-Output "$route -> $code"
        }
    }
}

# 5. Get the full HTML of main page and extract ALL RSC push data
Write-Output "`n=== FULL HTML - RSC PUSH EXTRACTION ==="
try {
    $r5 = Invoke-WebRequest -Uri "$base" -TimeoutSec 10 -UseBasicParsing
    $content = $r5.Content
    # Extract all self.__next_f.push data
    $pushMatches = [regex]::Matches($content, 'self\.__next_f\.push\(\[1,"([^"]*)"\]\)')
    Write-Output "Found $($pushMatches.Count) RSC push chunks"
    $i = 0
    foreach ($m in $pushMatches) {
        $i++
        $val = $m.Groups[1].Value
        # Search for flag/date patterns in each chunk
        if ($val -match "(?i)(rstcon|flag|secret|hidden|date|built|2025|2026)") {
            Write-Output "=== CHUNK $i (interesting) ==="
            Write-Output $val
        }
    }
    # Also search the entire content for flag
    $flagMatches = [regex]::Matches($content, "(?i)rstcon\{[^}]*\}")
    foreach ($m in $flagMatches) { Write-Output "FLAG: $($m.Value)" }
} catch {
    Write-Output "HTML error: $($_.Exception.Message)"
}

Write-Output "`nDone."
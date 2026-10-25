$base = "http://18.215.143.250:3000"
$mirror = "http://18.145.136.91:3000"

# Wayback Machine availability API
Write-Output "=== Wayback Availability API ==="
try {
    $r = Invoke-WebRequest -Uri "https://archive.org/wayback/available?url=18.215.143.250:3000" -TimeoutSec 15 -UseBasicParsing
    Write-Output $r.Content
} catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Wayback Availability API mirror2 ==="
try {
    $r2 = Invoke-WebRequest -Uri "https://archive.org/wayback/available?url=18.145.136.91:3000" -TimeoutSec 15 -UseBasicParsing
    Write-Output $r2.Content
} catch { Write-Output $_.Exception.Message }

# Try Wayback CDX with wildcard and different matchType
Write-Output "`n=== Wayback CDX matchType=exact ==="
try {
    $r3 = Invoke-WebRequest -Uri "https://web.archive.org/cdx/search/cdx?url=18.215.143.250:3000&output=json&limit=20&matchType=exact" -TimeoutSec 15 -UseBasicParsing
    Write-Output $r3.Content
} catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Wayback CDX matchType=prefix ==="
try {
    $r4 = Invoke-WebRequest -Uri "https://web.archive.org/cdx/search/cdx?url=18.215.143.250:3000&output=json&limit=20&matchType=prefix" -TimeoutSec 15 -UseBasicParsing
    Write-Output $r4.Content
} catch { Write-Output $_.Exception.Message }

Write-Output "`n=== Wayback CDX matchType=domain ==="
try {
    $r5 = Invoke-WebRequest -Uri "https://web.archive.org/cdx/search/cdx?url=18.215.143.250&output=json&limit=20&matchType=domain" -TimeoutSec 15 -UseBasicParsing
    Write-Output $r5.Content
} catch { Write-Output $_.Exception.Message }

# Check for git files
Write-Output "`n=== /.git/config ==="
try { $r6 = Invoke-WebRequest -Uri "$base/.git/config" -TimeoutSec 8 -UseBasicParsing; Write-Output $r6.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /.git/logs/HEAD ==="
try { $r7 = Invoke-WebRequest -Uri "$base/.git/logs/HEAD" -TimeoutSec 8 -UseBasicParsing; Write-Output $r7.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /.git/COMMIT_EDITMSG ==="
try { $r8 = Invoke-WebRequest -Uri "$base/.git/COMMIT_EDITMSG" -TimeoutSec 8 -UseBasicParsing; Write-Output $r8.Content } catch { Write-Output $_.Exception.Message }

# Check health/version endpoints
Write-Output "`n=== /api/health ==="
try { $r9 = Invoke-WebRequest -Uri "$base/api/health" -TimeoutSec 8 -UseBasicParsing; Write-Output $r9.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /api/version ==="
try { $r10 = Invoke-WebRequest -Uri "$base/api/version" -TimeoutSec 8 -UseBasicParsing; Write-Output $r10.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /version ==="
try { $r11 = Invoke-WebRequest -Uri "$base/version" -TimeoutSec 8 -UseBasicParsing; Write-Output $r11.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /health ==="
try { $r12 = Invoke-WebRequest -Uri "$base/health" -TimeoutSec 8 -UseBasicParsing; Write-Output $r12.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /.well-known/security.txt ==="
try { $r13 = Invoke-WebRequest -Uri "$base/.well-known/security.txt" -TimeoutSec 8 -UseBasicParsing; Write-Output $r13.Content } catch { Write-Output $_.Exception.Message }

# Try OPTIONS method
Write-Output "`n=== OPTIONS / ==="
try { $r14 = Invoke-WebRequest -Uri "$base/" -Method OPTIONS -TimeoutSec 8 -UseBasicParsing; Write-Output $r14.Content; $r14.Headers | Format-List } catch { Write-Output $_.Exception.Message }

# Try to trigger error page
Write-Output "`n=== /_error ==="
try { $r15 = Invoke-WebRequest -Uri "$base/_error" -TimeoutSec 8 -UseBasicParsing; Write-Output $r15.Content.Substring(0, [Math]::Min(1000, $r15.Content.Length)) } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /404 ==="
try { $r16 = Invoke-WebRequest -Uri "$base/404" -TimeoutSec 8 -UseBasicParsing; Write-Output $r16.Content.Substring(0, [Math]::Min(1000, $r16.Content.Length)) } catch { Write-Output $_.Exception.Message }

# Check mirror server
Write-Output "`n=== Mirror server main page (footer area) ==="
try {
    $r17 = Invoke-WebRequest -Uri "$mirror/" -TimeoutSec 10 -UseBasicParsing
    # Extract footer
    $idx = $r17.Content.IndexOf("footer")
    if ($idx -gt 0) { Write-Output $r17.Content.Substring($idx, [Math]::Min(500, $r17.Content.Length - $idx)) }
    else { Write-Output "No footer found"; Write-Output $r17.Content.Substring(0, [Math]::Min(500, $r17.Content.Length)) }
} catch { Write-Output $_.Exception.Message }

# Check mirror server headers
Write-Output "`n=== Mirror server headers ==="
try {
    $r18 = Invoke-WebRequest -Uri "$mirror/" -TimeoutSec 10 -UseBasicParsing
    $r18.Headers | Format-List
} catch { Write-Output $_.Exception.Message }

# Try to access _next/static/{buildId}/ directory
Write-Output "`n=== /_next/static/qyfJNY9j0_iFz3SifWy5m/ ==="
try { $r19 = Invoke-WebRequest -Uri "$base/_next/static/qyfJNY9j0_iFz3SifWy5m/" -TimeoutSec 8 -UseBasicParsing; Write-Output $r19.Content } catch { Write-Output $_.Exception.Message }

# Try to find source maps for page chunks
Write-Output "`n=== page chunk source map ==="
try { $r20 = Invoke-WebRequest -Uri "$base/_next/static/chunks/app/page-dcea1cd040fd23a5.js.map" -TimeoutSec 8 -UseBasicParsing; Write-Output $r20.Content.Substring(0, [Math]::Min(1000, $r20.Content.Length)) } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== stock detail chunk source map ==="
try { $r21 = Invoke-WebRequest -Uri "$base/_next/static/chunks/app/stock/%5Bsymbol%5D/page-6608109a205873bb.js.map" -TimeoutSec 8 -UseBasicParsing; Write-Output $r21.Content.Substring(0, [Math]::Min(1000, $r21.Content.Length)) } catch { Write-Output $_.Exception.Message }

# Check for 445 chunk source map
Write-Output "`n=== 445 chunk source map ==="
try { $r22 = Invoke-WebRequest -Uri "$base/_next/static/chunks/445-e015270e866f7521.js.map" -TimeoutSec 8 -UseBasicParsing; Write-Output $r22.Content.Substring(0, [Math]::Min(1000, $r22.Content.Length)) } catch { Write-Output $_.Exception.Message }

# Try to find hidden pages
Write-Output "`n=== /_next/static/qyfJNY9j0_iFz3SifWy5m/_buildManifest.js ==="
try { $r23 = Invoke-WebRequest -Uri "$base/_next/static/qyfJNY9j0_iFz3SifWy5m/_buildManifest.js" -TimeoutSec 8 -UseBasicParsing; Write-Output $r23.Content } catch { Write-Output $_.Exception.Message }

# Check for app router pages manifest
Write-Output "`n=== /_next/static/qyfJNY9j0_iFz3SifWy5m/app-build-manifest.js ==="
try { $r24 = Invoke-WebRequest -Uri "$base/_next/static/qyfJNY9j0_iFz3SifWy5m/app-build-manifest.js" -TimeoutSec 8 -UseBasicParsing; Write-Output $r24.Content } catch { Write-Output $_.Exception.Message }

Write-Output "`n=== /_next/static/qyfJNY9j0_iFz3SifWy5m/server-reference-manifest.js ==="
try { $r25 = Invoke-WebRequest -Uri "$base/_next/static/qyfJNY9j0_iFz3SifWy5m/server-reference-manifest.js" -TimeoutSec 8 -UseBasicParsing; Write-Output $r25.Content } catch { Write-Output $_.Exception.Message }

# Try fetching the full portfolio page
Write-Output "`n=== Full portfolio page ==="
try {
    $r26 = Invoke-WebRequest -Uri "$base/portfolio" -TimeoutSec 10 -UseBasicParsing
    # Search for flag-like strings
    $matches = [regex]::Matches($r26.Content, '(?:flag|rstcon|RSTCON|FLAG|secret|hidden)(?i)[^<]{0,200}')
    foreach ($m in $matches) { Write-Output "MATCH: $($m.Value)" }
    # Get last 2000 chars
    Write-Output $r26.Content.Substring([Math]::Max(0, $r26.Content.Length - 2000))
} catch { Write-Output $_.Exception.Message }

# Try fetching the full watchlist page  
Write-Output "`n=== Full watchlist page ==="
try {
    $r27 = Invoke-WebRequest -Uri "$base/watchlist" -TimeoutSec 10 -UseBasicParsing
    # Search for flag-like strings
    $matches = [regex]::Matches($r27.Content, '(?:flag|rstcon|RSTCON|FLAG|secret|hidden)(?i)[^<]{0,200}')
    foreach ($m in $matches) { Write-Output "MATCH: $($m.Value)" }
    # Get last 2000 chars
    Write-Output $r27.Content.Substring([Math]::Max(0, $r27.Content.Length - 2000))
} catch { Write-Output $_.Exception.Message }

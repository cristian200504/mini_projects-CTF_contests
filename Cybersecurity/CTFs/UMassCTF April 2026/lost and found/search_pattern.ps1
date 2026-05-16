$file = "C:\Users\crist\OneDrive\Desktop\lost and found\extract\disk.vmdk"
$pattern = [System.Text.Encoding]::ASCII.GetBytes("UMassCTF")
$buffer = New-Object byte[] 1048576 # 1MB chunks
$stream = [System.IO.File]::OpenRead($file)
$found = $false

while (($read = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
    for ($i = 0; $i -le $read - $pattern.Length; $i++) {
        $match = $true
        for ($j = 0; $j -lt $pattern.Length; $j++) {
            if ($buffer[$i + $j] -ne $pattern[$j]) {
                $match = $false
                break
            }
        }
        if ($match) {
            $offset = $stream.Position - $read + $i
            Write-Host "Pattern found at offset $offset"
            $found = $true
            # Print some surrounding text
            $start = [Math]::Max(0, $i - 50)
            $end = [Math]::Min($read - 1, $i + 100)
            $context = [System.Text.Encoding]::ASCII.GetString($buffer, $start, $end - $start)
            Write-Host "Context: $context"
        }
    }
}
$stream.Close()
if (-not $found) { Write-Host "Pattern not found." }

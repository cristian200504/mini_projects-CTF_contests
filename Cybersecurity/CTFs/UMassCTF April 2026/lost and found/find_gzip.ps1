$file = "C:\Users\crist\OneDrive\Desktop\lost and found\extract\file1.iso"
$bytes = [System.IO.File]::ReadAllBytes($file)
for ($i = 0; $i -lt $bytes.Length - 1; $i++) {
    if ($bytes[$i] -eq 0x1F -and $bytes[$i+1] -eq 0x8B) {
        Write-Host "GZIP found at offset $i"
    }
}

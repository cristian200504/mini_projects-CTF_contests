$file = "C:\Users\crist\OneDrive\Desktop\lost and found\extract\disk.vmdk"
$stream = [System.IO.File]::OpenRead($file)
$buffer = New-Object byte[] 65536
while (($read = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
    for ($i = 0; $i -lt $read - 2; $i++) {
        if ($buffer[$i] -eq 0x53 -and $buffer[$i+1] -eq 0xEF) {
            # Potential EXT signature at $i
            # Check if it's at offset 1080 (0x438) relative to a sector or block
            $abs_offset = $stream.Position - $read + $i
            if (($abs_offset - 0x438) % 512 -eq 0) {
                Write-Host "Potential EXT superblock found at offset $abs_offset"
            }
        }
    }
}
$stream.Close()

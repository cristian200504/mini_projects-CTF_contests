$input_file = "C:\Users\crist\OneDrive\Desktop\lost and found\extract\ctf-vm-disk1.vmdk.gz"
$output_file = "C:\Users\crist\OneDrive\Desktop\lost and found\extract\disk.vmdk"
$input_stream = New-Object System.IO.FileStream($input_file, [System.IO.FileMode]::Open)
$output_stream = New-Object System.IO.FileStream($output_file, [System.IO.FileMode]::Create)
$gzip_stream = New-Object System.IO.Compression.GZipStream($input_stream, [System.IO.Compression.CompressionMode]::Decompress)
$gzip_stream.CopyTo($output_stream)
$gzip_stream.Close()
$output_stream.Close()
$input_stream.Close()
Write-Host "Done disk.vmdk"

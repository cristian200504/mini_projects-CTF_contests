param(
    [string]$input_file,
    [string]$output_file
)
$input_stream = New-Object System.IO.FileStream($input_file, [System.IO.FileMode]::Open)
$output_stream = New-Object System.IO.FileStream($output_file, [System.IO.FileMode]::Create)
$gzip_stream = New-Object System.IO.Compression.GZipStream($input_stream, [System.IO.Compression.CompressionMode]::Decompress)
$gzip_stream.CopyTo($output_stream)
$gzip_stream.Close()
$output_stream.Close()
$input_stream.Close()
Write-Host "Done $output_file"

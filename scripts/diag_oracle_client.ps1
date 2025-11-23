# Diagnostic script to check Oracle Instant Client presence and bitness on Windows
Write-Host "Checking Oracle Instant Client configuration..."

Write-Host "ORACLE_9I_CLIENT_PATH = $env:ORACLE_9I_CLIENT_PATH"
Write-Host "ORACLE_CLIENT_PATH = $env:ORACLE_CLIENT_PATH"
Write-Host "PATH contains instant client? -->" (Get-ChildItem Env:PATH).Value -match ($env:ORACLE_9I_CLIENT_PATH ?? '')

if ($env:ORACLE_9I_CLIENT_PATH) {
  $oci = Join-Path $env:ORACLE_9I_CLIENT_PATH 'oci.dll'
  Write-Host "Checking $oci"
  if (Test-Path $oci) {
    $item = Get-Item $oci
    Write-Host "oci.dll found. FileVersion: " $item.VersionInfo.FileVersion
  } else {
    Write-Host "oci.dll not found in ORACLE_9I_CLIENT_PATH"
  }
} else {
  Write-Host "ORACLE_9I_CLIENT_PATH not set"
}

Write-Host "Node version: " (node -v)
Write-Host "PowerShell bitness (pointer size * 8): " [IntPtr]::Size * 8

Write-Host "If oci.dll is missing or wrong bitness, install Instant Client 11.2 x64 and set ORACLE_9I_CLIENT_PATH accordingly."

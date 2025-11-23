# Diagnostic script to check Oracle Client and 9i compatibility

Write-Host "=== Oracle Client Diagnosis ===" -ForegroundColor Cyan
Write-Host ""

# Check environment variables
Write-Host "1. Environment Variables:" -ForegroundColor Yellow
Write-Host "  ORACLE_HOME: $($env:ORACLE_HOME)"
Write-Host "  ORACLE_11G_CLIENT_PATH: $($env:ORACLE_11G_CLIENT_PATH)"
Write-Host "  ORACLE_9I_CLIENT_PATH: $($env:ORACLE_9I_CLIENT_PATH)"
Write-Host ""

# Check PATH for Oracle entries
Write-Host "2. Oracle entries in PATH:" -ForegroundColor Yellow
$env:PATH -split ";" | Where-Object { $_ -match "oracle|instant" } | ForEach-Object {
    Write-Host "  Path entry: $_"
    if (Test-Path "$_\oci.dll") {
        $version = (Get-Item "$_\oci.dll").VersionInfo.FileVersion
        Write-Host "    FOUND oci.dll: $version"
    }
}
Write-Host ""

# Check for Instant Client installations
Write-Host "3. Instant Client installations:" -ForegroundColor Yellow
$clients = @(
    "C:\instantclient_10_2",
    "C:\instantclient_11_2",
    "C:\instantclient_12_1",
    "C:\instantclient_19_3",
    "C:\Oracle"
)

foreach ($client in $clients) {
    if (Test-Path "$client\oci.dll") {
        $version = (Get-Item "$client\oci.dll").VersionInfo.FileVersion
        Write-Host "  FOUND: $client - Version: $version"
    }
}
Write-Host ""

# Check NODE.js and npm
Write-Host "4. Node.js/npm versions:" -ForegroundColor Yellow
Write-Host "  Node: $(node --version)"
Write-Host "  npm: $(&  'C:\Program Files\nodejs\npm.cmd' --version)"
Write-Host ""

# Check current directory and .env
Write-Host "5. Current directory setup:" -ForegroundColor Yellow
$pwd = Get-Location
Write-Host "  Working dir: $pwd"
if (Test-Path ".env") {
    Write-Host "  FOUND .env file"
    Write-Host "  Content:"
    Get-Content ".env" | ForEach-Object { Write-Host "    $_" }
}
Write-Host ""

# Final recommendations
Write-Host "6. Recommendations for 9i connectivity:" -ForegroundColor Green
Write-Host "  * Oracle 9i requires Instant Client 10.2, 11.2, or earlier"
Write-Host "  * Set ORACLE_9I_CLIENT_PATH to C:\instantclient_10_2 or C:\instantclient_11_2"
Write-Host "  * Ensure no conflicting newer Oracle Client entries are loaded"
Write-Host "  * If using cx_Oracle/oracledb, they must be compatible with the target client version"
Write-Host ""
Write-Host "=== End Diagnosis ===" -ForegroundColor Cyan

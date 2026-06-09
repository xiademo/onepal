param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PidPath = Join-Path $ProjectRoot "runtime\onepal_api.pid"

if (-not (Test-Path $PidPath)) {
    Write-Host "No OnePal API PID file found. Nothing to stop."
    exit 0
}

$pidText = (Get-Content -Path $PidPath -Raw).Trim()
$parsedPid = 0
if (-not [int]::TryParse($pidText, [ref]$parsedPid)) {
    Remove-Item -Path $PidPath -Force
    throw "Invalid PID file removed: $PidPath"
}

$processId = $parsedPid
$process = Get-Process -Id $processId -ErrorAction SilentlyContinue
if ($null -eq $process) {
    Remove-Item -Path $PidPath -Force
    Write-Host "OnePal API process $processId is not running. PID file removed."
    exit 0
}

if ($Force) {
    Stop-Process -Id $processId -Force
} else {
    Stop-Process -Id $processId
}

Remove-Item -Path $PidPath -Force
Write-Host "Stopped OnePal API process $processId."

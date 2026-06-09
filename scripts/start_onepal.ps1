param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 18790,
    [string]$Python = "",
    [switch]$NoBrowser,
    [switch]$SkipSmoke
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RuntimeDir = Join-Path $ProjectRoot "runtime"
$PidPath = Join-Path $RuntimeDir "onepal_api.pid"
$OutLog = Join-Path $RuntimeDir "onepal_api.out.log"
$ErrLog = Join-Path $RuntimeDir "onepal_api.err.log"
$ApiScript = Join-Path $ProjectRoot "scripts\api_server.py"
$SmokeScript = Join-Path $ProjectRoot "scripts\run_startup_smoke_test.py"
$DashboardPath = Join-Path $ProjectRoot "dashboard\index.html"
$HealthUrl = "http://${BindHost}:$Port/health"

function Test-OnePalApi {
    try {
        $resp = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2 -ErrorAction Stop
        return ($resp.ok -eq $true)
    } catch {
        return $false
    }
}

function Resolve-PythonExecutable {
    if ($Python) {
        if (-not (Test-Path $Python) -and -not (Get-Command $Python -ErrorAction SilentlyContinue)) {
            throw "Python executable was not found: $Python"
        }
        return $Python
    }

    foreach ($candidate in @("py", "python")) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            & $candidate -c "import sys; print(sys.executable)" *> $null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        }
    }

    $bundled = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundled) {
        return $bundled
    }

    throw "No usable Python executable found. Install Python for Windows or pass -Python <path-to-python.exe>."
}

$PythonExe = Resolve-PythonExecutable
Write-Host "Using Python: $PythonExe"

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

if (-not $SkipSmoke) {
    Write-Host "Running startup smoke test..."
    & $PythonExe $SmokeScript
    if ($LASTEXITCODE -ne 0) {
        throw "Startup smoke test failed. Fix the reported issue or rerun with -SkipSmoke only for local debugging."
    }
}

if (Test-OnePalApi) {
    Write-Host "OnePal API is already running at $HealthUrl"
} else {
    Write-Host "Starting OnePal API at $HealthUrl"
    $process = Start-Process -FilePath $PythonExe `
        -ArgumentList @($ApiScript, "--host", $BindHost, "--port", "$Port") `
        -WorkingDirectory $ProjectRoot `
        -RedirectStandardOutput $OutLog `
        -RedirectStandardError $ErrLog `
        -WindowStyle Hidden `
        -PassThru
    Set-Content -Path $PidPath -Value $process.Id -Encoding ascii

    $ready = $false
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-OnePalApi) {
            $ready = $true
            break
        }
    }

    if (-not $ready) {
        Write-Host "API stdout log: $OutLog"
        Write-Host "API stderr log: $ErrLog"
        throw "OnePal API did not become ready."
    }
}

Write-Host "Dashboard: $DashboardPath"
Write-Host "API:       $HealthUrl"
Write-Host "Stop with: powershell -ExecutionPolicy Bypass -File scripts\stop_onepal.ps1"

if (-not $NoBrowser) {
    Start-Process -FilePath $DashboardPath
}

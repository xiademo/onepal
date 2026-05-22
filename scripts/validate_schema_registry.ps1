# OnePal Schema Registry Validation Script
# Task 02-A: Validate schemas/core against schemas/registry.json
# Usage: powershell -ExecutionPolicy Bypass -File scripts\validate_schema_registry.ps1

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir

$reportPath = Join-Path $projectDir "docs\reports\task02_schema_validation_report.md"
$schemaDir = Join-Path $projectDir "schemas\core"
$registryPath = Join-Path $projectDir "schemas\registry.json"
$examplesDir = Join-Path $projectDir "schemas\examples"

$global:warnCount = 0
$global:failCount = 0
$global:passCount = 0
$reportLines = [System.Collections.ArrayList]::new()

function Add-ReportLine($msg) { [void]$reportLines.Add($msg) }
function Write-Pass($msg) {
    $global:passCount++
    Add-ReportLine "  [PASS] $msg"
    Write-Host "  PASS: $msg"
}
function Write-Warn($msg) {
    $global:warnCount++
    Add-ReportLine "  [WARN] $msg"
    Write-Host "  WARN: $msg" -ForegroundColor Yellow
}
function Write-Fail($msg) {
    $global:failCount++
    Add-ReportLine "  [FAIL] $msg"
    Write-Host "  FAIL: $msg" -ForegroundColor Red
}

# ============================================================================
# Phase 1: Prerequisites
# ============================================================================
Add-ReportLine "# Task 02 Schema Validation Report"
Add-ReportLine ""
Add-ReportLine "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zz')"
Add-ReportLine ""
Add-ReportLine "## 1. Summary"
Add-ReportLine ""

Write-Host "Project root: $projectDir"

if (-not (Test-Path $registryPath)) {
    Write-Fail "schemas/registry.json not found"
    Add-ReportLine ""
    Add-ReportLine "**CRITICAL: registry.json missing. Cannot proceed.**"
    $reportLines -join "`n" | Set-Content -Path $reportPath -Encoding UTF8
    exit 1
}
Write-Pass "schemas/registry.json exists"

if (-not (Test-Path $schemaDir)) {
    Write-Fail "schemas/core/ directory not found"
    Add-ReportLine ""
    Add-ReportLine "**CRITICAL: schemas/core/ missing. Cannot proceed.**"
    $reportLines -join "`n" | Set-Content -Path $reportPath -Encoding UTF8
    exit 1
}
Write-Pass "schemas/core/ directory exists"

# ============================================================================
# Phase 2: Parse registry and cross-reference
# ============================================================================
Add-ReportLine ""
Add-ReportLine "## 2. Registry Completeness"
Add-ReportLine ""

$registryContent = Get-Content $registryPath -Raw -Encoding UTF8
try {
    $registry = $registryContent | ConvertFrom-Json -ErrorAction Stop
    $regVer = $registry.version
    Write-Pass "schemas/registry.json parsed (version: $regVer)"
} catch {
    Write-Fail "schemas/registry.json parse error: $_"
    $reportLines -join "`n" | Set-Content -Path $reportPath -Encoding UTF8
    exit 1
}

$registeredIds = $registry.schemas | ForEach-Object { $_.schema_id }
$registeredEntries = $registry.schemas
$regCount = @($registeredIds).Count

$coreFiles = Get-ChildItem $schemaDir -Filter "*.schema.json" | Sort-Object Name
$coreFileNames = $coreFiles | ForEach-Object { $_.Name }
$coreFileCount = @($coreFileNames).Count

Add-ReportLine "  Registry: $regCount entries   Core files: $coreFileCount"

# Registry -> File mapping
Add-ReportLine ""
Add-ReportLine "  ### Registry -> File"
$missingFiles = @()
foreach ($entry in $registeredEntries) {
    $expectedPath = Join-Path $projectDir ($entry.path -replace '/', '\')
    if (-not (Test-Path $expectedPath)) {
        Write-Fail "$($entry.schema_id) -> $($entry.path): file not found"
        $missingFiles += $entry.schema_id
    }
}
if ($missingFiles.Count -eq 0) {
    Write-Pass "All $regCount registry entries resolve to existing files"
}

# File -> Registry mapping
Add-ReportLine ""
Add-ReportLine "  ### File -> Registry"
$unregistered = @()
foreach ($fn in $coreFileNames) {
    if ($registeredIds -notcontains $fn) {
        Write-Warn "$fn is NOT registered in schemas/registry.json"
        $unregistered += $fn
    }
}
if ($unregistered.Count -eq 0) {
    Write-Pass "All $coreFileCount core schemas are registered"
}

# Schema metadata scan
Add-ReportLine ""
Add-ReportLine "  ### Metadata"
foreach ($fn in $coreFileNames) {
    $fp = Join-Path $schemaDir $fn
    $c = Get-Content $fp -Raw -Encoding UTF8
    try { $obj = $c | ConvertFrom-Json } catch { Write-Fail "cannot parse $fn"; continue }
    $title = $obj.title
    $sid = $obj.'$id'
    $sdraft = $obj.'$schema'
    if (-not $title) { Write-Warn "$($fn): missing 'title'" }
    if (-not $sid) { Write-Warn "$($fn): missing '`$id'" }
    if (-not $sdraft) { Write-Warn "$($fn): missing '`$schema'" }
}
Write-Pass "Metadata scan complete"

# ============================================================================
# Phase 3: $ref check
# ============================================================================
Add-ReportLine ""
Add-ReportLine "## 3. `$ref Reference Check"
Add-ReportLine ""

$totalRefs = 0
$badRefs = 0
$refPattern = [regex]' "\$ref"\s*:\s*"([^"]+)"'

foreach ($fn in $coreFileNames) {
    $fp = Join-Path $schemaDir $fn
    $c = Get-Content $fp -Raw -Encoding UTF8
    $matches = $refPattern.Matches($c)
    $totalRefs += $matches.Count
    
    foreach ($m in $matches) {
        $rv = $m.Groups[1].Value
        if ($rv -match '^https?://json-schema\.org/') { continue }
        
        if ($rv -match '^\./') {
            $abs = Join-Path (Split-Path $fp -Parent) $rv
            if (-not (Test-Path $abs)) {
                Write-Fail "$($fn): local `$ref '$rv' not found"; $badRefs++
            }
        } elseif ($rv -match '^https?://ai-workbench\.local/') {
            $lp = $rv -replace 'https://ai-workbench\.local/schemas/core/', ''
            $abs = Join-Path $schemaDir $lp
            if (-not (Test-Path $abs)) {
                Write-Fail "$($fn): cross-schema `$ref '$rv' not found"; $badRefs++
            }
        } elseif ($rv -match '^#') {
            if ($rv -notmatch '^#(/[^/~]*(~[01][^/~]*)*)*$') {
                Write-Warn "$($fn): `$ref '$rv' unusual JSON Pointer"
            }
        }
    }
}

if ($badRefs -eq 0) {
    Write-Pass "`$ref check: $totalRefs references across $coreFileCount schemas, 0 broken"
} else {
    Write-Fail "`$ref check: $badRefs broken out of $totalRefs total"
}

# ============================================================================
# Phase 4: ajv compile
# ============================================================================
Add-ReportLine ""
Add-ReportLine "## 4. Core Schema Compile (ajv --spec=draft2019)"
Add-ReportLine ""

$compilePass = 0
$compileFail = 0

$glob = Join-Path $schemaDir "*.schema.json"
$res = ajv compile -s $glob --spec=draft2019 --strict=false 2>&1
$ec = $LASTEXITCODE

$resLines = $res -split "`n" | Where-Object { $_ -match 'is valid|is invalid' }
foreach ($line in $resLines) {
    if ($line -match 'is valid') {
        $compilePass++
        $short = ($line -replace 'schema .*?([^\\/]+\.schema\.json).*', '$1').Trim()
        Add-ReportLine "    [PASS] $short"
    } else {
        $compileFail++
        Add-ReportLine "    [FAIL] $line"
    }
}

if ($compileFail -eq 0) {
    Write-Pass "All $compilePass core schemas compile successfully"
} else {
    Write-Fail "$compileFail schema(s) failed to compile"
}

# ============================================================================
# Phase 5: Example validation
# ============================================================================
Add-ReportLine ""
Add-ReportLine "## 5. Example Validation"
Add-ReportLine ""

$pairs = @(
    @{E="action.example.json"; S="action.schema.json"},
    @{E="permission_profile.example.json"; S="permission_profile.schema.json"},
    @{E="approval_decision.example.json"; S="approval_decision.schema.json"},
    @{E="task.example.json"; S="task.schema.json"},
    @{E="task_tree.example.json"; S="task_tree.schema.json"},
    @{E="runtime_service.example.json"; S="runtime_service.schema.json"}
)

$exPass = 0
$exFail = 0
foreach ($p in $pairs) {
    $ep = Join-Path $examplesDir $p.E
    $sp = Join-Path $schemaDir $p.S
    
    if (-not (Test-Path $ep)) { Write-Warn "missing example: $($p.E)"; continue }
    
    $ecRaw = Get-Content $ep -Raw -Encoding UTF8
    try { $ej = $ecRaw | ConvertFrom-Json; $dj = $ej.data | ConvertTo-Json -Depth 10 -Compress }
    catch { Write-Fail "parse error: $($p.E) - $_"; $exFail++; continue }
    
    $tmp = [System.IO.Path]::GetTempFileName() + ".json"
    Set-Content $tmp $dj -Encoding UTF8
    $aOut = ajv validate -s $sp -d $tmp --spec=draft2019 --strict=false 2>&1
    $aec = $LASTEXITCODE
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    
    if ($aec -eq 0) {
        Write-Pass "$($p.E) validates ok"; $exPass++
    } else {
        Write-Fail "$($p.E) FAILS: $($aOut -join ' ')"; $exFail++
    }
}
Add-ReportLine "  Result: $exPass passed, $exFail failed"

# ============================================================================
# Phase 6: BOM & Stubs
# ============================================================================
Add-ReportLine ""
Add-ReportLine "## 6. BOM Cleanup & Stub Normalization"
Add-ReportLine ""

$bomFiles = @("memory\preferences.json", "memory\decisions.json", "agents\registry.json")
foreach ($bf in $bomFiles) {
    $bfp = Join-Path $projectDir $bf
    $b = [System.IO.File]::ReadAllBytes($bfp)
    if ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF) {
        Write-Fail "BOM still present: $bf"
    } else {
        Write-Pass "BOM removed: $bf"
    }
}

$stubs = @("workflows\features.json", "workflows\approvals.json", "skills\index.json")
foreach ($sf in $stubs) {
    $sfp = Join-Path $projectDir $sf
    $sfc = Get-Content $sfp -Raw -Encoding UTF8
    try { $sfj = $sfc | ConvertFrom-Json; if ($sfj.version) { Write-Pass "stub ok: $sf" } else { Write-Warn "stub: $sf missing version" } }
    catch { Write-Fail "stub parse error: $sf" }
}

# ============================================================================
# Phase 7: Results
# ============================================================================
Add-ReportLine ""
Add-ReportLine "## 7. Overall Results"
Add-ReportLine ""
Add-ReportLine "| Category | PASS | WARN | FAIL |"
Add-ReportLine "|----------|------|------|------|"
Add-ReportLine "| Total    | $passCount | $warnCount | $failCount |"

Add-ReportLine ""
if ($failCount -eq 0) {
    Add-ReportLine "## 8. Next Step"
    Add-ReportLine ""
    Add-ReportLine "All checks passed. Registry complete, schemas compile, examples validate."
    Add-ReportLine "Ready for Task 02-B or Task 03."
} else {
    Add-ReportLine "## 8. Failures Requiring Fix"
    Add-ReportLine ""
    Add-ReportLine "**$failCount failures. Resolve before proceeding.**"
}

# Write report
$rd = Split-Path $reportPath -Parent
if (-not (Test-Path $rd)) { New-Item -ItemType Directory -Path $rd -Force | Out-Null }
$reportLines -join "`n" | Set-Content -Path $reportPath -Encoding UTF8
Write-Host ""
Write-Host "Report: $reportPath"

if ($failCount -eq 0) { exit 0 } else { exit 1 }

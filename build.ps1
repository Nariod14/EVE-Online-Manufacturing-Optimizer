# Build the frontend, copy it into the backend, and build the exe.
#
#   .\build.ps1                 full build
#   .\build.ps1 -SkipFrontend   reuse manuoptimizer-frontend\out as it is
#   .\build.ps1 -SkipExe        frontend + copy only
#
# Or double-click build.bat. The exe ends up in ManuOptimizer-backend\dist\run.exe.
param(
    [switch]$SkipFrontend,
    [switch]$SkipExe
)

# Not "Stop": in Windows PowerShell 5.1 that turns a native tool's stderr (PyInstaller logs
# everything there) into an error. Each step checks $LASTEXITCODE instead.
$ErrorActionPreference = "Continue"
$root     = $PSScriptRoot
$frontend = Join-Path $root "manuoptimizer-frontend"
$backend  = Join-Path $root "ManuOptimizer-backend"
$python   = Join-Path $backend ".venv\Scripts\python.exe"

function Step($text) { Write-Host "`n=== $text ===" -ForegroundColor Cyan }
function Fail($text) { Write-Host "`nBUILD FAILED: $text" -ForegroundColor Red; exit 1 }

if (-not $SkipExe -and -not (Test-Path $python)) {
    Fail "No .venv found at $python"
}

# 1. Frontend
if (-not $SkipFrontend) {
    Step "Building frontend (npm run build)"
    Push-Location $frontend
    try {
        npm run build
        if ($LASTEXITCODE -ne 0) { Fail "npm run build exited with $LASTEXITCODE" }
    } finally {
        Pop-Location
    }
}

# 2. Copy frontend\out -> backend\out (mirror: files gone from the build are removed)
$src = Join-Path $frontend "out"
$dst = Join-Path $backend "out"
if (-not (Test-Path (Join-Path $src "index.html"))) {
    Fail "$src\index.html not found. Build the frontend first (run without -SkipFrontend)."
}
Step "Copying $src -> $dst"
robocopy $src $dst /MIR /NFL /NDL /NJH /NJS /NP | Out-Host
# robocopy: 0-7 = success (1 = files copied), 8+ = failure
if ($LASTEXITCODE -ge 8) { Fail "robocopy exited with $LASTEXITCODE" }

# 3. Exe
if (-not $SkipExe) {
    Step "Building exe (PyInstaller, from the .venv)"
    & $python -c "import PyInstaller" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Fail "PyInstaller is not installed in the .venv. Run: `"$python`" -m pip install pyinstaller==6.11.1"
    }
    Push-Location $backend
    try {
        & $python -m PyInstaller ManuOptimize.spec --noconfirm
        if ($LASTEXITCODE -ne 0) { Fail "PyInstaller exited with $LASTEXITCODE" }
    } finally {
        Pop-Location
    }
    Write-Host "`nDone: $(Join-Path $backend 'dist\run.exe')" -ForegroundColor Green
} else {
    Write-Host "`nDone (exe skipped)." -ForegroundColor Green
}
exit 0

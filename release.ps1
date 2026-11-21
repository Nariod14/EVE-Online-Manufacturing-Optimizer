# Build everything and zip run.exe for a GitHub release: releases\EOMO.<version>.zip
#
#   .\release.ps1                     asks for the version, builds, zips
#   .\release.ps1 -Version 2.1.0
#   .\release.ps1 -Version 2.1.0 -SkipBuild    zip the run.exe that is already in dist\
#
# Or double-click release.bat.
#
# The zip holds run.exe and a short README. Nothing else is needed: the PuLP solver
# (cbc.exe), the mini SDE and the frontend are inside run.exe, and the database is
# created next to run.exe (instances\eve_optimizer.db) the first time it starts.
param(
    [string]$Version,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Continue"   # see build.ps1: native tools write to stderr
$root    = $PSScriptRoot
$backend = Join-Path $root "ManuOptimizer-backend"
$exe     = Join-Path $backend "dist\run.exe"
$outDir  = Join-Path $root "releases"

function Fail($text) { Write-Host "`nRELEASE FAILED: $text" -ForegroundColor Red; exit 1 }

if (-not $Version) { $Version = Read-Host "Version (e.g. 2.1.0)" }
$Version = $Version.Trim().TrimStart("v", "V")
if ($Version -notmatch '^\d+(\.\d+){1,3}$') { Fail "'$Version' is not a version like 2.1.0" }

if (-not $SkipBuild) {
    & (Join-Path $root "build.ps1")
    if ($LASTEXITCODE -ne 0) { Fail "the build failed (see above)" }
}
if (-not (Test-Path $exe)) { Fail "$exe not found. Build first (run without -SkipBuild)." }

# Stage the files in a clean folder, then zip that folder's contents
$stage = Join-Path $outDir "EOMO.$Version"
$zip   = Join-Path $outDir "EOMO.$Version.zip"
New-Item -ItemType Directory -Force $outDir | Out-Null
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
if (Test-Path $zip) { Remove-Item -Force $zip }
New-Item -ItemType Directory -Force $stage | Out-Null

Copy-Item $exe (Join-Path $stage "run.exe")
@"
EVE Online Manufacturing Optimizer $Version
============================================

1. Unzip this folder anywhere.
2. Run run.exe. A console window opens and your browser goes to http://127.0.0.1:5000
3. The database is created next to run.exe (instances\eve_optimizer.db) on first start.
   Keep that folder when you update: copy your instances folder into the new version.

Log in with EVE SSO to update prices from your structures' markets.
"@ | Set-Content -Encoding UTF8 (Join-Path $stage "README.txt")

Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip
if (-not (Test-Path $zip)) { Fail "could not create $zip" }
Remove-Item -Recurse -Force $stage

$sizeMb = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host "`nDone: $zip ($sizeMb MB)" -ForegroundColor Green
Write-Host "Upload it on GitHub: Releases > Draft a new release > tag v$Version > attach the zip."
exit 0

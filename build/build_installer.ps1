# Postaz - one-shot build runner for the Windows installer.
#
# Pipeline:
#   1. Make sure pip dependencies are installed.
#   2. Generate build/postaz.ico from the painted in-app icon.
#   3. Run PyInstaller against build/postaz.spec - produces
#      build/dist/Postaz/Postaz.exe and friends.
#   4. Run Inno Setup against installer/postaz.iss - produces
#      installer/dist/Postaz-Setup-<version>.exe
#
# Usage (from project root, in PowerShell):
#     powershell -ExecutionPolicy Bypass -File build/build_installer.ps1
#
# After it finishes, attach the resulting Postaz-Setup-<version>.exe to a
# GitHub Release so end users can download and double-click to install.

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

Write-Host "==> ensuring Python dependencies..."
python -m pip install --quiet -r requirements.txt
python -m pip install --quiet pyinstaller Pillow

Write-Host "==> rendering app icon to .ico..."
python build\make_icon.py

Write-Host "==> running PyInstaller..."
# --workpath / --distpath keep all generated stuff under build/
python -m PyInstaller `
    --noconfirm `
    --clean `
    --workpath build\pyinstaller-work `
    --distpath build\dist `
    build\postaz.spec

if (-not (Test-Path "build\dist\Postaz\Postaz.exe")) {
    throw "PyInstaller did not produce Postaz.exe"
}

Write-Host "==> locating Inno Setup compiler..."
$iscc = $null
$candidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
foreach ($p in $candidates) {
    if (Test-Path $p) { $iscc = $p; break }
}
if (-not $iscc) {
    throw "Inno Setup 6 not found. Install from https://jrsoftware.org/isdl.php"
}
Write-Host "    using: $iscc"

Write-Host "==> compiling installer..."
& $iscc installer\postaz.iss

$out = Get-ChildItem installer\dist\Postaz-Setup-*.exe | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($out) {
    $size = [math]::Round($out.Length / 1MB, 1)
    Write-Host ""
    Write-Host "DONE - $($out.FullName) ($size MB)"
    Write-Host ""
    Write-Host "Next: upload to a GitHub Release:"
    Write-Host "    gh release upload v2.0.0 `"$($out.FullName)`""
} else {
    throw "installer compilation produced no output"
}

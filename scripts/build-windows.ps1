param([switch]$InstallDependencies)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($env:OS -ne 'Windows_NT') { throw 'Build on Windows, not WSL/Linux.' }
$Python = Join-Path $PWD '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) { throw 'Create the project .venv first.' }
if ($InstallDependencies) {
    & $Python -m pip install -e '.[hardware,desktop,qr,build]'
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
& $Python scripts\verify.py --require-node
if ($LASTEXITCODE -ne 0) { throw 'Tests failed or Node tests were skipped.' }
# This recipe is supplied for local qualification; no signed installer is claimed.
& $Python -m PyInstaller --noconfirm --clean --onedir --name nfcraft --collect-data nfcraft --collect-all webview --hidden-import pystray._win32 --collect-all smartcard run.py
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
Write-Host 'Unsigned build: dist\nfcraft. Test on a clean Windows profile; do not call this hardware-qualified.'

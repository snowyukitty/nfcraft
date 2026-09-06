param([switch]$Qr)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
# Local venv only. No admin, drivers, execution-policy changes, NFC writes or cloud operations.
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 -m venv .venv }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { & python -m venv .venv }
    else { throw 'Python 3.11+ is required. Install it from its official source, then retry.' }
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}
$Python = Join-Path $PWD '.venv\Scripts\python.exe'
& $Python scripts\preflight.py
if ($LASTEXITCODE -ne 0) { throw 'Preflight failed.' }
if ($Qr) {
    & $Python -m pip install -e '.[qr]'
    if ($LASTEXITCODE -ne 0) { throw 'Optional QR dependency installation failed.' }
}
& $Python scripts\verify.py
if ($LASTEXITCODE -ne 0) { throw 'Verification failed. Review .local\verification.' }
Write-Host 'Start with: .\.venv\Scripts\python.exe run.py'
Write-Host 'Read the verification summary. Missing Node checks are NOT_RUN, not a full pass.'

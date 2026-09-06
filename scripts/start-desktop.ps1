# Desktop shortcut entrypoint. Keep the console hidden and the native window visible.
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$PackagedApp = Join-Path $ProjectRoot 'dist\nfcraft\nfcraft.exe'
if (Test-Path -LiteralPath $PackagedApp) {
    Start-Process -FilePath $PackagedApp -ArgumentList @('--desktop', '--tray') -WorkingDirectory $ProjectRoot -WindowStyle Hidden
} else {
    $WindowedPython = Join-Path $ProjectRoot '.venv\Scripts\pythonw.exe'
    if (-not (Test-Path -LiteralPath $WindowedPython)) { throw 'Build nfcraft or install the local desktop extra first.' }
    $EntryPoint = Join-Path $ProjectRoot 'run.py'
    Start-Process -FilePath $WindowedPython -ArgumentList @(('"' + $EntryPoint + '"'), '--desktop', '--tray') -WorkingDirectory $ProjectRoot -WindowStyle Hidden
}

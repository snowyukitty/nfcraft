# Legacy developer launcher; the installed shortcut targets the GUI executable directly.
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$PackagedApp = Join-Path $ProjectRoot 'dist\nfcraft\nfcraft-desktop.exe'
if (Test-Path -LiteralPath $PackagedApp) {
    # The GUI subsystem needs no console-hiding flag: SW_HIDE also hides WinForms.
    Start-Process -FilePath $PackagedApp -WorkingDirectory $ProjectRoot
} else {
    $WindowedPython = Join-Path $ProjectRoot '.venv\Scripts\pythonw.exe'
    if (-not (Test-Path -LiteralPath $WindowedPython)) { throw 'Build nfcraft or install the local desktop extra first.' }
    Start-Process -FilePath $WindowedPython -ArgumentList @('-m', 'nfcraft.desktop_app') -WorkingDirectory $ProjectRoot
}

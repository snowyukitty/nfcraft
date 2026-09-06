param(
    [string]$Destination = [Environment]::GetFolderPath('Desktop'),
    [string]$Name = 'nfcraft',
    [string]$Arguments = ''
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Executable = Join-Path $ProjectRoot 'dist\nfcraft\nfcraft-desktop.exe'
$Icon = Join-Path $ProjectRoot 'nfcraft\web\icons\build\icon.ico'
$IconFlowPython = Join-Path (Split-Path $ProjectRoot -Parent) 'ai-iconflow\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Executable)) { throw 'Build the desktop executable first.' }
& $IconFlowPython -m iconflow shortcut --target $Executable --icon $Icon --name $Name --workdir (Split-Path $Executable -Parent) --out $Destination --content-address-icon
if ($LASTEXITCODE -ne 0) { throw 'IconFlow shortcut creation failed.' }
# IconFlow creates minimized shortcuts. A native app must start normally.
# Use an ASCII temporary path because WScript.Shell mishandles CJK .lnk paths.
$LinkPath = Join-Path $Destination ($Name + '.lnk')
$TemporaryLink = Join-Path ([IO.Path]::GetTempPath()) ('nfcraft-shortcut-' + [Guid]::NewGuid().ToString('N') + '.lnk')
try {
    Copy-Item -LiteralPath $LinkPath -Destination $TemporaryLink
    $Shell = New-Object -ComObject WScript.Shell
    $Link = $Shell.CreateShortcut($TemporaryLink)
    $Link.WindowStyle = 1
    # Assign through COM to preserve quotes across Windows PowerShell 5.1.
    $Link.Arguments = $Arguments
    $Link.Save()
    $Verified = $Shell.CreateShortcut($TemporaryLink)
    if ($Verified.WindowStyle -ne 1 -or $Verified.TargetPath -ne $Executable -or $Verified.Arguments -ne $Arguments) {
        throw 'Shortcut readback did not match the native launch contract.'
    }
    [IO.File]::Copy($TemporaryLink, $LinkPath, $true)
    Write-Output 'PASS: direct GUI target, exact arguments, normal window style.'
} finally {
    if (Test-Path -LiteralPath $TemporaryLink) { Remove-Item -LiteralPath $TemporaryLink }
}

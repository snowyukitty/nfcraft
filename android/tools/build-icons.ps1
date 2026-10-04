param(
    [string]$IconFlowPython = (Join-Path $PSScriptRoot '../../../ai-iconflow/.venv/Scripts/python.exe')
)
$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    function Invoke-IconFlow {
        & $IconFlowPython -m iconflow @args
        if ($LASTEXITCODE -ne 0) { throw 'IconFlow gate or render failed.' }
    }
    Invoke-IconFlow ship --config iconflow.toml --review master-review.json
    $densities = @{ mdpi = 48; hdpi = 72; xhdpi = 96; xxhdpi = 144; xxxhdpi = 192 }
    foreach ($density in $densities.Keys) {
        $directory = "app/src/main/res/mipmap-$density"
        Invoke-IconFlow render master.svg --sizes $densities[$density] --out "$directory/ic_launcher.png"
        Copy-Item -LiteralPath "$directory/ic_launcher.png" -Destination "$directory/ic_launcher_round.png"
    }
    Invoke-IconFlow render master.svg --sizes 512 --bg '#214b40' --out store/google-play-icon.png
    Invoke-IconFlow render master.svg --sizes 1024 --bg '#214b40' --out store/app-store-icon.png
} finally {
    Pop-Location
}

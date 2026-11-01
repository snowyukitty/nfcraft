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
    # Copy the reviewed Android target bytes; do not redraw adaptive layers.
    $generatedRoot = (Resolve-Path 'icons/android/res').Path
    $resourceRoot = (Resolve-Path 'app/src/main/res').Path
    foreach ($source in Get-ChildItem -LiteralPath $generatedRoot -File -Recurse) {
        $relative = $source.FullName.Substring($generatedRoot.Length + 1)
        $target = Join-Path $resourceRoot $relative
        New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
        Copy-Item -LiteralPath $source.FullName -Destination $target
    }
    # Existing API-33 resources must resolve to the same generated layers.
    foreach ($name in @('ic_launcher.xml', 'ic_launcher_round.xml')) {
        Copy-Item -LiteralPath "icons/android/res/mipmap-anydpi-v26/$name" `
            -Destination "app/src/main/res/mipmap-anydpi-v33/$name"
    }
    Copy-Item -LiteralPath 'icons/android/play-store-512.png' -Destination 'store/google-play-icon.png'
    Invoke-IconFlow render master.svg --sizes 1024 --bg '#214b40' --out store/app-store-icon.png
} finally {
    Pop-Location
}

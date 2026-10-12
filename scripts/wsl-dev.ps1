# Runs scripts/wsl-dev.sh in WSL. Usage: .\scripts\wsl-dev.ps1 [pywrangler dev args]
$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "wsl-dev.sh"
$wslScript = (wsl.exe wslpath -a ($script -replace '\\', '/')).Trim()
wsl.exe bash $wslScript @args
exit $LASTEXITCODE

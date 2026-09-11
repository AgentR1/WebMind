$ErrorActionPreference = "Stop"
$pluginRoot = Split-Path -Parent $PSScriptRoot
$dataRoot = if ($env:WEBUSE_DATA_DIR) { $env:WEBUSE_DATA_DIR } elseif ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA "WebUse" } else { Join-Path $env:USERPROFILE "AppData\Local\WebUse" }
$venvRoot = Join-Path $dataRoot ".venv"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"

New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    & $launcher.Source -3 -m venv $venvRoot
} else {
    $launcher = Get-Command python -ErrorAction Stop
    & $launcher.Source -m venv $venvRoot
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $pluginRoot "requirements.txt")
& $venvPython (Join-Path $pluginRoot "scripts\webuse.py") doctor

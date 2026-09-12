$ErrorActionPreference = "Stop"
if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    Write-Error "This edition requires native Windows PowerShell and Python."
    exit 1
}
$pluginRoot = Split-Path -Parent $PSScriptRoot
$dataRoot = if ($env:WEBMIND_DATA_DIR) { $env:WEBMIND_DATA_DIR } elseif ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA "WebMind" } else { Join-Path $env:USERPROFILE "AppData\Local\WebMind" }
$venvRoot = Join-Path $dataRoot ".venv"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"

New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    $pythonArguments = @("-3")
} else {
    $launcher = Get-Command python -ErrorAction Stop
    $pythonArguments = @()
}

& $launcher.Source @pythonArguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python 3.10 or newer is required."
    exit 1
}

& $launcher.Source @pythonArguments -m venv $venvRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $venvPython -m pip install -r (Join-Path $pluginRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $venvPython (Join-Path $pluginRoot "scripts\webmind.py") doctor
exit $LASTEXITCODE

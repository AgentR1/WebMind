$ErrorActionPreference = "Stop"
if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    Write-Error "This edition requires native Windows PowerShell and Python."
    exit 1
}
$pluginRoot = Split-Path -Parent $PSScriptRoot
$dataRoot = if ($env:WEBMIND_DATA_DIR) { $env:WEBMIND_DATA_DIR } elseif ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA "WebMind" } else { Join-Path $env:USERPROFILE "AppData\Local\WebMind" }
$venvPython = Join-Path $dataRoot ".venv\Scripts\python.exe"
$dispatcher = Join-Path $pluginRoot "scripts\webmind.py"

if (Test-Path -LiteralPath $venvPython) {
    & $venvPython $dispatcher @args
    exit $LASTEXITCODE
}

$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    & $launcher.Source -3 $dispatcher @args
    exit $LASTEXITCODE
}

$launcher = Get-Command python -ErrorAction SilentlyContinue
if ($launcher) {
    & $launcher.Source $dispatcher @args
    exit $LASTEXITCODE
}

Write-Error "Python 3.10 or newer was not found. Install Python, then run scripts\install.ps1."
exit 1

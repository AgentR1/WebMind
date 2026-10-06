$ErrorActionPreference = "Stop"
if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    Write-Error "This edition requires native Windows PowerShell and Python."
    exit 1
}
if ($env:WEBMIND_PYTHON) {
    $pythonExecutable = $env:WEBMIND_PYTHON
    $pythonArguments = @()
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExecutable = (Get-Command py).Source
    $pythonArguments = @("-3")
} else {
    $pythonExecutable = (Get-Command python -ErrorAction Stop).Source
    $pythonArguments = @()
}
& $pythonExecutable @pythonArguments -B (Join-Path $PSScriptRoot "install.py") @args
exit $LASTEXITCODE

$ErrorActionPreference = 'Stop'
if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    Write-Error "This edition requires native Windows PowerShell and Python."
    exit 1
}
$root = Split-Path -Parent $PSScriptRoot
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
try { [Console]::InputEncoding = $OutputEncoding; [Console]::OutputEncoding = $OutputEncoding } catch {}
$pythonArgs = @()
if ($env:WEBMIND_PYTHON) {
    $python = $env:WEBMIND_PYTHON
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $python = (Get-Command py).Source
    $pythonArgs = @('-3')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = (Get-Command python).Source
} else {
    Write-Error 'Python 3.10+ is required. Install Python or set WEBMIND_PYTHON to its executable.'
    exit 1
}
$commandArgs = $pythonArgs + @('-B', (Join-Path $root 'scripts\bootstrap.py')) + $args
if ($MyInvocation.ExpectingInput) {
    $input | & $python @commandArgs
} else {
    & $python @commandArgs
}
exit $LASTEXITCODE

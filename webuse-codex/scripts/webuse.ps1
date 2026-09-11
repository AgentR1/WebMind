$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
try { [Console]::InputEncoding = $OutputEncoding; [Console]::OutputEncoding = $OutputEncoding } catch {}
$pythonArgs = @()
if ($env:WEBUSE_PYTHON) {
    $python = $env:WEBUSE_PYTHON
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $python = (Get-Command py).Source
    $pythonArgs = @('-3')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = (Get-Command python).Source
} else {
    Write-Error 'Python 3.10+ is required. Install Python or set WEBUSE_PYTHON to its executable.'
    exit 1
}
$commandArgs = $pythonArgs + @('-B', (Join-Path $root 'scripts\bootstrap.py')) + $args
if ($MyInvocation.ExpectingInput) {
    $input | & $python @commandArgs
} else {
    & $python @commandArgs
}
exit $LASTEXITCODE

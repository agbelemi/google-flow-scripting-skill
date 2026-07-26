$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    $Python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $Python) {
    throw "Python 3 is required. Install Python, then run this script again."
}
& $Python.Source (Join-Path $ScriptRoot "update.py") @args
exit $LASTEXITCODE

# OSINT WordGen launcher (Windows PowerShell)
# Usage:  .\run.ps1                     interactive run
#         .\run.ps1 -i simple_input.json -m 50000
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Venv = Join-Path $Root ".venv"
$Py   = Join-Path $Venv "Scripts\python.exe"

if (-not (Test-Path $Py)) {
    Write-Host "[*] Creating virtual environment..." -ForegroundColor Green
    python -m venv $Venv
    & $Py -m pip install --upgrade pip
    & $Py -m pip install -r (Join-Path $Root "requirements.txt")
}

& $Py (Join-Path $Root "main.py") @args
exit $LASTEXITCODE

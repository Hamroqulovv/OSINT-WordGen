@echo off
REM OSINT WordGen launcher (Windows cmd.exe)
REM Usage:  run.bat                     interactive run
REM         run.bat -i simple_input.json -m 50000
setlocal
set "ROOT=%~dp0"
set "VENV=%ROOT%.venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
    echo [*] Creating virtual environment...
    python -m venv "%VENV%"
    "%PY%" -m pip install --upgrade pip
    "%PY%" -m pip install -r "%ROOT%requirements.txt"
)

"%PY%" "%ROOT%main.py" %*

@echo off
echo =========================================
echo   PT SK 2.0 - STARTING
echo =========================================

cd /d "%~dp0"

IF NOT EXIST "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    echo Installing requirements...
    venv\Scripts\pip.exe install -r requirements.txt
)

echo Starting application...
venv\Scripts\python.exe app.py
pause

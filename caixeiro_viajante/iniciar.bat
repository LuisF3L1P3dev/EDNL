@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Crie o ambiente virtual e instale requirements.txt conforme o README.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" main.py %*
if errorlevel 1 pause


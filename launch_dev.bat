@echo off
cd /d "C:\Users\Administrator\Desktop\LeagueLoop"
set PYTHONPATH=%CD%\src

:: Initialize error log if it doesn't exist so the tail command doesn't fail
if not exist error.log type nul > error.log

".venv\Scripts\python.exe" -m core.main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo === CRASHED - see error.log ===
    pause
)

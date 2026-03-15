@echo off
cd /d "C:\Users\Administrator\antigravity-worspaces-1\LeagueLoop"
set PYTHONPATH=%CD%

:: Initialize error log if it doesn't exist so the tail command doesn't fail
if not exist error.log type nul > error.log

:: Pop open a real-time monitor for the error log
start "LeagueLoop Error Monitor" cmd /c "powershell -NoProfile -Command Get-Content error.log -Wait -Tail 20"

:: Small delay to let the monitor release its initial lock
ping 127.0.0.1 -n 2 > nul

"C:\Users\Administrator\antigravity-worspaces-1\antigravity-worspaces\.venv\Scripts\python.exe" -m core.main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo === CRASHED - see error.log ===
    pause
)

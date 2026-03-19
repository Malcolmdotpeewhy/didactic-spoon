@echo off
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist\LeagueLoop rmdir /s /q dist\LeagueLoop
if exist dist\LeagueLoop.exe del /f /q dist\LeagueLoop.exe
echo.
echo Building LeagueLoop ONEFILE executable...
echo This will take a moment, gathering all dependencies...
pyinstaller --clean LeagueLoop.spec
echo.
echo Build complete! Your standalone executable is ready:
echo dist\LeagueLoop.exe
pause

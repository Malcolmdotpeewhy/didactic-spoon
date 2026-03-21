@echo off
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist\LeagueLoop rmdir /s /q dist\LeagueLoop
if exist dist\LeagueLoop.exe del /f /q dist\LeagueLoop.exe
echo.
echo Building LeagueLoop ONEDIR executable...
echo This will take a moment, gathering all dependencies...
pyinstaller --clean LeagueLoop.spec
echo.
if exist dist\LeagueLoop\LeagueLoop.exe (
    echo Build complete! Output folder: dist\LeagueLoop\
    echo.
    echo To create the installer, run Inno Setup with installer.iss
) else (
    echo BUILD FAILED - check output above for errors
)
pause

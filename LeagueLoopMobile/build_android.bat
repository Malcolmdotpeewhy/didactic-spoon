@echo off
setlocal
echo ===================================================
echo LeagueLoop Mobile - Android Release Build System
echo ===================================================

echo [1/3] Building Web Assets (Vite)...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Vite build failed.
    exit /b %ERRORLEVEL%
)

echo [2/3] Syncing Capacitor native files...
call npx cap sync android
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Capacitor sync failed.
    exit /b %ERRORLEVEL%
)

echo [3/3] Compiling Release APK and AAB via Gradle...
pushd android

:: Build APK (for direct sideloading or alternative stores)
call gradlew.bat assembleRelease
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] APK Gradle build failed.
    popd
    exit /b %ERRORLEVEL%
)

:: Build AAB (Required for Google Play Store)
call gradlew.bat bundleRelease
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] AAB Gradle build failed.
    popd
    exit /b %ERRORLEVEL%
)
popd

echo.
echo ===================================================
echo [SUCCESS] Build Completed!
echo ===================================================
echo Your release artifacts have been generated. Note: They are unsigned.
echo Before uploading to the Google Play Store, you must sign the AAB.
echo.
echo APK (Direct Download): android\app\build\outputs\apk\release\app-release-unsigned.apk
echo AAB (Play Store Bundle): android\app\build\outputs\bundle\release\app-release.aab
echo ===================================================
echo Read README_ANDROID.md for instructions on how to generate a keystore and sign these files.
pause

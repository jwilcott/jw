@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%Deploy_JW_CommandSearch.ps1"
set "DEST_ROOT=C:\Program Files\Maxon ZBrush 2025\ZStartup\Macros"

if not exist "%PS_SCRIPT%" (
    echo Deploy script not found:
    echo   "%PS_SCRIPT%"
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -DestinationRoot "%DEST_ROOT%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Deployment failed with exit code %EXIT_CODE%.
    pause
    exit /b %EXIT_CODE%
)

echo.
pause
exit /b 0

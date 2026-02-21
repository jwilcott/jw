@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Path to Maya executable
set "MAYA_EXE=C:\Program Files\Autodesk\Maya2025\bin\maya.exe"
set "KILL_SCRIPT=%~dp0killMaya.ps1"
set "IS_ELEVATED_RUN=0"
if /I "%~1"=="--elevated" set "IS_ELEVATED_RUN=1"

if not exist "%MAYA_EXE%" (
	echo Maya executable not found:
	echo   "%MAYA_EXE%"
	exit /b 1
)

if not exist "%KILL_SCRIPT%" (
	echo Kill script not found:
	echo   "%KILL_SCRIPT%"
	exit /b 1
)

echo Closing existing Maya processes...
powershell -NoProfile -ExecutionPolicy Bypass -File "%KILL_SCRIPT%"
set "KILL_EXIT=%ERRORLEVEL%"

if "%KILL_EXIT%"=="0" goto launch_maya

:give_up
echo Warning: Some Maya processes are still running after retries.

if "%IS_ELEVATED_RUN%"=="0" (
	net session >nul 2>&1
	if errorlevel 1 (
		echo Trying one more time with Administrator privileges...
		powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -ArgumentList '--elevated' -Verb RunAs"
		exit /b 0
	)
)

echo Fallback kill via taskkill...
taskkill /IM maya.exe /T /F >nul 2>&1
taskkill /IM mayabatch.exe /T /F >nul 2>&1
taskkill /IM mayapy.exe /T /F >nul 2>&1

echo Attempting to launch a new Maya instance anyway...

:launch_maya
echo Launching Maya 2025...
start "" "%MAYA_EXE%"
exit /b 0

@echo off
REM Kill any process named maya
taskkill /IM maya.exe /F

REM Launch Maya 2025
start "" "C:\Program Files\Autodesk\Maya2025\bin\maya.exe"

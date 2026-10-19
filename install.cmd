@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if errorlevel 1 (
    echo Installation failed. Read the error above and see docs\INSTALL.md.
    pause
    exit /b 1
)
echo Installation complete. Double-click start.cmd to launch QuickSpeak.
pause

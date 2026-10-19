@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1"
if errorlevel 1 (
    echo Run install.cmd first. See docs\INSTALL.md for help.
    pause
    exit /b 1
)

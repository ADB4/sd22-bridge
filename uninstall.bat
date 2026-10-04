@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"
set rc=%ERRORLEVEL%
echo.
rem Keep a double-clicked window open, but don't wait when a script or tool runs this without a console.
powershell -NoProfile -Command "exit ([int][Console]::IsInputRedirected)"
if not errorlevel 1 pause
exit /b %rc%

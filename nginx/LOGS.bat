@echo off
rem LOGS.bat - show who is using the website, live. Press Ctrl+C to stop.
setlocal
set "NGX="
for /d %%D in ("%~dp0win\nginx-*") do set "NGX=%%D"
set "LOG=%NGX%\logs\luma.access.log"
if not exist "%LOG%" (
  echo No log yet - double-click START.bat and open the website first.
  pause
  exit /b 1
)
echo Live requests - IP, time, request, status, bytes, seconds. Press Ctrl+C to stop.
echo.
powershell -NoProfile -Command "Get-Content -LiteralPath '%LOG%' -Wait -Tail 20"

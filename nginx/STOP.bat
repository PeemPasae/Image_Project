@echo off
rem STOP.bat - stop nginx (graceful, then force if still running)
setlocal
set "NGX="
for /d %%D in ("%~dp0win\nginx-*") do set "NGX=%%D"
if defined NGX if exist "%NGX%\nginx.exe" (
  pushd "%NGX%"
  nginx.exe -s quit 2>nul
  popd
  timeout /t 2 >nul
)
tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul
if %errorlevel%==0 taskkill /IM nginx.exe /F >nul
echo nginx stopped.
pause

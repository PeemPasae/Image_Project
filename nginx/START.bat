@echo off
setlocal
rem ==================================================================
rem  START.bat - start nginx for LUMA (or reload it after editing conf\)
rem    1) copy nginx\conf\*.conf into the nginx program folder
rem    2) test the config
rem    3) start nginx, or reload it if it is already running
rem ==================================================================
set "HERE=%~dp0"
set "NGX="
for /d %%D in ("%HERE%win\nginx-*") do set "NGX=%%D"
if not defined NGX goto :no_nginx
if not exist "%NGX%\nginx.exe" goto :no_nginx

if not exist "%HERE%..\frontend\luma-frontend\dist\index.html" (
  echo [!] Website not built yet - double-click BUILD-WEB.bat first.
  echo.
)

echo [1/3] Copy config from nginx\conf ...
copy /Y "%HERE%conf\*.conf" "%NGX%\conf\" >nul || goto :fail
if exist "%HERE%luma_dev.htpasswd" copy /Y "%HERE%luma_dev.htpasswd" "%NGX%\conf\" >nul

cd /d "%NGX%" || goto :fail
echo [2/3] Test config ...
nginx.exe -t
if errorlevel 1 goto :fail

echo [3/3] Start or reload nginx ...
tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul
if %errorlevel%==0 goto :reload

netstat -ano | findstr /R /C:":80 .*LISTENING" >nul
if %errorlevel%==0 echo [!] Port 80 is already used by another program - nginx may fail to start.
start "" nginx.exe
timeout /t 2 >nul
tasklist /FI "IMAGENAME eq nginx.exe" 2>nul | find /I "nginx.exe" >nul
if errorlevel 1 goto :fail
echo nginx started.
goto :done

:reload
nginx.exe -s reload
if errorlevel 1 goto :fail
echo nginx was already running - reloaded with the new config.

:done
echo.
echo   This PC : http://localhost/
echo   Others  : http://THIS-PC-IP/   - run ipconfig to see the IPv4 address
echo   Health  : http://localhost/api/v1/health
echo.
pause
exit /b 0

:no_nginx
echo [X] nginx program not found.
echo     Download the Windows zip from https://nginx.org/en/download.html
echo     and unzip it into nginx\win\  so you get  nginx\win\nginx-x.y.z\nginx.exe
pause
exit /b 1

:fail
echo.
echo [X] Failed. Read the message above, or the log: nginx\win\nginx-*\logs\error.log
pause
exit /b 1

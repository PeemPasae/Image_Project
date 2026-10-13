@echo off
rem BUILD-WEB.bat - rebuild the website (frontend\luma-frontend\dist) after git pull
setlocal
cd /d "%~dp0..\frontend\luma-frontend" || goto :fail
if not exist node_modules (
  echo [1/2] npm install ...
  call npm install || goto :fail
)
echo Building website ...
call npm run build || goto :fail
echo.
echo Done. Refresh the browser - no need to restart nginx.
pause
exit /b 0
:fail
echo.
echo [X] Build failed - read the message above. Is Node.js installed?
pause
exit /b 1

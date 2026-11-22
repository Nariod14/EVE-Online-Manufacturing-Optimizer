@echo off
rem Double-click to build the frontend, copy it into the backend and build the exe.
rem Extra arguments are passed on, e.g.  build.bat -SkipFrontend
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" %*
echo.
pause

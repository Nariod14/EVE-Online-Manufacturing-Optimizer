@echo off
rem Double-click to build everything and zip run.exe into releases\EOMO.<version>.zip
rem Extra arguments are passed on, e.g.  release.bat -Version 2.1.0 -SkipBuild
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0release.ps1" %*
echo.
pause

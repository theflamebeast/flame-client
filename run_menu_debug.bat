@echo off
setlocal
cd /d "%~dp0"
echo Starting Flame Client Manager (console mode, verbose)...
echo.
py -3 -X dev settings_menu.py
if errorlevel 1 (
  echo.
  echo Flame Client Manager exited with an error.
  pause
)
endlocal

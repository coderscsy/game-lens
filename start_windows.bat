@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 server.py
    goto finished
)
where python >nul 2>nul
if %errorlevel% equ 0 (
    python server.py
    goto finished
)
echo Python was not found. Please install Python 3.10 or newer.
echo You can still open steam_lens.html to use the offline demo.
:finished
echo.
echo The local service has stopped. See README for details.
pause
endlocal

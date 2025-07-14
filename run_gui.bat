@echo off
echo WatchMan GUI - Starting...
echo ==========================
echo.

python gui/main.py
if %errorlevel% neq 0 (
    echo Error starting GUI
    pause
    exit /b 1
)

pause

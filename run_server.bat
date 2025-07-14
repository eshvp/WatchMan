@echo off
echo WatchMan System - Quick Start
echo =============================
echo.

echo Installing Python dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing dependencies
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.

echo Starting WatchMan Server...
python server/main.py

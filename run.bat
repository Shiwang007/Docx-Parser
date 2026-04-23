@echo off
SETLOCAL EnableDelayedExpansion

echo ===================================================
echo   Medjeex Exam Studio - Unified Launcher
echo ===================================================

:: Force UTF-8 encoding for math symbols
set PYTHONIOENCODING=utf-8

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+ and add it to PATH.
    pause
    exit /b
)

:: 2. Check for Virtual Environment
if not exist "venv" (
    echo [SETUP] First-time setup detected. Creating virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b
    )
    
    echo [SETUP] Installing dependencies (this may take a minute)...
    venv\Scripts\python -m pip install --upgrade pip
    venv\Scripts\pip install -r requirements.txt
)

:: 3. Launch the Studio
echo [START] Launching Medjeex Exam Studio on Port 8001...
echo [INFO] Once started, open: http://localhost:8001
echo ===================================================

venv\Scripts\python -m uvicorn app:app --host 0.0.0.0 --port 8001

pause

@echo off
REM ============================================================
REM   FangYan Interactive - Backend Launcher
REM   Auto-selects best Python version (prefers 3.11 / 3.12)
REM ============================================================
cd /d "%~dp0"

echo.
echo ============================================================
echo   FangYan Interactive  -  Backend Launcher
echo ============================================================
echo.

REM --- Choose Python: prefer 3.11, then 3.12, 3.10, default ---
set PYCMD=
py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set PYCMD=py -3.11
    echo Using Python 3.11
    goto found
)
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set PYCMD=py -3.12
    echo Using Python 3.12
    goto found
)
py -3.10 --version >nul 2>&1
if not errorlevel 1 (
    set PYCMD=py -3.10
    echo Using Python 3.10
    goto found
)
echo [WARN] Python 3.10-3.12 not found, falling back to default python
echo        Python 3.14 may fail to install some dependencies
echo        Recommended: install Python 3.11 from python.org
set PYCMD=python

:found
echo Python command: %PYCMD%
echo.

REM --- Step 1: Create venv ---
if not exist ".venv" (
    echo [1/4] Creating virtual environment .venv ...
    %PYCMD% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
)

REM --- Step 2: Activate ---
echo [2/4] Activating virtual environment ...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate venv.
    pause
    exit /b 1
)

REM --- Step 3: Install dependencies ---
echo [3/4] Installing dependencies ^(first run takes a few minutes^) ...
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [ERROR] Install failed. Try running install_direct.bat instead.
    pause
    exit /b 1
)

REM --- Step 4: Start server ---
echo [4/4] Starting FastAPI server ...
echo.
echo ============================================================
echo   Frontend:  http://127.0.0.1:8000/
echo   API Docs:  http://127.0.0.1:8000/docs
echo   Press Ctrl+C to stop
echo ============================================================
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause

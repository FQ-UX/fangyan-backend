@echo off
REM ============================================================
REM   Install dependencies directly (no venv)
REM   Use this if start.bat fails
REM ============================================================
cd /d "%~dp0"

echo Installing dependencies globally (no venv) ...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if errorlevel 1 (
    echo Trying default PyPI...
    python -m pip install -r requirements.txt
)

echo.
echo Done. Now run: run_direct.bat
pause

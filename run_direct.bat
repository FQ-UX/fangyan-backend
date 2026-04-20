@echo off
cd /d "%~dp0"
echo.
echo ============================================================
echo   Frontend:  http://127.0.0.1:8000/
echo   API Docs:  http://127.0.0.1:8000/docs
echo ============================================================
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause

@echo off
REM One-click launcher for the demo (Windows). Usage: run.bat [port]
setlocal
cd /d "%~dp0"
set PORT=%1
if "%PORT%"=="" set PORT=8077
if not exist .venv (
  echo Creating virtual environment...
  py -3.12 -m venv .venv || python -m venv .venv
  .venv\Scripts\python -m pip install -q -r requirements.txt
)
if not exist .env copy .env.example .env >nul
if not defined NO_BROWSER start "" /min cmd /c "timeout /t 4 /nobreak >nul & start http://localhost:%PORT%/"
.venv\Scripts\python -m uvicorn app.main:app --port %PORT%

@echo off
setlocal
set ROOT=%~dp0
cd /d "%ROOT%"

echo Setting up backend...
if not exist backend\.venv (
  python -m venv backend\.venv
)
call backend\.venv\Scripts\python -m pip install -r backend\requirements.txt

echo Starting backend...
start "Backend" cmd /k "cd /d %ROOT%backend && .\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

echo Setting up frontend...
if not exist frontend\node_modules (
  pushd frontend
  npm install
  popd
)

echo Starting frontend...
start "Frontend" cmd /k "cd /d %ROOT%frontend && npm run dev -- --port 5173"

echo Opening browser...
start "" "http://localhost:5173"

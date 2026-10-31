@echo off
REM Starts the ScamShield backend (port 8000) and frontend (port 5173) in two windows.
start "ScamShield API" cmd /k "cd /d %~dp0backend && uv run uvicorn app.main:app --port 8000"
start "ScamShield UI" cmd /k "cd /d %~dp0frontend && npm run dev"
echo Open http://localhost:5173

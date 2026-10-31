@echo off
REM Same as start-local.bat but serves the UI over HTTPS so a phone on your Wi-Fi can use the camera QR scanner.
REM On the phone open the https://<this-pc-ip>:5173 address printed in the UI window and accept the certificate warning.
start "ScamShield API" cmd /k "cd /d %~dp0backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000"
start "ScamShield UI (phone)" cmd /k "cd /d %~dp0frontend && npm run dev:phone"

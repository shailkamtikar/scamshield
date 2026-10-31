@echo off
REM Serves the UI over HTTPS so a phone on the same Wi-Fi can open it and use the camera QR scanner.
REM 1) Wait for the "Network: https://192.168.x.x:5173" line in the UI window.
REM 2) On the phone (same Wi-Fi) open that https:// address, tap Advanced > Proceed (the certificate is self-signed).
REM If it never loads, allow "Node.js" through Windows Firewall on Private networks when Windows asks.
start "ScamShield API" cmd /k "cd /d %~dp0backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000"
start "ScamShield UI (phone)" cmd /k "cd /d %~dp0frontend && npm run phone"

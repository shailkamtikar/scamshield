@echo off
REM Opens ScamShield for a phone on the same Wi-Fi. Two ways in; use the "Network" address printed in each UI window:
REM   https://192.168.x.x:5173   self-signed certificate, needed for the live camera QR scanner (tap Advanced > Proceed)
REM   http://192.168.x.x:5175    plain http, always loads; use this first to check the phone can reach the PC.
REM                              Screenshot and QR-image upload work on it. For the camera over http, on the phone open
REM                              chrome://flags/#unsafely-treat-insecure-origin-as-secure, add the http address, relaunch Chrome.
start "ScamShield API" cmd /k "cd /d %~dp0backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000"
start "ScamShield UI (https :5173)" cmd /k "cd /d %~dp0frontend && npm run phone"
start "ScamShield UI (http :5175)" cmd /k "cd /d %~dp0frontend && timeout /t 12 /nobreak >nul && set NO_TLS=1&& set PREVIEW_PORT=5175&& npm run phone:http"

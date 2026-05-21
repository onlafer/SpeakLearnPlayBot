@echo off
title SpeakLearnPlay Launcher

echo ===================================================
echo   Starting SpeakLearnPlayBot (Local Full Stack)
echo ===================================================
echo.

:: 1. Start API (Backend)
echo [1/4] Starting FastAPI Backend on port 8001...
start "SpeakLearnPlay API" cmd /k "uv run python -m api.main"
timeout /t 2 > nul

:: 2. Start Vite Dev Server (Frontend)
echo [2/4] Starting React/Vite Frontend on port 5173...
start "SpeakLearnPlay Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 3 > nul

:: 3. Start SSH Tunnel on port 5173
echo [3/4] Starting SSH Tunnel to port 5173...
echo Copy the HTTPS link (starts with https://) from the tunnel window.
echo.
start "SpeakLearnPlay Tunnel" cmd /k "ssh -R 80:localhost:5173 nokey@localhost.run"
timeout /t 3 > nul

echo ===================================================
echo   CONFIGURATION INSTRUCTIONS:
echo ===================================================
echo 1. IF TESTING ON PC (Telegram Desktop):
echo    You can set in config\.env:
echo    WEBAPP_URL=http://localhost:5173/streak
echo.
echo 2. IF TESTING ON PHONE (or via Internet):
echo    Copy the HTTPS link from the tunnel window (e.g. https://xxxx.lhr.life)
echo    And set in config\.env:
echo    WEBAPP_URL=https://xxxx.lhr.life/streak
echo.
echo Save config\.env and press any key in this window to start the Telegram Bot...
pause > nul

echo.
echo [4/4] Starting Telegram Bot...
uv run main.py

echo.
echo Bot stopped. Press any key to exit...
pause > nul

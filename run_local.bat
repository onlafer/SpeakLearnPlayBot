@echo off
title SpeakLearnPlay Launcher

echo ===================================================
echo   Starting SpeakLearnPlayBot (Local Full Stack)
echo ===================================================
echo.
echo Running the automated launcher script...
echo.

uv run python run_local.py

echo.
echo Launcher exited. Press any key to close...
pause > nul


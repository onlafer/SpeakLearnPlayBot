@echo off
title SpeakLearnPlay Auto Deployer

echo ===================================================
echo   Auto-Deploying SpeakLearnPlay to GitHub & Vercel
echo ===================================================
echo.

:: 1. Build frontend
echo [1/3] Building React Frontend locally...
cd frontend
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed!
    cd ..
    pause
    exit /b %errorlevel%
)
cd ..
echo.

:: 2. Stage changes
echo [2/3] Staging changes in Git...
git add .
echo.

:: 3. Commit changes
set /p commit_msg="Enter commit message (or press Enter for default): "
if "%commit_msg%"=="" (
    set commit_msg="dev: update webapp and backend integration"
)

echo Creating commit...
git commit -m "%commit_msg%"
echo.

:: 4. Push to remote dev branch
echo [3/3] Pushing to GitHub (dev branch)...
git push origin dev
if %errorlevel% neq 0 (
    echo [ERROR] Git push failed!
    pause
    exit /b %errorlevel%
)

echo ===================================================
echo   SUCCESS! Changes pushed to GitHub.
echo   Vercel is now automatically rebuilding your app!
echo ===================================================
echo.
pause

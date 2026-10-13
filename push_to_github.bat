@echo off
echo ========================================================
echo   Pushing LinkedIn Profile AI Analyzer to GitHub
echo   Repository: https://github.com/sameerbag/linkedin-profile-ai-analyzer
echo ========================================================
echo.

REM Set Git path
set "GIT_CMD=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"

if not exist "%GIT_CMD%" (
    set "GIT_CMD=git"
)

echo Checking Git status...
"%GIT_CMD%" status

echo.
echo Pushing branch 'main' to origin...
"%GIT_CMD%" push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   SUCCESS! Pushed to https://github.com/sameerbag/linkedin-profile-ai-analyzer
    echo ========================================================
) else (
    echo.
    echo PUSH FAILED!
    echo Please make sure:
    echo 1. You created the repository at: https://github.com/new
    echo    Name: linkedin-profile-ai-analyzer
    echo 2. You are logged into GitHub when prompted.
)

pause

@echo off
echo ========================================================
echo   Launching LinkedIn Profile AI Analyzer & Optimizer
echo ========================================================
echo.

REM Check if Python is in path, otherwise fallback to local AppData Python
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python -m streamlit run app.py
) else (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" -m streamlit run app.py
)

pause

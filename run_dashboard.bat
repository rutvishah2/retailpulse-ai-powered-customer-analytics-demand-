@echo off
REM RetailPulse - Run Dashboard (Windows)

echo.
echo ======================================
echo 📊 RetailPulse - Interactive Dashboard
echo ======================================
echo.

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️  Virtual environment not activated!
    echo Please run: venv\Scripts\activate.bat
    pause
    exit /b 1
)

REM Set environment variables
set PYTHONUNBUFFERED=1

REM Run Streamlit dashboard
echo 🚀 Launching Streamlit dashboard...
echo.
echo 📈 Dashboard URL: http://localhost:8501
echo.

streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0

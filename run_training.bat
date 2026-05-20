@echo off
REM RetailPulse - Run Training Pipeline (Windows)

echo.
echo ====================================
echo 🚀 RetailPulse - Training Pipeline
echo ====================================
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
set PYTHONDONTWRITEBYTECODE=1

REM Run training pipeline
echo 📊 Starting training pipeline...
echo.

python train.py

echo.
echo ====================================
echo ✅ Training pipeline completed!
echo ====================================
echo.
echo 📁 Output files saved to: outputs/
echo 📊 View results in MLflow UI: mlflow ui
echo 📈 Launch dashboard: streamlit run dashboard/app.py
echo.
pause

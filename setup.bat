@echo off
REM RetailPulse - Quick Setup Script (Windows)
REM This script automates the initial setup of RetailPulse

echo.
echo ===================================
echo 🚀 RetailPulse - Quick Setup Script (Windows)
echo ===================================
echo.

REM Check Python version
echo 📌 Checking Python version...
python --version
echo.

REM Create virtual environment
if not exist "venv" (
    echo 📌 Creating virtual environment...
    python -m venv venv
    echo    ✅ Virtual environment created
) else (
    echo    ✅ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo 📌 Activating virtual environment...
call venv\Scripts\activate.bat
echo    ✅ Virtual environment activated
echo.

REM Upgrade pip
echo 📌 Upgrading pip...
python -m pip install --upgrade pip setuptools wheel
echo    ✅ pip upgraded
echo.

REM Install dependencies
echo 📌 Installing dependencies...
pip install -r requirements.txt
echo    ✅ Dependencies installed
echo.

REM Setup configuration
if not exist ".env" (
    echo 📌 Setting up environment configuration...
    copy .env.example .env
    echo    ✅ Created .env file
    echo    ⚠️  Please update .env with your settings
) else (
    echo    ✅ .env already exists
)
echo.

REM Create necessary directories
echo 📌 Creating directories...
if not exist "logs" mkdir logs
if not exist "models_saved" mkdir models_saved
if not exist "cache" mkdir cache
if not exist "outputs" mkdir outputs
echo    ✅ Directories created
echo.

REM Test imports
echo 📌 Testing Python imports...
python -c "import pandas; import numpy; import torch; import streamlit; import mlflow; print('   ✅ All imports successful')"
echo.

echo ===================================
echo ✅ Setup completed successfully!
echo ===================================
echo.
echo 🚀 Next steps:
echo    1. Run training: python train.py
echo    2. Launch dashboard: streamlit run dashboard/app.py
echo    3. View notebooks: jupyter notebook notebook/RetailPulse.ipynb
echo.
pause

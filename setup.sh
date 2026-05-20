#!/bin/bash
# RetailPulse - Quick Setup Script
# This script automates the initial setup of RetailPulse

set -e

echo "🚀 RetailPulse - Quick Setup Script"
echo "=================================="
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📌 Creating virtual environment..."
    python -m venv venv
    echo "   ✅ Virtual environment created"
fi

# Activate virtual environment
echo "📌 Activating virtual environment..."
source venv/Scripts/activate || source venv/bin/activate
echo "   ✅ Virtual environment activated"

# Upgrade pip
echo "📌 Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo "   ✅ pip upgraded"

# Install dependencies
echo "📌 Installing dependencies..."
pip install -r requirements.txt
echo "   ✅ Dependencies installed"

# Setup configuration
if [ ! -f ".env" ]; then
    echo "📌 Setting up environment configuration..."
    cp .env.example .env
    echo "   ✅ Created .env file"
    echo "   ⚠️  Please update .env with your settings"
fi

# Create necessary directories
echo "📌 Creating directories..."
mkdir -p logs
mkdir -p models_saved
mkdir -p cache
mkdir -p outputs
echo "   ✅ Directories created"

# Test imports
echo "📌 Testing Python imports..."
python -c "import pandas; import numpy; import torch; import streamlit; import mlflow; print('   ✅ All imports successful')"

echo ""
echo "=================================="
echo "✅ Setup completed successfully!"
echo ""
echo "🚀 Next steps:"
echo "   1. Run training: python train.py"
echo "   2. Launch dashboard: streamlit run dashboard/app.py"
echo "   3. View notebooks: jupyter notebook notebook/RetailPulse.ipynb"
echo ""

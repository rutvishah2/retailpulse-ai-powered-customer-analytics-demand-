#!/bin/bash
# RetailPulse - Run Training Pipeline

echo "🚀 RetailPulse - Training Pipeline"
echo "===================================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Please run: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
    exit 1
fi

# Set environment variables
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Run training pipeline
echo "📊 Starting training pipeline..."
echo ""

python train.py

echo ""
echo "===================================="
echo "✅ Training pipeline completed!"
echo ""
echo "📁 Output files saved to: outputs/"
echo "📊 View results in MLflow UI: mlflow ui"
echo "📈 Launch dashboard: streamlit run dashboard/app.py"
echo ""

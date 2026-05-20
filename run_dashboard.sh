#!/bin/bash
# RetailPulse - Run Dashboard

echo "📊 RetailPulse - Interactive Dashboard"
echo "======================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Please run: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
    exit 1
fi

# Set environment variables
export PYTHONUNBUFFERED=1

# Run Streamlit dashboard
echo "🚀 Launching Streamlit dashboard..."
echo ""
echo "📈 Dashboard URL: http://localhost:8501"
echo ""

streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0


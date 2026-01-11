#!/bin/bash
# Quick start script for Workspace module

set -e

echo "🚀 Workspace Module Quick Start"
echo "================================"
echo ""

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from backend/modules/workspace directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated"
    echo "   Attempting to activate..."
    if [ -f "../../../venv/bin/activate" ]; then
        source ../../../venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Error: Virtual environment not found"
        echo "   Please create one with: python3 -m venv venv"
        exit 1
    fi
fi

echo ""
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "🧪 Running tests..."
export PYTHONPATH=$PWD:$PYTHONPATH
pytest ../../tests/workspace/ -v --tb=no -q

echo ""
echo "📊 Test Summary:"
pytest ../../tests/workspace/ --co -q | tail -1

echo ""
echo "✅ Phase 1 Setup Complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Run migration: alembic upgrade head"
echo "   2. Start API: python main.py"
echo "   3. Test API: curl http://localhost:8000/health"
echo ""
echo "📚 Documentation:"
echo "   - PHASE1_FINAL.md - Final status report"
echo "   - docs/protocols.md - API protocols"
echo "   - implement.md - Implementation plan"
echo ""

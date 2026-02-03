#!/bin/bash
# Start script for Share-box bot

echo "🚀 Starting Share-box by Univora..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Python version
python --version

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Run bot
echo "✅ Starting bot..."
python bot.py

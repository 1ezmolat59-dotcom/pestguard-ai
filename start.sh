#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# PestGuard AI — Startup Script
# Usage: ./start.sh [port]
# ─────────────────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Optional port override: ./start.sh 9000
if [ -n "$1" ]; then
    export PORT="$1"
fi

# Load .env if present
if [ -f ".env" ]; then
    echo "📋 Loading .env configuration..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

PORT="${PORT:-8888}"

echo ""
echo "🌿 PestGuard AI — Starting up..."
echo "────────────────────────────────"

# Check Python
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi
PY=$(command -v python3 || command -v python)
echo "✅ Python: $($PY --version)"

# Check Tornado
$PY -c "import tornado" 2>/dev/null || {
    echo "❌ Tornado not installed. Run: pip install -r requirements.txt"
    exit 1
}
echo "✅ Tornado: $($PY -c 'import tornado; print(tornado.version)')"

# Check ReportLab
$PY -c "import reportlab" 2>/dev/null || {
    echo "⚠️  ReportLab not found — PDF reports disabled. Run: pip install reportlab"
}

# AI mode
if [ -n "$OPENAI_API_KEY" ]; then
    echo "🤖 AI Mode: OpenAI GPT-4o"
else
    echo "🔧 AI Mode: Demo (rule-based — no API key set)"
fi

echo ""
echo "🚀 Starting server at http://localhost:${PORT}"
echo "   Press Ctrl+C to stop"
echo ""

$PY app.py

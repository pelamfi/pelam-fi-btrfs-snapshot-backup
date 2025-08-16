#!/bin/bash
set -euo pipefail

# Create logs directory for build outputs
LOGS_DIR=".build"
mkdir -p "$LOGS_DIR"

echo "🔧 Setting up development environment..."

# Ensure uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install it first: https://github.com/astral-sh/uv"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
if ! uv sync --dev > "$LOGS_DIR/deps.log" 2>&1; then
    echo "❌ Failed to install dependencies. Check $LOGS_DIR/deps.log for details."
    exit 1
fi

echo "🎨 Running code formatting..."
if ! uv run ruff format src tests > "$LOGS_DIR/format.log" 2>&1; then
    echo "❌ Code formatting failed. Check $LOGS_DIR/format.log for details."
    exit 1
fi

echo "🔍 Running linting..."
if ! uv run ruff check src tests --fix > "$LOGS_DIR/lint.log" 2>&1; then
    echo "❌ Linting failed. Check $LOGS_DIR/lint.log for details."
    exit 1
fi

echo "🧪 Running tests..."
if ! uv run pytest tests/ -v --cov=src --cov-report=term-missing > "$LOGS_DIR/tests.log" 2>&1; then
    echo "❌ Tests failed. Check $LOGS_DIR/tests.log for details."
    exit 1
fi

echo "✅ All checks passed! (logs in $LOGS_DIR/)"

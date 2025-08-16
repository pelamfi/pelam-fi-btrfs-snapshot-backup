#!/bin/bash
set -euo pipefail

echo "🔧 Setting up development environment..."

# Ensure uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install it first: https://github.com/astral-sh/uv"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync --dev

echo "🎨 Running code formatting..."
uv run ruff format src tests

echo "🔍 Running linting..."
uv run ruff check src tests --fix

echo "🧪 Running tests..."
uv run pytest tests/ -v --cov=src --cov-report=term-missing

echo "✅ All checks passed!"

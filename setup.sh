#!/bin/bash
# Quick setup script for Compiler Explorer MCP Server

set -e

echo "🚀 Setting up Compiler Explorer MCP Server..."

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Make sure you're in the ce-mcp directory."
    exit 1
fi

echo "🔧 Creating virtual environment..."
uv venv

echo "📚 Installing dependencies..."
source .venv/bin/activate
uv pip install -e ".[dev]"

echo "🧪 Running tests to verify installation..."
pytest tests/ -m "not integration" --tb=short

echo "✅ Setup complete!"
echo ""
echo "To activate the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To start the MCP server:"
echo "  ce-mcp"
echo ""
echo "To run all tests:"
echo "  pytest tests/"
echo ""
echo "Happy coding! 🎉"
# Compiler Explorer MCP Server

A Model Context Protocol (MCP) server that provides efficient access to Compiler Explorer (godbolt.org) compilation and execution services.

## Features

- **Token-efficient responses** - Minimized output while preserving essential information
- **Use-case driven tools** - Specific functions for common compilation scenarios
- **Smart filtering** - Context-aware output filtering based on the task
- **Comprehensive language support** - C++, C, Rust, Go, Python, and more
- **Claude Code integration** - Automated setup for Claude Code workflows

## Quick Start (Claude Code Users)

If you're using Claude Code, simply run:

```bash
git clone https://github.com/compiler-explorer/ce-mcp
cd ce-mcp
./setup-claude-code.sh
```

This will automatically install and configure everything. That's it!

## Quick Setup

### Prerequisites

- **Python 3.10+** - Required for running the MCP server
- **UV** - Fast Python package manager (recommended)

### 1. Install UV (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or on macOS with Homebrew:
```bash
brew install uv
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/compiler-explorer/ce-mcp
cd ce-mcp

# Option A: Quick setup (Linux/macOS)
./setup.sh

# Option B: Manual setup
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### 3. Run Tests (Optional)

```bash
# Run unit tests
.venv/bin/pytest tests/ -m "not integration"

# Run integration tests (requires internet)
.venv/bin/pytest tests/ -m integration

# Run all tests
.venv/bin/pytest tests/
```

### 4. Start the MCP Server

```bash
# Basic usage
ce-mcp

# With custom configuration
ce-mcp --config ~/.config/ce-mcp/config.yaml

# With verbose logging
ce-mcp --verbose
```


## Available Tools

The server provides 12 specialized MCP tools for compilation, analysis, and sharing. See [`docs/available_tools.md`](docs/available_tools.md) for detailed documentation of each tool.

**Core Tools**:
- `compile_check_tool` - Syntax validation
- `compile_and_run_tool` - Compile and execute
- `compile_with_diagnostics_tool` - Error analysis

**Analysis Tools**:
- `analyze_optimization_tool` - Assembly optimization analysis
- `compare_compilers_tool` - Compiler comparison
- `lookup_instruction_tool` - Assembly instruction documentation

**Discovery & Sharing**:
- `generate_share_url_tool` - Create Compiler Explorer URLs
- `find_compilers_tool` - Find compilers with filtering
- `get_libraries_tool` - List available libraries
- `get_library_details_tool` - Library information
- `get_languages_tool` - List supported languages
- `download_shortlink_tool` - Download shared code

## Configuration

Create a configuration file at `~/.config/compiler_explorer_mcp/config.yaml`:

```yaml
compiler_explorer_mcp:
  api:
    endpoint: "https://godbolt.org/api"
    timeout: 30
    
  defaults:
    language: "c++"
    compiler: "g132"
    
  output_limits:
    max_stdout_lines: 100
    max_stderr_lines: 50
```

## Development

### Setting up for Development

```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Run tests
.venv/bin/pytest tests/

# Run integration tests (requires internet)
.venv/bin/pytest tests/ -m integration

# Format code
black .
isort .

# Type checking
mypy ce_mcp/

# Code quality checks
uv run black ce_mcp/ tests/
isort ce_mcp/ tests/
```

### Alternative: Traditional pip setup

If you prefer using pip instead of UV:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run the server
python -m ce_mcp.cli
```

## Troubleshooting

### Common Issues

**"command not found: ce-mcp"**
- Make sure your virtual environment is activated
- Try running directly: `python -m ce_mcp.cli`

**"ModuleNotFoundError: No module named 'packaging'"**
- Install missing dependency: `uv pip install packaging`
- Or reinstall with all dependencies: `uv pip install -e .`

**"ModuleNotFoundError: No module named 'ce_mcp'"**
- Install in development mode: `uv pip install -e .`
- Check your virtual environment is activated

**Integration tests failing**
- Tests require internet access to godbolt.org
- Some tests may be skipped if the API is temporarily unavailable
- Run unit tests only: `pytest tests/ -m "not integration"`

**"uv not found"**
- Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Or use pip: `pip install -e ".[dev]"`

### Configuration

Create `~/.config/ce-mcp/config.yaml` for custom settings:

```yaml
compiler_explorer_mcp:
  api:
    timeout: 30
  defaults:
    language: "c++"
    compiler: "g132"
  output_limits:
    max_stdout_lines: 50
```

## License

MIT
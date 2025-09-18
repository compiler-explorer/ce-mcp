# Compiler Explorer MCP Server

A Model Context Protocol (MCP) server that provides efficient access to Compiler Explorer (godbolt.org) compilation and execution services.

## Features

- **Token-efficient responses** - Minimized output while preserving essential information
- **Use-case driven tools** - Specific functions for common compilation scenarios
- **Smart filtering** - Context-aware output filtering based on the task
- **Comprehensive language support** - C++, C, Rust, Go, Python, and more
- **Extensive test coverage** - 48/49 tests passing (98% success rate)
- **Claude Code integration** - Automated setup for Claude Code workflows

## Implementation Status

**85% Complete** - See [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md) for detailed analysis.

✅ **Fully Working**: All 6 MCP tools implemented and functional  
⚠️ **Minor Issues**: Some tools need spec compliance fixes  
❌ **Missing**: Caching system (high priority)

## Quick Setup

### Prerequisites

- **Python 3.8+** - Required for running the MCP server
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

## MCP Client Integration

### Claude Desktop

To use this server with Claude Desktop, add it to your MCP configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "compiler-explorer": {
      "command": "ce-mcp",
      "args": ["--verbose"]
    }
  }
}
```

### Claude Code

Claude Code can use MCP servers installed in your project environment. Here's how to set it up:

#### 🚀 Automatic Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/compiler-explorer/ce-mcp
cd ce-mcp

# Run the automated Claude Code setup
./setup-claude-code.sh

# Or setup in a specific project directory
./setup-claude-code.sh --project-dir /path/to/your/project
```

The script will:
- ✅ Install the MCP server 
- ✅ Create `.claude.json` project configuration
- ✅ Configure `~/.claude/settings.json` for auto-approval
- ✅ Create `.ce-mcp-config.yaml` with your preferences
- ✅ Verify everything works
- ✅ Show you how to use the tools

#### Manual Setup

If you prefer manual setup:

**Option 1: Project Environment**
```bash
# Navigate to your C++/coding project
cd /path/to/your/project

# Install ce-mcp in project environment
uv pip install -e path/to/ce-mcp

# Or from PyPI (when published)
uv pip install ce-mcp
```

**Option 2: Global Installation**
```bash
# Install globally for use across all projects
pipx install ce-mcp

# Or with UV in a global environment
uv tool install ce-mcp
```

#### Configuration

Claude Code uses project-specific MCP configurations in `.claude.json`:

```json
{
  "mcp_servers": {
    "compiler-explorer": {
      "command": "/path/to/ce-mcp",
      "args": ["--config", "./.ce-mcp-config.yaml"]
    }
  }
}
```

And optionally, enable auto-approval in `~/.claude/settings.json`:

```json
{
  "enableAllProjectMcpServers": true
}
```

**Project-specific configuration** (`.ce-mcp-config.yaml`):
```yaml
compiler_explorer_mcp:
  defaults:
    language: "c++"
    compiler: "g132"
  output_limits:
    max_stdout_lines: 50
    max_stderr_lines: 25
```

📁 **Complete example configurations**: See [`examples/claude-code-config/`](examples/claude-code-config/) for ready-to-use configuration files.

#### Verification

Test that Claude Code can access the MCP server:

1. Open your project in Claude Code
2. Try using a tool like: `@compiler-explorer compile_check_tool`
3. The server should be automatically detected and available

#### Tips for Claude Code

- **Project-specific configs**: Use different compiler defaults per project
- **Language detection**: The server auto-detects language from file extensions
- **Argument extraction**: Add `// compile: -std=c++20 -O2` comments to source files
- **Efficient output**: The server provides token-optimized responses perfect for Claude Code

### Other MCP Clients

For other MCP-compatible clients, use the standard MCP server configuration format with the `ce-mcp` command.

## Available Tools

### compile_check
Quick compilation validation - checks if code compiles without verbose output.

### compile_and_run
Compile and run code, returning only execution results.

### compile_with_diagnostics
Get comprehensive compilation warnings and errors.

### analyze_optimization
Check compiler optimizations and assembly analysis.

### compare_compilers
Compare output across different compilers/options with detailed execution analysis and unified diff output.

### generate_share_url
Generate Compiler Explorer URLs for collaboration.

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

# Linting
flake8 ce_mcp/
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
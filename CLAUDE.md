# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

Compiler Explorer MCP server - provides an MCP interface to Compiler Explorer (godbolt.org) for code compilation, analysis, and comparison across multiple languages and compilers.

**Status**: 85% complete - See `IMPLEMENTATION_STATUS.md` for details.

## Development Commands

```bash
# Setup
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Tests
.venv/bin/pytest tests/                              # All tests
.venv/bin/pytest tests/ -m "not integration"        # Unit tests only
.venv/bin/pytest tests/ -m integration              # Integration tests

# Code quality
uv run black ce_mcp/ tests/               # Format
uv run ruff check --fix ce_mcp/ tests/    # Lint
uv run mypy ce_mcp/                       # Type check

# Run server
ce-mcp                                    # Basic
ce-mcp --config ./.ce-mcp-config.yaml    # With config
ce-mcp --verbose                          # Debug mode
```

## MCP Tools

1. **compile_check_tool** - Syntax validation
2. **compile_and_run_tool** - Compile and execute
3. **compile_with_diagnostics_tool** - Detailed error analysis
4. **analyze_optimization_tool** - Assembly optimization analysis
5. **compare_compilers_tool** - Compiler comparison
6. **generate_share_url_tool** - Create Compiler Explorer URLs

## Key Implementation Notes

- Extract compilation flags from source comments: `// flags: -O2 -Wall`
- Use structured JSON with Compiler Explorer API
- Support both compiler IDs (`g132`) and friendly names (`g++`)
- Configuration in YAML format
- Token-efficient responses for AI workflows

## Priority Tasks

1. **Implement caching system** - Missing core spec requirement
2. **Fix diagnostics parsing** - Line/column extraction issues
3. **Enhance compiler comparisons** - Better difference analysis

See `IMPLEMENTATION_STATUS.md` for complete status and `ADDITIONAL_TOOLS_PROPOSAL.md` for expansion ideas.

## Configuration

Default config location: `~/.config/compiler_explorer_mcp/config.yaml`

Key settings:
- API endpoint and timeout
- Default language/compiler
- Output filtering preferences
- Compiler name mappings

## Testing

- 49 total tests (48 passing)
- Unit tests with mocked API responses
- Integration tests with real Compiler Explorer API
- Focus on token efficiency and error handling
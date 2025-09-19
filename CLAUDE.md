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
uv run black ce_mcp/ tests/               # Format (120 char line length)
isort ce_mcp/ tests/                      # Sort imports
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
5. **compare_compilers_tool** - Enhanced compiler comparison with detailed execution analysis
6. **generate_share_url_tool** - Create Compiler Explorer URLs
7. **find_compilers_tool** - Find compilers with filtering by experimental features, runtime/compile tools support
8. **get_libraries_tool** - Get simplified list of available libraries with search
9. **get_library_details_tool** - Get detailed library information including versions
10. **get_languages_tool** - Get supported languages with id, name and extensions only
11. **download_shortlink_tool** - Download and save source code from Compiler Explorer shortlinks to local files

## Key Implementation Notes

- Extract compilation flags from source comments: `// flags: -O2 -Wall`
- Use structured JSON with Compiler Explorer API
- Support both compiler IDs (`g132`) and friendly names (`g++`)
- Configuration in YAML format
- Token-efficient responses for AI workflows
- Enhanced execution comparison with unified diff output for stdout/stderr
- Detailed compilation/execution status tracking across compilers
- Library discovery with token-efficient filtering (id/name for lists, full details on demand)
- Search capability across library names and IDs

See `IMPLEMENTATION_STATUS.md` for complete status and `ADDITIONAL_TOOLS_PROPOSAL.md` for expansion ideas.

## Configuration

Default config location: `~/.config/compiler_explorer_mcp/config.yaml`

Key settings:
- API endpoint and timeout
- Default language/compiler
- Output filtering preferences
- Compiler name mappings

### Development Configuration

**pyproject.toml** contains tool configurations:
- **Black**: 120 character line length, Python 3.10+ target
- **isort**: Black-compatible profile with 120 character line length
- **mypy**: Strict type checking with untyped definition warnings
- **pytest**: Async mode enabled, integration test markers

## Testing

- 56 total tests (all passing)
- Unit tests with mocked API responses
- Integration tests with real Compiler Explorer API
- Focus on token efficiency and error handling
- Comprehensive library tool testing

## GitHub Actions CI/CD

**.github/workflows/ci.yml** provides automated testing:
- **Triggers**: Push/PR to main branch only
- **test** job: Setup, formatting check, type checking, unit tests, integration tests, coverage
- **lint-and-format** job: Code formatting validation and import sorting check
- **UV package manager**: Fast dependency management with caching
- **Coverage reporting**: Codecov integration for test coverage tracking
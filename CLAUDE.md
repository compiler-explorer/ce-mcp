# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Compiler Explorer MCP (Model Context Protocol) server repository. The project provides an MCP interface to Compiler Explorer (godbolt.org) services, enabling AI assistants to efficiently compile, analyze, and compare code across multiple languages and compilers.

## Development Commands

Since this is currently in the specification phase, implementation commands will include:

```bash
# Development setup
uv pip install -e ".[dev]"

# Run tests (once implemented)
pytest tests/
pytest tests/test_specific.py::test_name  # Run single test

# Code quality (to be configured)
black .                    # Format code
isort .                   # Sort imports
flake8 .                  # Lint code
mypy .                    # Type checking
```

## Architecture

The MCP server follows a tool-based architecture with these core components:

### MCP Tools
1. **compile_check** - Fast syntax validation without execution
2. **compile_and_run** - Compile and execute with smart output filtering
3. **compile_with_diagnostics** - Detailed compilation analysis with warnings/errors
4. **analyze_optimization** - Assembly output analysis for optimization insights
5. **compare_compilers** - Side-by-side compiler comparison
6. **generate_share_url** - Create persistent Compiler Explorer URLs

### Design Principles
- **Token Efficiency**: Minimize output while maximizing usefulness
- **Smart Defaults**: Opinionated defaults that work for common cases
- **Use-Case Driven**: Each tool optimized for specific workflows
- **Flexible Filtering**: Granular control over compilation output

### Key Implementation Patterns
- Extract compilation arguments from source code comments (e.g., `// flags: -O2 -Wall`)
- Use structured JSON communication with Compiler Explorer API
- Implement comprehensive error handling with helpful messages
- Cache API responses to reduce redundant requests
- Support both explicit compiler IDs and user-friendly names

## Configuration

The server uses YAML configuration with hierarchical settings:
- API endpoint and authentication
- Caching behavior
- Default language/compiler preferences
- Output filter defaults
- Custom compiler aliases

Configuration file location: `~/.config/compiler_explorer_mcp/config.yaml`

## API Integration

Base API endpoint: `https://godbolt.org/api`

Key endpoints:
- `/compilers` - List available compilers
- `/compiler/{compiler_id}/compile` - Compile source code
- `/languages` - List supported languages
- `/shortlinkinfo/{link_id}` - Retrieve shared code

## Testing Strategy

When implementing tests:
- Unit test each MCP tool function
- Mock Compiler Explorer API responses for offline testing
- Integration tests with real API (use sparingly)
- Performance tests to ensure token efficiency
- Test error handling and edge cases

## Important Notes

- Always check `compiler-explorer-mcp-spec.md` for detailed implementation requirements
- Follow the existing Compiler Explorer API patterns for consistency
- Prioritize token efficiency in all output formatting decisions
- Support multi-file compilation scenarios when applicable
- Maintain backward compatibility with configuration changes
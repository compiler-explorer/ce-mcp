# Compiler Explorer MCP Implementation Specification

## Overview

Create a Model Context Protocol (MCP) server for Compiler Explorer that provides efficient, token-conscious access to compilation and execution services. This MCP should improve upon existing implementations by providing use-case specific tools with intelligent output filtering.

## Core Design Principles

1. **Token-efficient responses** - Minimize output while preserving essential information
2. **Use-case driven API** - Specific functions for common compilation scenarios  
3. **Smart filtering** - Context-aware output filtering based on the task
4. **Flexible but opinionated** - Provide sensible defaults with override capabilities
5. **Reuse existing patterns** - Build upon the proven approaches from the existing Python scripts

## Starting Point: Existing Best Practices

The implementation should incorporate these patterns from the existing `run-examples.py` script:

### 1. Compile Argument Extraction
```python
def extract_compile_args_from_source(source_code, language):
    """Extract compilation arguments from source code comments"""
    # Support for both C++ (//) and Pascal ({}) comment styles
    # Look for 'compile:' directive in first 10 lines
    # Return sensible defaults if not found
```

### 2. Structured API Communication
```python
# Use proper JSON payloads with all necessary options
payload = {
    "source": source_code,
    "options": {
        "userArguments": options,
        "executeParameters": {"args": [], "stdin": ""},
        "compilerOptions": {"executorRequest": True},
        "filters": { /* comprehensive filter set */ },
        "tools": [],
        "libraries": []
    }
}
```

### 3. ANSI Color Coding for Terminal Output
```python
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color
```

### 4. Comprehensive Error Handling
- Parse both compilation and execution results
- Handle API failures gracefully
- Provide meaningful error messages with context

## Proposed MCP Tools

### 1. `compile_check` - Quick compilation validation
**Purpose**: Check if code compiles without returning verbose output

**Parameters**:
- `source` (str): Source code to compile
- `language` (str): Programming language
- `compiler` (str): Compiler ID or name
- `options` (str, optional): Compiler flags
- `extract_args` (bool, default=True): Extract args from source comments

**Returns**:
```json
{
  "success": true/false,
  "exit_code": 0,
  "error_count": 0,
  "warning_count": 2,
  "first_error": "error: use of undeclared identifier 'foo' at line 10"
}
```

### 2. `compile_and_run` - Execute with filtered output
**Purpose**: Compile and run code, returning only execution results

**Parameters**:
- `source` (str): Source code
- `language` (str): Programming language  
- `compiler` (str): Compiler ID
- `options` (str, optional): Compiler flags
- `stdin` (str, optional): Standard input
- `args` (list, optional): Command line arguments
- `timeout` (int, default=5000): Execution timeout in ms

**Returns**:
```json
{
  "compiled": true,
  "executed": true,
  "exit_code": 0,
  "execution_time_ms": 42,
  "stdout": "Hello, World!\n",
  "stderr": "",
  "truncated": false
}
```

### 3. `compile_with_diagnostics` - Detailed compilation analysis
**Purpose**: Get comprehensive compilation warnings and errors

**Parameters**:
- `source` (str): Source code
- `language` (str): Programming language
- `compiler` (str): Compiler ID
- `options` (str, optional): Compiler flags
- `diagnostic_level` (str, default="normal"): "minimal", "normal", "verbose"

**Returns**:
```json
{
  "success": false,
  "diagnostics": [
    {
      "type": "error",
      "line": 15,
      "column": 8,
      "message": "use of undeclared identifier 'foo'",
      "suggestion": "did you mean 'bar'?"
    }
  ],
  "command": "g++ -std=c++17 -Wall example.cpp"
}
```

### 4. `analyze_optimization` - Assembly analysis for optimization
**Purpose**: Check compiler optimizations (based on `check-loop-optimization.py`)

**Parameters**:
- `source` (str): Source code
- `language` (str): Programming language
- `compiler` (str): Compiler ID
- `optimization_level` (str, default="-O3"): Optimization flags
- `analysis_type` (str, optional): "vectorization", "inlining", "loop", "all"

**Returns**:
```json
{
  "optimizations_detected": {
    "memcpy_conversion": true,
    "vectorization": true,
    "loop_unrolling": false,
    "function_inlining": true,
    "simd_instructions": ["movdqu", "movups"]
  },
  "summary": "Compiler optimized manual loop to memcpy call",
  "assembly_lines": 45
}
```

### 5. `compare_compilers` - Side-by-side comparison
**Purpose**: Compare output across different compilers/options

**Parameters**:
- `source` (str): Source code
- `language` (str): Programming language
- `compilers` (list): List of compiler configurations
- `comparison_type` (str): "execution", "assembly", "diagnostics"

**Returns**:
```json
{
  "results": [
    {
      "compiler": "gcc-13.2",
      "options": "-O3",
      "execution_result": "42",
      "assembly_size": 128,
      "warnings": 0
    },
    {
      "compiler": "clang-17",
      "options": "-O3", 
      "execution_result": "42",
      "assembly_size": 96,
      "warnings": 1
    }
  ],
  "differences": ["clang produces 25% smaller code", "clang warns about unused variable"]
}
```

### 6. `generate_share_url` - Create shareable links
**Purpose**: Generate Compiler Explorer URLs for collaboration (based on existing URL generation)

**Parameters**:
- `source` (str): Source code
- `language` (str): Programming language
- `compiler` (str): Compiler ID
- `options` (str, optional): Compiler flags
- `layout` (str, default="simple"): "simple", "comparison", "assembly"

**Returns**:
```json
{
  "url": "https://godbolt.org/z/abc123",
  "short_url": "https://godbolt.org/z/abc123",
  "configuration": {
    "compiler": "g132",
    "options": "-std=c++17 -O3"
  }
}
```

## API Communication Requirements

### User Agent
All API requests MUST include a custom User-Agent header to identify the MCP:
```python
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "CompilerExplorerMCP/1.0 (github.com/your-repo)"
}
```

### API Endpoints
- Base URL: `https://godbolt.org/api`
- Compilation: `POST /api/compiler/{compiler_id}/compile`
- Languages: `GET /api/languages`
- Compilers: `GET /api/compilers/{language}`

## Configuration

The MCP should support comprehensive configuration including ALL available Compiler Explorer filters:

```yaml
compiler_explorer_mcp:
  api:
    endpoint: "https://godbolt.org/api"
    timeout: 30
    retry_count: 3
    retry_backoff: 1.5
    
  cache:
    enabled: true
    directory: "~/.cache/compiler_explorer_mcp"
    ttl_seconds: 3600
    max_size_mb: 100
    
  defaults:
    language: "c++"
    compiler: "g132"
    extract_args_from_source: true
    
  filters:
    # ALL Compiler Explorer filters should be configurable
    binary: false
    binaryObject: false
    commentOnly: true
    demangle: true
    directives: true
    execute: false
    intel: true
    labels: true
    libraryCode: false
    trim: false
    # Additional filters from API
    debugCalls: false
    
  output_limits:
    max_stdout_lines: 100
    max_stderr_lines: 50
    max_assembly_lines: 500
    max_line_length: 200
    truncation_message: "... (truncated)"
    
  compiler_mappings:
    # User-friendly names to CE compiler IDs
    "g++": "g132"
    "gcc-latest": "g132"
    "clang++": "clang1700"
    "clang-latest": "clang1700"
    "fpc": "fpc322"
    "rustc": "r1740"
    "go": "gccgo132"
```

## Implementation Guidelines

### 1. Error Handling
```python
try:
    # API call
except urllib.error.HTTPError as e:
    if e.code == 429:
        # Rate limiting - implement exponential backoff
    elif e.code == 400:
        # Bad request - parse error details
except urllib.error.URLError as e:
    # Network error - retry with backoff
```

### 2. Output Processing
- Strip ANSI codes when not in terminal context
- Implement smart truncation that preserves error context
- Group similar errors/warnings

### 3. Caching Strategy
- Cache based on hash of (source, compiler, options)
- Respect cache headers from API
- Implement cache eviction based on LRU

### 4. Language Support
Initial support for:
- C++ (`.cpp`, `.cc`, `.cxx`)
- C (`.c`)
- Rust (`.rs`)
- Go (`.go`)
- Python (`.py`)
- Pascal/Delphi (`.pas`, `.dpr`)

### 5. Compiler Detection
```python
def detect_compiler(language, source=None):
    """Auto-detect appropriate compiler based on language and source"""
    # Check source for compiler hints
    # Fall back to sensible defaults
    # Allow user override
```

## Example Usage Patterns

### Quick Syntax Check
```python
result = compile_check(
    source=code,
    language="c++",
    compiler="g++"
)
# Returns: {"success": true, "warning_count": 1}
```

### Performance Comparison
```python
result = compare_compilers(
    source=code,
    language="c++",
    compilers=[
        {"id": "g++", "options": "-O3"},
        {"id": "clang++", "options": "-O3"}
    ],
    comparison_type="assembly"
)
```

### Teaching Optimization
```python
result = analyze_optimization(
    source=loop_code,
    language="c++",
    compiler="g++",
    analysis_type="loop"
)
# Returns: {"optimizations_detected": {"memcpy_conversion": true}}
```

## Testing Requirements

1. Unit tests for each tool function
2. Integration tests with real Compiler Explorer API
3. Mock tests for offline development
4. Performance tests for token efficiency
5. Examples from the existing codebase as test cases

## Installation and Distribution

```bash
pip install compiler-explorer-mcp

# Or for development
git clone https://github.com/yourusername/compiler-explorer-mcp
cd compiler-explorer-mcp
pip install -e .
```

## Success Metrics

1. **Token Efficiency**: 80% reduction in output tokens vs raw API
2. **Response Time**: <2s for compilation checks
3. **Cache Hit Rate**: >50% for typical usage patterns
4. **Error Clarity**: Structured errors that pinpoint issues
5. **Compatibility**: Works with all major CE compilers

## Future Enhancements

1. **Diff Analysis**: Compare code changes impact on assembly
2. **Benchmark Runner**: Performance testing with statistics
3. **Security Analysis**: Integration with static analyzers
4. **Multi-file Support**: Handle project-style compilations
5. **Custom Compiler Support**: User-defined compiler configurations

This specification provides a complete blueprint for implementing a powerful, efficient Compiler Explorer MCP that addresses current limitations while building upon proven patterns from existing tools.
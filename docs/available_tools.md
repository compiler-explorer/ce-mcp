# Available Tools

The Compiler Explorer MCP server provides 12 specialized tools for code compilation, analysis, and sharing. Each tool is optimized for specific use cases and provides token-efficient responses.

## Core Compilation Tools

### compile_check_tool
**Purpose**: Quick syntax and compilation validation
**Best for**: CI checks, code review, syntax validation

Validates code compilation without executing or returning verbose output. Perfect for fast feedback on whether code compiles successfully.

**Key Parameters**:
- `source` - Source code to validate
- `language` - Programming language (c++, c, rust, go, python, etc.)
- `compiler` - Compiler ID (g132, clang1600) or friendly name (g++, clang)
- `options` - Compiler flags (e.g., "-std=c++20 -O2")
- `extract_args` - Extract flags from source comments (default: true)

**Returns**: Success status, exit code, error/warning counts, first error message

### compile_and_run_tool
**Purpose**: Compile and execute code with program output
**Best for**: Testing algorithms, validating program behavior

Compiles source code and executes the resulting program, capturing stdout, stderr, and execution metrics.

**Key Parameters**:
- All compile_check_tool parameters plus:
- `stdin` - Input to provide to the program
- `args` - Command line arguments for the program
- `timeout` - Maximum execution time in milliseconds (default: 5000)

**Returns**: Compilation status, execution results, stdout/stderr, exit code, execution time

### compile_with_diagnostics_tool
**Purpose**: Detailed compilation error and warning analysis
**Best for**: Debugging compilation issues, code quality analysis

Provides comprehensive diagnostics including line numbers, error types, and compiler suggestions.

**Key Parameters**:
- All compile_check_tool parameters plus:
- `diagnostic_level` - "normal" (standard warnings) or "verbose" (comprehensive warnings)

**Returns**: Detailed diagnostic messages with line/column info, error types, compiler suggestions

## Analysis Tools

### analyze_optimization_tool
**Purpose**: Assembly-level optimization analysis
**Best for**: Performance investigation, understanding compiler optimizations

Examines generated assembly code to detect optimizations like vectorization, inlining, and loop transformations.

**Key Parameters**:
- All compile_check_tool parameters plus:
- `optimization_level` - Optimization flags (-O0, -O2, -O3, -Os, -Ofast)
- `analysis_type` - Focus area ("all", "vectorization", "inlining", "loops")
- `filter_out_library_code` - Hide standard library code (default: null)
- `do_demangle` - Convert C++ symbols to readable names (default: null)

**Returns**: Assembly output, instruction counts, optimization detection analysis, compiler optimization info (when supported)

### compare_compilers_tool
**Purpose**: Side-by-side compiler comparison
**Best for**: Evaluating compiler differences, optimization comparison

Compares compilation or execution results across different compilers with unified diff output for easy analysis.

**Key Parameters**:
- `source` - Source code to compare
- `language` - Programming language
- `compilers` - List of compiler configurations to compare
- `comparison_type` - "execution", "assembly", or "diagnostics"

**Returns**: Detailed comparison with unified diffs, execution status, performance metrics

## Sharing and Discovery Tools

### generate_share_url_tool
**Purpose**: Create shareable Compiler Explorer URLs
**Best for**: Collaboration, bug reports, educational examples

Generates URLs that link directly to Compiler Explorer with your code and settings pre-loaded.

**Key Parameters**:
- All compile_check_tool parameters plus:
- `layout` - Interface layout ("simple", "comparison", "assembly")

**Returns**: Shareable URL to Compiler Explorer

### find_compilers_tool
**Purpose**: Discover available compilers with advanced filtering
**Best for**: Finding experimental features, specific compiler versions

Searches for compilers with support for experimental features, proposals, or specific tools.

**Key Parameters**:
- `language` - Programming language (default: "c++")
- `proposal` - Specific proposal number (e.g., "P3385", "3385")
- `feature` - Experimental feature (e.g., "reflection", "concepts", "modules")
- `search_text` - Filter by compiler name/ID
- `exact_search` - Treat search_text as exact compiler ID match
- `include_overrides` - Include architecture override options
- `include_runtime_tools` - Include runtime tool information
- `include_compile_tools` - Include compile-time tool information

**Returns**: Filtered list of compilers with detailed capabilities

## Library Tools

### get_libraries_tool
**Purpose**: List available libraries with search capability
**Best for**: Discovering libraries, token-efficient library browsing

Returns a simplified list of libraries (ID and name only) with optional text search filtering.

**Key Parameters**:
- `language` - Programming language (default: "c++")
- `search_text` - Filter libraries by name/ID (optional)

**Returns**: List of libraries with ID and name fields only

### get_library_details_tool
**Purpose**: Detailed information for specific libraries
**Best for**: Understanding library versions, getting full library info

Provides comprehensive details for a specific library including all available versions.

**Key Parameters**:
- `language` - Programming language (default: "c++")
- `library_id` - Specific library ID to get details for

**Returns**: Complete library information including versions, description, URL

### get_languages_tool
**Purpose**: List supported programming languages with essential metadata
**Best for**: Language discovery, token-efficient language browsing, AI workflow optimization

Returns a simplified list of supported programming languages with only essential fields (id, name, extensions) and optional search filtering.

**Key Parameters**:
- `search_text` - Filter languages by name/ID (optional)

**Returns**: List of languages with id, name, and extensions fields only

### lookup_instruction_tool
**Purpose**: Get detailed documentation for assembly instructions/opcodes
**Best for**: Assembly analysis, understanding instruction behavior, debugging assembly code

Provides comprehensive documentation for assembly instructions across multiple architectures using Compiler Explorer's instruction documentation API.

**Key Parameters**:
- `instruction_set` - Architecture/instruction set name
  - x86/x86-64: "amd64", "x86", "x86_64", "x64", "intel"
  - ARM: "aarch64", "arm64", "armv8", "arm"
  - Others: "mips", "riscv", "powerpc" (if supported)
- `opcode` - Instruction/opcode to look up (e.g., "pop", "stp", "mov", "add")
- `format_output` - Format for readability (true) vs raw JSON (false)

**Returns**: Instruction documentation with syntax, operation details, flags affected, encoding, and formatted description

**Smart Features**:
- **Alias resolution**: Automatically maps common aliases (x64→amd64, arm64→aarch64)
- **Multi-architecture support**: x86, ARM64, and other instruction sets
- **Formatted output**: Clean, readable documentation optimized for AI workflows

## Additional Tools

### download_shortlink_tool
**Purpose**: Download and save source code from Compiler Explorer shortlinks
**Best for**: Code extraction, project integration, archiving shared examples

Extracts source code from Compiler Explorer shared links and saves to local files, preserving filenames and metadata.

**Key Parameters**:
- `shortlink_url` - CE shortlink URL or ID
- `destination_path` - Directory to save files
- `preserve_filenames` - Use original filenames when available (default: true)
- `include_metadata` - Save compilation settings as JSON (default: true)

**Returns**: List of saved files with metadata and summary

## Smart Features

### Argument Extraction
All compilation tools support extracting compiler flags from source code comments:
```cpp
// compile: -std=c++20 -O2 -Wall
// flags: -march=native
#include <iostream>
int main() { return 0; }
```

### Compiler Name Resolution
Tools accept both:
- **Compiler IDs**: `g132`, `clang1600`, `rustc1750`
- **Friendly names**: `g++`, `clang`, `rustc` (resolved to latest stable)

### Token Optimization
All tools provide responses optimized for AI workflows:
- Essential information only
- Structured JSON output
- Configurable output limits
- Context-aware filtering
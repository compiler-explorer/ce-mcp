"""Main MCP server implementation for Compiler Explorer."""

import json
import logging

from mcp.server import FastMCP

from .tools import (
    compile_check,
    compile_and_run,
    compile_with_diagnostics,
    analyze_optimization,
    compare_compilers,
    generate_share_url,
    find_experimental_compilers,
)
from .config import Config

logger = logging.getLogger(__name__)

# Global config instance
config = Config()

# Create FastMCP server
mcp = FastMCP("ce-mcp")


@mcp.tool()
async def compile_check_tool(
    source: str,
    language: str,
    compiler: str,
    options: str = "",
    extract_args: bool = True,
    libraries: list | None = None,
) -> str:
    """Quick compilation validation - checks if code compiles without verbose output.

    This tool provides fast syntax and compilation validation without executing code
    or returning detailed output. Perfect for CI checks, syntax validation, and
    quick error detection.

    **Use Cases:**
    - **Syntax validation**: Check if code compiles before detailed analysis
    - **CI pipeline checks**: Fast validation in automated builds
    - **Code review**: Quick verification that proposed changes compile
    - **Learning**: Test code snippets while learning new language features
    - **Bulk validation**: Check multiple code samples efficiently

    **Parameters:**
    - source: Source code to compile (minimal comments preferred)
    - language: Programming language (c++, c, rust, go, python, etc.)
    - compiler: Compiler identifier (e.g., "g132", "clang1600") or friendly name
    - options: Compiler flags (e.g., "-O2 -Wall", "-std=c++20")
    - extract_args: If True, extracts compiler flags from source comments like "// flags: -Wall"
    - libraries: List of libraries with format [{"id": "library_name", "version": "latest"}]

    **Returns JSON with:**
    - success: Boolean indicating if compilation succeeded
    - exit_code: Compiler exit code (0 = success)
    - error_count: Number of compilation errors found
    - warning_count: Number of warnings generated
    - first_error: Text of the first error encountered (if any)

    **Example Tool Calls:**

    Quick C++ syntax check:
    ```
    compile_check_tool({
        "source": "int main() { return 0; }",
        "language": "c++",
        "compiler": "g132"
    })
    ```

    Check with specific compiler flags:
    ```
    compile_check_tool({
        "source": "#include <iostream>\\nint main() { std::cout << \\"Hello\\"; }",
        "language": "c++",
        "compiler": "g132",
        "options": "-std=c++20 -Wall"
    })
    ```

    Use flags from source comments:
    ```
    compile_check_tool({
        "source": "// flags: -std=c++17 -O2\\nint main() { return 0; }",
        "language": "c++",
        "compiler": "clang1600",
        "extract_args": true
    })
    ```

    **When to use vs other tools:**
    - Use compile_check_tool for fast validation without execution
    - Use compile_and_run_tool when you need to see program output
    - Use compile_with_diagnostics_tool for detailed error analysis
    """
    result = await compile_check(
        {
            "source": source,
            "language": language,
            "compiler": compiler,
            "options": options,
            "extract_args": extract_args,
            "libraries": libraries,
        },
        config,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def compile_and_run_tool(
    source: str,
    language: str,
    compiler: str,
    options: str = "",
    stdin: str = "",
    args: list | None = None,
    timeout: int = 5000,
    libraries: list | None = None,
) -> str:
    """Compile and run code, returning execution results and program output.

    This tool compiles source code and executes the resulting program, capturing
    stdout, stderr, exit codes, and execution time. Perfect for testing algorithms,
    debugging programs, and validating program behavior.

    **Use Cases:**
    - **Testing programs**: Verify that code produces expected output
    - **Algorithm validation**: Test implementations with sample inputs
    - **Debugging**: See actual program behavior and error messages
    - **Performance measurement**: Check execution time for simple benchmarks
    - **Learning**: Run example code to understand language features
    - **Integration testing**: Test programs with different inputs and arguments

    **Parameters:**
    - source: Source code to compile and execute (minimal comments preferred)
    - language: Programming language (c++, c, rust, go, python, etc.)
    - compiler: Compiler identifier (e.g., "g132", "clang1600") or friendly name
    - options: Compiler flags (e.g., "-O2 -Wall", "-std=c++20")
    - stdin: Standard input to provide to the program during execution
    - args: Command line arguments passed to the program (list of strings)
    - timeout: Maximum execution time in milliseconds (default: 5000ms)
    - libraries: List of libraries with format [{"id": "library_name", "version": "latest"}]

    **Returns JSON with:**
    - compiled: Boolean indicating if compilation succeeded
    - executed: Boolean indicating if the program ran
    - exit_code: Program exit code (0 typically means success)
    - execution_time_ms: How long the program took to run
    - stdout: Program's standard output
    - stderr: Program's error output
    - truncated: Boolean indicating if output was truncated due to length

    **Example Tool Calls:**

    Simple program execution:
    ```
    compile_and_run_tool({
        "source": "#include <iostream>\\nint main() { std::cout << \\"Hello World\\"; return 0; }",
        "language": "c++",
        "compiler": "g132"
    })
    ```

    Program with command line arguments:
    ```
    compile_and_run_tool({
        "source": "#include <iostream>\\nint main(int argc, char* argv[]) { std::cout << argv[1]; }",
        "language": "c++",
        "compiler": "g132",
        "args": ["test_argument"]
    })
    ```

    Program with stdin input:
    ```
    compile_and_run_tool({
        "source": "#include <iostream>\\nint main() { int x; std::cin >> x; std::cout << x*2; }",
        "language": "c++",
        "compiler": "g132",
        "stdin": "42"
    })
    ```

    With timeout for long-running programs:
    ```
    compile_and_run_tool({
        "source": "while True: pass",
        "language": "python",
        "compiler": "python311",
        "timeout": 1000
    })
    ```

    **When to use vs other tools:**
    - Use compile_and_run_tool when you need to see program output
    - Use compile_check_tool for fast validation without execution
    - Use analyze_optimization_tool to examine generated assembly
    - Use compare_compilers_tool to compare execution across different compilers
    """
    if args is None:
        args = []
    result = await compile_and_run(
        {
            "source": source,
            "language": language,
            "compiler": compiler,
            "options": options,
            "stdin": stdin,
            "args": args,
            "timeout": timeout,
            "libraries": libraries,
        },
        config,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def compile_with_diagnostics_tool(
    source: str,
    language: str,
    compiler: str,
    options: str = "",
    diagnostic_level: str = "normal",
    libraries: list | None = None,
) -> str:
    """Get comprehensive compilation warnings and errors with detailed analysis.

    This tool provides detailed compilation diagnostics including warnings, errors,
    line numbers, and compiler suggestions. Perfect for code analysis, debugging
    compilation issues, and learning about compiler warnings.

    **Use Cases:**
    - **Code analysis**: Get detailed warnings and suggestions for code improvement
    - **Debugging compilation issues**: Understand why code fails to compile
    - **Learning**: See what compiler warnings teach about language best practices
    - **Code review**: Identify potential issues before code integration
    - **Static analysis**: Find potential bugs through compiler diagnostics
    - **Standard compliance**: Check code against language standards

    **Parameters:**
    - source: Source code to analyze for compilation issues (minimal comments preferred)
    - language: Programming language (c++, c, rust, go, etc.)
    - compiler: Compiler identifier (e.g., "g132", "clang1600") or friendly name
    - options: Additional compiler flags (e.g., "-std=c++20", "-march=native")
    - diagnostic_level: Controls verbosity of diagnostics:
      - "normal": Standard warnings with -Wall
      - "verbose": Comprehensive warnings with -Wall -Wextra -Wpedantic
    - libraries: List of libraries with format [{"id": "library_name", "version": "latest"}]

    **Returns JSON with:**
    - success: Boolean indicating if compilation succeeded
    - diagnostics: Array of diagnostic messages with details:
      - type: "error", "warning", "note", etc.
      - line: Line number where issue occurs
      - column: Column number (if available)
      - message: Human-readable diagnostic message
      - suggestion: Compiler suggestion for fixing the issue (if available)
    - command: The exact compiler command that was executed

    **Example Tool Calls:**

    Basic diagnostic analysis:
    ```
    compile_with_diagnostics_tool({
        "source": "int main() { int unused_var; return 0; }",
        "language": "c++",
        "compiler": "g132",
        "diagnostic_level": "normal"
    })
    ```

    Verbose diagnostics for thorough analysis:
    ```
    compile_with_diagnostics_tool({
        "source": "void func(int* p) { delete p; }\\nint main() { int x; func(&x); }",
        "language": "c++",
        "compiler": "clang1600",
        "diagnostic_level": "verbose"
    })
    ```

    Check modern C++ standard compliance:
    ```
    compile_with_diagnostics_tool({
        "source": "auto lambda = [=](auto x) { return x + 1; };",
        "language": "c++",
        "compiler": "g132",
        "options": "-std=c++14",
        "diagnostic_level": "verbose"
    })
    ```

    Analyze with specific warning flags:
    ```
    compile_with_diagnostics_tool({
        "source": "#include <cstdio>\\nint main() { printf(\\"Hello\\"); }",
        "language": "c++",
        "compiler": "g132",
        "options": "-Wformat-security -Wno-unused",
        "diagnostic_level": "normal"
    })
    ```

    **When to use vs other tools:**
    - Use compile_with_diagnostics_tool for detailed error analysis and code quality
    - Use compile_check_tool for quick pass/fail validation
    - Use compile_and_run_tool when you need to see program execution
    - Use analyze_optimization_tool to examine generated assembly
    """
    result = await compile_with_diagnostics(
        {
            "source": source,
            "language": language,
            "compiler": compiler,
            "options": options,
            "diagnostic_level": diagnostic_level,
            "libraries": libraries,
        },
        config,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def analyze_optimization_tool(
    source: str,
    language: str,
    compiler: str,
    optimization_level: str = "-O3",
    analysis_type: str = "all",
    filter_out_library_code: bool | None = None,
    filter_out_debug_calls: bool | None = None,
    do_demangle: bool | None = None,
    libraries: list | None = None,
) -> str:
    """Analyze compiler optimizations and generated assembly code.

    This tool examines how compilers optimize code by analyzing the generated assembly.
    It detects vectorization, inlining, loop optimizations, SIMD usage, and other
    compiler transformations. Perfect for performance analysis and understanding
    how different code patterns affect optimization.

    **Use Cases:**
    - **Performance investigation**: Understand why code is fast or slow
    - **Optimization validation**: Verify that compilers apply expected optimizations
    - **Learning**: See how different coding patterns affect compiler behavior
    - **Code review**: Check if performance-critical code optimizes well
    - **Benchmarking**: Compare optimization effectiveness across compilers
    - **Algorithm analysis**: See how different implementations optimize

    **Parameters:**
    - source: Source code to analyze for optimizations (minimal comments preferred)
    - language: Programming language (c++, c, rust, go, etc.)
    - compiler: Compiler identifier (e.g., "g132", "clang1600") or friendly name
    - optimization_level: Optimization flags (e.g., "-O0", "-O2", "-O3", "-Os", "-Ofast")
    - analysis_type: Focus of analysis ("all", "vectorization", "inlining", "loops")
    - filter_out_library_code: Hide standard library implementations for cleaner output
    - filter_out_debug_calls: Hide debug and profiling function calls
    - do_demangle: Convert mangled C++ symbols to readable names
    - libraries: List of libraries with format [{"id": "library_name", "version": "latest"}]

    **Returns JSON with:**
    - optimizations_detected: Object with detected optimization types:
      - memcpy_conversion: Boolean - compiler replaced loops with memcpy
      - vectorization: Boolean - SIMD/vector instructions generated
      - loop_unrolling: Boolean - loops were unrolled for performance
      - function_inlining: Boolean - function calls were inlined
      - simd_instructions: Array of SIMD instruction names found
    - summary: Human-readable description of key optimizations
    - assembly_lines: Number of assembly lines generated
    - full_assembly: Complete assembly output (filtered based on settings)
    - truncated: Boolean indicating if assembly output was truncated

    **Example Tool Calls:**

    Basic optimization analysis:
    ```
    analyze_optimization_tool({
        "source": "void copy_array(int* dst, int* src, int n) { for(int i=0; i<n; i++) dst[i] = src[i]; }",
        "language": "c++",
        "compiler": "g132",
        "optimization_level": "-O3"
    })
    ```

    Focus on vectorization detection:
    ```
    analyze_optimization_tool({
        "source": "float dot_product(float* a, float* b, int n) { float sum=0; for(int i=0; i<n; i++) sum += a[i]*b[i]; return sum; }",
        "language": "c++",
        "compiler": "clang1600",
        "optimization_level": "-O3 -march=native",
        "analysis_type": "vectorization"
    })
    ```

    Compare optimization levels:
    ```
    analyze_optimization_tool({
        "source": "int factorial(int n) { return n <= 1 ? 1 : n * factorial(n-1); }",
        "language": "c++",
        "compiler": "g132",
        "optimization_level": "-O0"
    })
    ```

    Clean assembly output for analysis:
    ```
    analyze_optimization_tool({
        "source": "template<int N> int power(int x) { return x * power<N-1>(x); }",
        "language": "c++",
        "compiler": "g132",
        "optimization_level": "-O2",
        "filter_out_library_code": true,
        "do_demangle": true
    })
    ```

    **When to use vs other tools:**
    - Use analyze_optimization_tool to understand compiler optimizations and assembly
    - Use compile_and_run_tool to test program behavior and performance
    - Use compare_compilers_tool to compare optimization across different compilers
    - Use compile_with_diagnostics_tool for code quality and warning analysis
    """
    result = await analyze_optimization(
        {
            "source": source,
            "language": language,
            "compiler": compiler,
            "optimization_level": optimization_level,
            "analysis_type": analysis_type,
            "filter_out_library_code": filter_out_library_code,
            "filter_out_debug_calls": filter_out_debug_calls,
            "do_demangle": do_demangle,
            "libraries": libraries,
        },
        config,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def compare_compilers_tool(
    source: str,
    language: str,
    compilers: list,
    comparison_type: str,
    libraries: list | None = None,
) -> str:
    """Compare output across different compilers/options.

    Args:
        source: Source code to compile
        language: Programming language (e.g., 'c++', 'rust')
        compilers: List of compiler configurations
        comparison_type: Type of comparison (execution, assembly, diagnostics)
        libraries: List of libraries with format [{"id": "library_name", "version": "latest"}]
    """
    result = await compare_compilers(
        {
            "source": source,
            "language": language,
            "compilers": compilers,
            "comparison_type": comparison_type,
            "libraries": libraries,
        },
        config,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def generate_share_url_tool(
    source: str,
    language: str,
    compiler: str,
    options: str = "",
    layout: str = "simple",
    libraries: list | None = None,
) -> str:
    """Generate shareable Compiler Explorer URLs for collaboration and demonstration.

    This tool creates URLs that link directly to Compiler Explorer with your code,
    compiler settings, and configuration pre-loaded. Perfect for sharing examples,
    demonstrating issues, collaborating on code, and creating educational content.

    **Use Cases:**
    - **Bug reports**: Share minimal reproducible examples with exact compiler settings
    - **Code collaboration**: Send colleagues links to specific compiler configurations
    - **Education**: Create examples for teaching compiler behavior or language features
    - **Documentation**: Include live, interactive code examples in documentation
    - **Performance discussions**: Share assembly output for performance analysis
    - **Standard compliance**: Demonstrate how code behaves across different compiler versions

    **Parameters:**
    - source: Source code to include in the shareable URL (minimal comments preferred)
    - language: Programming language (c++, c, rust, go, python, etc.)
    - compiler: Compiler identifier (e.g., "g132", "clang1600") or friendly name
    - options: Compiler flags (e.g., "-O2 -Wall", "-std=c++20 -march=native")
    - layout: Controls the Compiler Explorer interface layout:
      - "simple": Clean, minimal interface
      - "comparison": Side-by-side compiler comparison view
      - "assembly": Focus on assembly output view
    - libraries: List of libraries with format [{"id": "library_name", "version": "latest"}]

    **Returns JSON with:**
    - url: Full Compiler Explorer URL with all settings
    - short_url: Shortened URL for easier sharing
    - configuration: Summary of the settings included in the URL:
      - compiler: The compiler that will be used
      - options: Compiler flags that will be applied
      - layout: Interface layout that will be shown

    **Example Tool Calls:**

    Simple code sharing:
    ```
    generate_share_url_tool({
        "source": "#include <iostream>\\nint main() { std::cout << \\"Hello World\\"; return 0; }",
        "language": "c++",
        "compiler": "g132",
        "options": "-std=c++20"
    })
    ```

    Bug report with optimization flags:
    ```
    generate_share_url_tool({
        "source": "volatile int x = 0;\\nint main() { return x++; }",
        "language": "c++",
        "compiler": "clang1600",
        "options": "-O3 -ffast-math",
        "layout": "assembly"
    })
    ```

    Educational example with comparison view:
    ```
    generate_share_url_tool({
        "source": "auto lambda = [](auto x) { return x + 1; };",
        "language": "c++",
        "compiler": "g132",
        "options": "-std=c++14",
        "layout": "comparison"
    })
    ```

    Example with libraries:
    ```
    generate_share_url_tool({
        "source": "#include <fmt/core.h>\\nint main() { fmt::print(\\"Hello\\"); }",
        "language": "c++",
        "compiler": "g132",
        "options": "-std=c++17",
        "libraries": [{"id": "fmt", "version": "latest"}]
    })
    ```

    **When to use vs other tools:**
    - Use generate_share_url_tool to create shareable links for collaboration
    - Use compile_and_run_tool to test and validate code behavior first
    - Use analyze_optimization_tool to understand assembly before sharing
    - Use compare_compilers_tool to compare multiple configurations before sharing
    """
    result = await generate_share_url(
        {
            "source": source,
            "language": language,
            "compiler": compiler,
            "options": options,
            "layout": layout,
            "libraries": libraries,
        },
        config,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def find_experimental_compilers_tool(
    language: str = "c++",
    proposal: str | None = None,
    feature: str | None = None,
    category: str | None = None,
    show_all: bool = False,
) -> str:
    """Find experimental compilers supporting specific proposals or features.

    Args:
        language: Programming language (default: c++)
        proposal: Specific proposal number to search for (e.g., 'P3385', '3385')
        feature: Experimental feature to search for (e.g., 'reflection', 'concepts', 'modules')
        category: Category to filter by (e.g., 'proposals', 'reflection', 'concepts')
        show_all: Show all experimental compilers organized by category

    Examples:
        - Find P3385 compilers: proposal="P3385"
        - Find reflection compilers: feature="reflection"
        - Find all proposal compilers: category="proposals"
        - Show all experimental compilers: show_all=True
    """
    result = await find_experimental_compilers(
        {
            "language": language,
            "proposal": proposal,
            "feature": feature,
            "category": category,
            "show_all": show_all,
        },
        config,
    )
    return json.dumps(result, indent=2)


def create_server(server_config: Config | None = None) -> FastMCP:
    """Create and configure the MCP server."""
    global config
    if server_config:
        config = server_config
    return mcp

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

    Args:
        source: Source code to compile
        language: Programming language (e.g., 'c++', 'rust')
        compiler: Compiler identifier or name
        options: Compiler options (e.g., '-O2 -Wall')
        extract_args: Extract compiler arguments from source comments
        libraries: List of libraries with format [{"id": "library_name", "version": "latest"}]
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
    """Compile and run code, returning only execution results.

    Args:
        source: Source code to compile and run
        language: Programming language (e.g., 'c++', 'rust')
        compiler: Compiler identifier or name
        options: Compiler options (e.g., '-O2 -Wall')
        stdin: Input to provide to the program
        args: Command line arguments for the program
        timeout: Execution timeout in milliseconds
        libraries: List of libraries with format [{"id": "library_name", "version": "latest"}]
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
    """Get comprehensive compilation warnings and errors.

    Args:
        source: Source code to compile
        language: Programming language (e.g., 'c++', 'rust')
        compiler: Compiler identifier or name
        options: Compiler options (e.g., '-O2 -Wall')
        diagnostic_level: Level of diagnostics (normal, verbose)
        libraries: List of libraries with format [{"id": "library_name", "version": "latest"}]
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
    """Check compiler optimizations and assembly analysis.

    Args:
        source: Source code to analyze
        language: Programming language (c++, c, rust, etc.)
        compiler: Compiler to use (g++, clang++, etc.)
        optimization_level: Optimization flags (default: -O3)
        analysis_type: Type of analysis to perform
        filter_out_library_code: Hide standard library implementations (default: config setting)
        filter_out_debug_calls: Hide debug/profiling calls (default: config setting)
        do_demangle: Demangle C++ symbols for readability (default: config setting)
        libraries: List of libraries with format [{"id": "library_name", "version": "latest"}]
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
    """Generate Compiler Explorer URLs for collaboration.

    Args:
        source: Source code to include in URL
        language: Programming language (e.g., 'c++', 'rust')
        compiler: Compiler identifier or name
        options: Compiler options (e.g., '-O2 -Wall')
        layout: Layout type for the URL
        libraries: List of libraries with format [{"id": "library_name", "version": "latest"}]
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


def create_server(server_config: Config | None = None) -> FastMCP:
    """Create and configure the MCP server."""
    global config
    if server_config:
        config = server_config
    return mcp

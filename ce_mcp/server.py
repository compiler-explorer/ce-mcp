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
) -> str:
    """Quick compilation validation - checks if code compiles without verbose output."""
    result = await compile_check(
        {
            "source": source,
            "language": language,
            "compiler": compiler,
            "options": options,
            "extract_args": extract_args,
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
    args: list = None,
    timeout: int = 5000,
) -> str:
    """Compile and run code, returning only execution results."""
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
) -> str:
    """Get comprehensive compilation warnings and errors."""
    result = await compile_with_diagnostics(
        {
            "source": source,
            "language": language,
            "compiler": compiler,
            "options": options,
            "diagnostic_level": diagnostic_level,
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
    filter_out_library_code: bool = None,
    filter_out_debug_calls: bool = None,
    do_demangle: bool = None,
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
) -> str:
    """Compare output across different compilers/options."""
    result = await compare_compilers(
        {
            "source": source,
            "language": language,
            "compilers": compilers,
            "comparison_type": comparison_type,
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
) -> str:
    """Generate Compiler Explorer URLs for collaboration."""
    result = await generate_share_url(
        {
            "source": source,
            "language": language,
            "compiler": compiler,
            "options": options,
            "layout": layout,
        },
        config,
    )
    return json.dumps(result, indent=2)


def create_server(server_config: Config = None) -> FastMCP:
    """Create and configure the MCP server."""
    global config
    if server_config:
        config = server_config
    return mcp

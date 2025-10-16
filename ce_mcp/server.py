"""Main MCP server implementation for Compiler Explorer."""

import json
import logging

from mcp.server import FastMCP

from .config import Config
from .tools import (
    analyze_optimization,
    compare_compilers,
    compile_and_run,
    compile_check,
    compile_with_diagnostics,
    download_shortlink,
    find_compilers,
    generate_share_url,
    get_languages_list,
    get_libraries_list,
    get_library_details_info,
    lookup_instruction,
)

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
    create_binary: bool = False,
    create_object_only: bool = False,
) -> str:
    """Check if code compiles without executing it.

    Args:
        source: Source code to compile
        language: Programming language (c++, c, rust, go, python, etc.)
        compiler: Compiler ID (e.g., "g132", "clang1600") or friendly name
        options: Compiler flags (e.g., "-O2 -Wall", "-std=c++20")
        extract_args: Extract flags from source comments like "// flags: -Wall"
        libraries: Libraries list [{"id": "name", "version": "latest"}]
        create_binary: Create full executable binary
        create_object_only: Create object file without linking

    Returns: {success, exit_code, error_count, warning_count, first_error}
    """
    result = await compile_check(
        {
            "source": source,
            "language": language,
            "compiler": compiler,
            "options": options,
            "extract_args": extract_args,
            "libraries": libraries,
            "create_binary": create_binary,
            "create_object_only": create_object_only,
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
    tools: list | None = None,
    create_binary: bool = False,
    create_object_only: bool = False,
) -> str:
    """Compile and execute code, capturing output and execution results.

    Args:
        source: Source code to compile and run
        language: Programming language (c++, c, rust, go, python, etc.)
        compiler: Compiler ID (e.g., "g132", "clang1600") or friendly name
        options: Compiler flags (e.g., "-O2 -Wall", "-std=c++20")
        stdin: Standard input for the program
        args: Command line arguments (list of strings)
        timeout: Max execution time in ms (default: 5000)
        libraries: Libraries list [{"id": "name", "version": "latest"}]
        tools: Additional tools to run [{"id": "tool_name", "args": []}]
        create_binary: Create full executable binary
        create_object_only: Create object file without linking

    Returns: {compiled, executed, exit_code, execution_time_ms, stdout, stderr, truncated}
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
            "tools": tools,
            "create_binary": create_binary,
            "create_object_only": create_object_only,
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
    tools: list | None = None,
    create_binary: bool = False,
    create_object_only: bool = False,
) -> str:
    """Get detailed compilation warnings and errors with line numbers.

    Args:
        source: Source code to analyze
        language: Programming language (c++, c, rust, go, etc.)
        compiler: Compiler ID (e.g., "g132", "clang1600") or friendly name
        options: Additional compiler flags (e.g., "-std=c++20")
        diagnostic_level: "normal" (-Wall) or "verbose" (-Wall -Wextra -Wpedantic)
        libraries: Libraries list [{"id": "name", "version": "latest"}]
        tools: Additional tools [{"id": "tool_name", "args": []}]
        create_binary: Create full executable binary
        create_object_only: Create object file without linking

    Returns: {success, diagnostics: [{type, line, column, message, suggestion}], command}
    """
    result = await compile_with_diagnostics(
        {
            "source": source,
            "language": language,
            "compiler": compiler,
            "options": options,
            "diagnostic_level": diagnostic_level,
            "libraries": libraries,
            "tools": tools,
            "create_binary": create_binary,
            "create_object_only": create_object_only,
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
    include_optimization_remarks: bool = True,
    filter_out_library_code: bool | None = None,
    filter_out_debug_calls: bool | None = None,
    do_demangle: bool | None = None,
    libraries: list | None = None,
) -> str:
    """Analyze generated assembly code to understand compiler optimizations.

    Args:
        source: Source code to analyze
        language: Programming language (c++, c, rust, go, etc.)
        compiler: Compiler ID (e.g., "g132", "clang1600") or friendly name
        optimization_level: Optimization flags ("-O0", "-O2", "-O3", "-Os", "-Ofast")
        analysis_type: Focus area ("all", "vectorization", "inlining", "loops")
        include_optimization_remarks: Include compiler optimization passes
        filter_out_library_code: Hide standard library implementations
        filter_out_debug_calls: Hide debug/profiling function calls
        do_demangle: Convert mangled C++ symbols to readable names
        libraries: Libraries list [{"id": "name", "version": "latest"}]

    Returns: {assembly_lines, instruction_count, assembly_output, truncated, total_instructions, optimization_remarks}
    """
    result = await analyze_optimization(
        {
            "source": source,
            "language": language,
            "compiler": compiler,
            "optimization_level": optimization_level,
            "analysis_type": analysis_type,
            "include_optimization_remarks": include_optimization_remarks,
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
    """Compare compilation/execution results across multiple compilers.

    Args:
        source: Source code to compile
        language: Programming language (c++, rust, etc.)
        compilers: List of compiler configurations [{"compiler": "id", "options": "flags"}]
        comparison_type: "execution", "assembly", or "diagnostics"
        libraries: Libraries list [{"id": "name", "version": "latest"}]

    Returns: Comparison results based on type (diffs for execution, side-by-side for assembly)
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
    tools: list | None = None,
    create_binary: bool = False,
    create_object_only: bool = False,
) -> str:
    """Generate shareable Compiler Explorer URL with code and settings.

    Args:
        source: Source code to include
        language: Programming language (c++, c, rust, go, python, etc.)
        compiler: Compiler ID (e.g., "g132", "clang1600") or friendly name
        options: Compiler flags (e.g., "-O2 -Wall", "-std=c++20")
        layout: UI layout ("simple", "comparison", "assembly")
        libraries: Libraries list [{"id": "name", "version": "latest"}]
        tools: Tools list [{"id": "tool_name", "args": []}]
        create_binary: Create full executable binary
        create_object_only: Create object file without linking

    Returns: {url: shareable Compiler Explorer URL}
    """
    result = await generate_share_url(
        {
            "source": source,
            "language": language,
            "compiler": compiler,
            "options": options,
            "layout": layout,
            "libraries": libraries,
            "tools": tools,
            "create_binary": create_binary,
            "create_object_only": create_object_only,
        },
        config,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def find_compilers_tool(
    language: str = "c++",
    proposal: str | None = None,
    feature: str | None = None,
    category: str | None = None,
    show_all: bool = False,
    search_text: str | None = None,
    exact_search: bool = False,
    ids_only: bool = False,
    include_overrides: bool = False,
    include_runtime_tools: bool = False,
    include_compile_tools: bool = False,
) -> str:
    """Find compilers with optional filtering by experimental features, proposals, or tools.

    ⚠️  AVOID generic searches like 'gcc' or 'clang' - they exceed token limits (25k+).
    Use specific terms: 'gcc 13', 'x86-64 gcc', or exact compiler IDs with exact_search=True.

    Args:
        language: Programming language (default: c++)
        proposal: Specific proposal number to search for (e.g., 'P3385', '3385')
        feature: Experimental feature to search for (e.g., 'reflection', 'concepts', 'modules')
        category: Category to filter by (e.g., 'proposals', 'reflection', 'concepts')
        show_all: Show all experimental compilers organized by category
        search_text: Filter compilers by text search in compiler names and IDs (should be compiler-related keywords like "gcc 13", "clang17", "msvc", "nightly")
        exact_search: If True, search_text is treated as an exact compiler ID match (case-sensitive)
        ids_only: Return only compiler IDs (use sparingly, only when search_text isn't sufficient)
        include_overrides: Include possibleOverrides field for architecture discovery (increases output significantly)
        include_runtime_tools: Include possibleRuntimeTools field for runtime tool discovery (increases output significantly)
        include_compile_tools: Include tools field for compile-time tool discovery (increases output significantly; requires specific compiler ID in search_text)

    Examples:
        - Find all C++ compilers: language="c++"
        - Find GCC 13 compilers: search_text="gcc 13"
        - Find MSVC compilers: search_text="msvc"
        - Find P3385 proposal compilers: proposal="P3385"
        - Find reflection feature compilers: feature="reflection"
        - Find nightly/experimental compilers: search_text="nightly"
        - Get only compiler IDs for MSVC (if needed): search_text="msvc", ids_only=True
        - Get GCC with architecture overrides: search_text="gcc", include_overrides=True
        - Get clang 17 with runtime tools: search_text="clang1701", include_runtime_tools=True
        - Get GCC 13.2 with compile tools: search_text="g132", include_compile_tools=True
        - Find exact compiler by ID: search_text="clang1600", exact_search=True
    """
    # Validate search_text to prevent overly broad searches that exceed token limits
    if search_text and not exact_search:
        forbidden_terms = ["gcc", "clang", "g++", "clang++"]
        search_lower = search_text.lower().strip()
        if search_lower in forbidden_terms:
            return json.dumps(
                {
                    "error": f"Search term '{search_text}' is too broad and would exceed token limits (25k+). Please be more specific:",
                    "suggestions": [
                        f"Use specific versions: '{search_text} 13', '{search_text} 14', '{search_text} 17'",
                        f"Use architecture prefix: 'x86-64 {search_text}', 'arm64 {search_text}'",
                        f"Use exact compiler ID with exact_search=True: '{search_text}132', '{search_text}1600'",
                    ],
                    "valid_examples": ["gcc 13", "clang 17", "msvc", "nightly", "g132", "clang1600"],
                },
                indent=2,
            )

    result = await find_compilers(
        {
            "language": language,
            "proposal": proposal,
            "feature": feature,
            "category": category,
            "show_all": show_all,
            "search_text": search_text,
            "exact_search": exact_search,
            "ids_only": ids_only,
            "include_overrides": include_overrides,
            "include_runtime_tools": include_runtime_tools,
            "include_compile_tools": include_compile_tools,
        },
        config,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_libraries_tool(
    language: str = "c++",
    search_text: str | None = None,
) -> str:
    """Get simplified list of libraries (id and name only) with optional search.

    Args:
        language: Programming language (default: c++)
        search_text: Filter libraries by text search in names and IDs (optional)

    Examples:
        - Get all C++ libraries: language="c++"
        - Search for boost libraries: language="c++", search_text="boost"
        - Search for format libraries: language="c++", search_text="fmt"
        - Get Rust libraries: language="rust"
    """
    result = await get_libraries_list(
        {
            "language": language,
            "search_text": search_text,
        },
        config,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_library_details_tool(
    language: str = "c++",
    library_id: str = "",
) -> str:
    """Get detailed information for a specific library including versions.

    Args:
        language: Programming language (default: c++)
        library_id: The ID of the library to get details for (required)

    Examples:
        - Get boost details: language="c++", library_id="boost"
        - Get fmt details: language="c++", library_id="fmt"
        - Get range-v3 details: language="c++", library_id="range-v3"
        - Get Rust crate details: language="rust", library_id="serde"
    """
    result = await get_library_details_info(
        {
            "language": language,
            "library_id": library_id,
        },
        config,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_languages_tool(
    search_text: str | None = None,
) -> str:
    """Get simplified list of languages (id, name and extensions only) with optional search.

    Args:
        search_text: Filter languages by text search in names and IDs (optional)

    Examples:
        - Get all languages: (no arguments)
        - Search for C languages: search_text="c"
        - Search for JavaScript/TypeScript: search_text="script"
        - Search for Python: search_text="python"
    """
    result = await get_languages_list(
        {
            "search_text": search_text,
        },
        config,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def lookup_instruction_tool(
    instruction_set: str,
    opcode: str,
    format_output: bool = True,
) -> str:
    """Get documentation for assembly instructions/opcodes.

    Args:
        instruction_set: Architecture ("amd64"/"x86_64", "aarch64"/"arm64", "mips", "riscv")
        opcode: Instruction to look up (e.g., "pop", "stp", "mov", "add")
        format_output: Format for readability (true) vs raw JSON (false)

    Returns: {found, instruction_set, opcode, documentation, formatted_docs, error}

    Supports alias resolution (x64→amd64, arm64→aarch64) and case-insensitive lookups.
    """
    result = await lookup_instruction(
        {
            "instruction_set": instruction_set,
            "opcode": opcode,
            "format_output": format_output,
        },
        config,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
async def download_shortlink_tool(
    shortlink_url: str,
    destination_path: str,
    preserve_filenames: bool = True,
    fallback_prefix: str = "ce",
    include_metadata: bool = True,
    overwrite_existing: bool = False,
) -> str:
    """Download source code from Compiler Explorer shortlink to local files.

    Args:
        shortlink_url: Full CE URL or just ID (e.g., "G38YP7eW4")
        destination_path: Directory where files should be saved
        preserve_filenames: Use original CE filenames (default: True)
        fallback_prefix: Prefix for generated filenames (default: "ce")
        include_metadata: Save compilation settings as JSON (default: True)
        overwrite_existing: Overwrite existing files (default: False)

    Returns: {saved_files, metadata_file, summary, error}

    Preserves original filenames, handles multi-file projects, saves compiler configs.
    """
    result = await download_shortlink(
        {
            "shortlink_url": shortlink_url,
            "destination_path": destination_path,
            "preserve_filenames": preserve_filenames,
            "fallback_prefix": fallback_prefix,
            "include_metadata": include_metadata,
            "overwrite_existing": overwrite_existing,
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

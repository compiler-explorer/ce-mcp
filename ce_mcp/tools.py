"""Tool implementations for Compiler Explorer MCP."""

from typing import Any, Dict

from .config import Config
from .api_client import CompilerExplorerClient
from .utils import extract_compile_args_from_source
from .experimental_utils import (
    search_experimental_compilers,
    ExperimentalCompilerFinder,
)


def _collect_all_stderr(result: Dict[str, Any]) -> str:
    """
    Collect stderr messages from all possible locations in API response.

    Combines stderr from:
    1. buildResult.stderr (detailed compilation errors)
    2. top-level result.stderr (high-level messages)
    3. buildsteps[].stderr (build step errors)
    4. execResult.stderr (execution errors)

    Args:
        result: Full API response from Compiler Explorer

    Returns:
        Combined stderr string with all error messages
    """
    stderr_parts = []

    # 1. Get detailed compilation errors from buildResult.stderr
    build_result = result.get("buildResult", {})
    if "stderr" in build_result:
        build_stderr = build_result["stderr"]
        if isinstance(build_stderr, list):
            for item in build_stderr:
                if isinstance(item, dict):
                    stderr_parts.append(item.get("text", ""))
                else:
                    stderr_parts.append(str(item))
        else:
            stderr_parts.append(str(build_stderr))

    # 2. Get high-level messages from top-level result.stderr
    if "stderr" in result:
        top_stderr = result["stderr"]
        if isinstance(top_stderr, list):
            for item in top_stderr:
                if isinstance(item, dict):
                    text = item.get("text", "")
                    # Avoid duplicating generic "Build failed" if we have detailed errors
                    if text != "Build failed" or not stderr_parts:
                        stderr_parts.append(text)
                else:
                    stderr_parts.append(str(item))
        else:
            stderr_parts.append(str(top_stderr))

    # 3. Check for build step errors
    if "buildsteps" in result and isinstance(result["buildsteps"], list):
        for i, step in enumerate(result["buildsteps"]):
            if isinstance(step, dict) and "stderr" in step:
                step_stderr = step["stderr"]
                if step_stderr:  # Only add non-empty stderr
                    if isinstance(step_stderr, list):
                        for item in step_stderr:
                            if isinstance(item, dict):
                                stderr_parts.append(
                                    f"Build step {i+1}: {item.get('text', '')}"
                                )
                            else:
                                stderr_parts.append(f"Build step {i+1}: {str(item)}")
                    else:
                        stderr_parts.append(f"Build step {i+1}: {str(step_stderr)}")

    # 4. Check for execution errors
    if "execResult" in result:
        exec_result = result["execResult"]
        if isinstance(exec_result, dict) and "stderr" in exec_result:
            exec_stderr = exec_result["stderr"]
            if exec_stderr:  # Only add non-empty stderr
                if isinstance(exec_stderr, list):
                    for item in exec_stderr:
                        if isinstance(item, dict):
                            stderr_parts.append(f"Execution: {item.get('text', '')}")
                        else:
                            stderr_parts.append(f"Execution: {str(item)}")
                else:
                    stderr_parts.append(f"Execution: {str(exec_stderr)}")

    # Join all stderr parts, filtering out empty ones
    combined_stderr = "".join(part for part in stderr_parts if part.strip())

    return combined_stderr


async def compile_check(arguments: Dict[str, Any], config: Config) -> Dict[str, Any]:
    """Quick compilation validation."""
    source = arguments["source"]
    language = arguments["language"]
    compiler = config.resolve_compiler(arguments["compiler"])
    options = arguments.get("options", "")
    extract_args = arguments.get("extract_args", True)
    libraries = arguments.get("libraries")

    if extract_args:
        extracted_args = extract_compile_args_from_source(source, language)
        if extracted_args:
            options = f"{options} {extracted_args}".strip()

    client = CompilerExplorerClient(config)

    try:
        # Resolve libraries if provided
        resolved_libraries = []
        if libraries:
            from .library_utils import (
                validate_and_resolve_libraries,
                search_libraries,
                format_library_error_with_suggestions,
                LibraryError,
                LibraryNotFoundError,
            )

            try:
                resolved_libraries = await validate_and_resolve_libraries(
                    libraries, language, compiler, client
                )
            except LibraryError as e:
                # Try to provide helpful suggestions for library errors
                if isinstance(e, LibraryNotFoundError):
                    # Extract the library name from the error for suggestions
                    error_msg = str(e)
                    if "'" in error_msg:
                        lib_name = error_msg.split("'")[1]
                        suggestions = await search_libraries(lib_name, language, client)
                        enhanced_error = format_library_error_with_suggestions(
                            e, lib_name, language, suggestions
                        )
                        raise LibraryError(enhanced_error)
                raise

        result = await client.compile(
            source, language, compiler, options, libraries=resolved_libraries
        )
    finally:
        await client.close()

    return {
        "success": result.get("code", 1) == 0,
        "exit_code": result.get("code", 1),
        "error_count": len(
            [d for d in result.get("diagnostics", []) if d.get("type") == "error"]
        ),
        "warning_count": len(
            [d for d in result.get("diagnostics", []) if d.get("type") == "warning"]
        ),
        "first_error": next(
            (
                d["message"]
                for d in result.get("diagnostics", [])
                if d.get("type") == "error"
            ),
            None,
        ),
    }


async def compile_and_run(arguments: Dict[str, Any], config: Config) -> Dict[str, Any]:
    """Compile and run code, returning execution results."""
    source = arguments["source"]
    language = arguments["language"]
    compiler = config.resolve_compiler(arguments["compiler"])
    options = arguments.get("options", "")
    stdin = arguments.get("stdin", "")
    args = arguments.get("args", [])
    timeout = arguments.get("timeout", 5000)
    libraries = arguments.get("libraries")

    client = CompilerExplorerClient(config)

    try:
        # Resolve libraries if provided
        resolved_libraries = []
        if libraries:
            from .library_utils import (
                validate_and_resolve_libraries,
                search_libraries,
                format_library_error_with_suggestions,
                LibraryError,
                LibraryNotFoundError,
            )

            try:
                resolved_libraries = await validate_and_resolve_libraries(
                    libraries, language, compiler, client
                )
            except LibraryError as e:
                # Try to provide helpful suggestions for library errors
                if isinstance(e, LibraryNotFoundError):
                    # Extract the library name from the error for suggestions
                    error_msg = str(e)
                    if "'" in error_msg:
                        lib_name = error_msg.split("'")[1]
                        suggestions = await search_libraries(lib_name, language, client)
                        enhanced_error = format_library_error_with_suggestions(
                            e, lib_name, language, suggestions
                        )
                        raise LibraryError(enhanced_error)
                raise

        result = await client.compile_and_execute(
            source,
            language,
            compiler,
            options,
            stdin,
            args,
            timeout,
            resolved_libraries,
        )
    finally:
        await client.close()

    # Handle different API response formats
    build_result = result.get("buildResult", result)
    compiled = build_result.get("code", 1) == 0

    # Check for execution results
    executed = result.get("didExecute", False) or "execResult" in result
    exit_code = result.get("code", -1)
    exec_time = result.get("execTime", 0)

    # Handle stdout/stderr from different locations
    if compiled:
        # For successful compilation, execution stdout/stderr is at top level
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
    else:
        # For failed compilation, get stdout from buildResult
        stdout = build_result.get("stdout", "")
        # Collect stderr from all possible locations
        stderr = _collect_all_stderr(result)

    # Convert arrays to strings for both stdout and stderr
    if isinstance(stdout, list):
        stdout = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in stdout
        )

    # stderr is already processed by _collect_all_stderr for compilation failures
    if compiled and isinstance(stderr, list):
        stderr = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in stderr
        )

    return {
        "compiled": compiled,
        "executed": executed,
        "exit_code": exit_code,
        "execution_time_ms": exec_time,
        "stdout": stdout,
        "stderr": stderr,
        "truncated": result.get("truncated", False),
    }


async def compile_with_diagnostics(
    arguments: Dict[str, Any], config: Config
) -> Dict[str, Any]:
    """Get comprehensive compilation warnings and errors."""
    source = arguments["source"]
    language = arguments["language"]
    compiler = config.resolve_compiler(arguments["compiler"])
    options = arguments.get("options", "")
    diagnostic_level = arguments.get("diagnostic_level", "normal")
    libraries = arguments.get("libraries")

    if diagnostic_level == "verbose":
        options = f"{options} -Wall -Wextra -Wpedantic".strip()
    elif diagnostic_level == "normal":
        options = f"{options} -Wall".strip()

    client = CompilerExplorerClient(config)

    try:
        # Resolve libraries if provided
        resolved_libraries = []
        if libraries:
            from .library_utils import (
                validate_and_resolve_libraries,
                search_libraries,
                format_library_error_with_suggestions,
                LibraryError,
                LibraryNotFoundError,
            )

            try:
                resolved_libraries = await validate_and_resolve_libraries(
                    libraries, language, compiler, client
                )
            except LibraryError as e:
                # Try to provide helpful suggestions for library errors
                if isinstance(e, LibraryNotFoundError):
                    # Extract the library name from the error for suggestions
                    error_msg = str(e)
                    if "'" in error_msg:
                        lib_name = error_msg.split("'")[1]
                        suggestions = await search_libraries(lib_name, language, client)
                        enhanced_error = format_library_error_with_suggestions(
                            e, lib_name, language, suggestions
                        )
                        raise LibraryError(enhanced_error)
                raise

        result = await client.compile(
            source, language, compiler, options, libraries=resolved_libraries
        )
    finally:
        await client.close()

    diagnostics = []
    for diag in result.get("stderr", []):
        if "text" in diag:
            diagnostics.append(
                {
                    "type": "error" if "error" in diag["text"].lower() else "warning",
                    "line": diag.get("line", 0),
                    "column": diag.get("column", 0),
                    "message": diag["text"],
                    "suggestion": None,
                }
            )

    return {
        "success": result.get("code", 1) == 0,
        "diagnostics": diagnostics,
        "command": f"{compiler} {options} <source>",
    }


async def analyze_optimization(
    arguments: Dict[str, Any], config: Config
) -> Dict[str, Any]:
    """Check compiler optimizations and assembly analysis."""
    source = arguments["source"]
    language = arguments["language"]
    compiler = config.resolve_compiler(arguments["compiler"])
    optimization_level = arguments.get("optimization_level", "-O3")
    libraries = arguments.get("libraries")

    # Build filter overrides from user preferences
    filter_overrides = {}
    if arguments.get("filter_out_library_code") is not None:
        filter_overrides["libraryCode"] = not arguments["filter_out_library_code"]
    if arguments.get("filter_out_debug_calls") is not None:
        filter_overrides["debugCalls"] = not arguments["filter_out_debug_calls"]
    if arguments.get("do_demangle") is not None:
        filter_overrides["demangle"] = arguments["do_demangle"]

    options = optimization_level
    client = CompilerExplorerClient(config)

    try:
        # Resolve libraries if provided
        resolved_libraries = []
        if libraries:
            from .library_utils import (
                validate_and_resolve_libraries,
                search_libraries,
                format_library_error_with_suggestions,
                LibraryError,
                LibraryNotFoundError,
            )

            try:
                resolved_libraries = await validate_and_resolve_libraries(
                    libraries, language, compiler, client
                )
            except LibraryError as e:
                # Try to provide helpful suggestions for library errors
                if isinstance(e, LibraryNotFoundError):
                    # Extract the library name from the error for suggestions
                    error_msg = str(e)
                    if "'" in error_msg:
                        lib_name = error_msg.split("'")[1]
                        suggestions = await search_libraries(lib_name, language, client)
                        enhanced_error = format_library_error_with_suggestions(
                            e, lib_name, language, suggestions
                        )
                        raise LibraryError(enhanced_error)
                raise

        result = await client.compile(
            source,
            language,
            compiler,
            options,
            get_assembly=True,
            filter_overrides=filter_overrides if filter_overrides else None,
            libraries=resolved_libraries,
        )
    finally:
        await client.close()

    asm_output = result.get("asm", "")

    # Handle assembly output which might be a list of objects or strings
    if isinstance(asm_output, list):
        asm_text = "\n".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in asm_output
        )
    else:
        asm_text = asm_output

    # Return all assembly lines that Compiler Explorer provides
    asm_lines = asm_text.splitlines() if asm_text else []
    instruction_lines = []

    for line in asm_lines:
        line = line.strip()
        # Only skip completely empty lines
        if line:
            instruction_lines.append(line)

    # Analyze assembly for optimizations
    optimizations = {
        "memcpy_conversion": "memcpy" in asm_text or "memmove" in asm_text,
        "vectorization": any(
            inst in asm_text
            for inst in ["movdqu", "movups", "vmovups", "vaddps", "vmov", "vadd"]
        ),
        "function_inlining": "call" not in asm_text.lower(),  # Simple heuristic
        "simd_instructions": [
            inst
            for inst in ["movdqu", "movups", "vmovups", "vaddps", "vmov", "vadd"]
            if inst in asm_text
        ],
    }

    summary = []
    if optimizations["memcpy_conversion"]:
        summary.append("Compiler optimized manual loop to memcpy call")
    if optimizations["vectorization"]:
        summary.append("SIMD vectorization detected")
    if optimizations["function_inlining"]:
        summary.append("Function calls inlined")

    # Limit assembly output for readability
    max_asm_lines = config.output_limits.max_assembly_lines
    truncated_asm = False
    if len(instruction_lines) > max_asm_lines:
        instruction_lines = instruction_lines[:max_asm_lines]
        truncated_asm = True

    return {
        "optimizations_detected": optimizations,
        "summary": (
            "; ".join(summary) if summary else "No significant optimizations detected"
        ),
        "assembly_lines": len(asm_lines),
        "instruction_count": len(instruction_lines),
        "assembly_output": instruction_lines,
        "truncated": truncated_asm,
        "total_instructions": len(instruction_lines)
        + (len(asm_lines) - max_asm_lines if truncated_asm else 0),
    }


async def compare_compilers(
    arguments: Dict[str, Any], config: Config
) -> Dict[str, Any]:
    """Compare output across different compilers, optimization levels, and options.

    This MCP tool provides comprehensive comparison capabilities for analyzing how
    different compiler configurations affect code generation and output.

    **Use Cases:**
    - **Cross-compiler analysis**: Compare GCC vs Clang vs ICC output
    - **Optimization level comparison**: Compare -O0 vs -O2 vs -O3 effects
    - **Architecture comparison**: Compare x86 vs ARM vs RISC-V assembly
    - **Flag impact analysis**: Test effects of -march, -mtune, -ffast-math, etc.
    - **Code style comparison**: Compare different C++ idioms (loops, algorithms)
    - **Performance investigation**: Analyze how code changes affect assembly

    **Parameters:**
    - source: Source code to compile
    - language: Programming language (c++, c, rust, etc.)
    - compilers: List of compiler configurations, each with:
      - id: Compiler identifier (e.g., "g132", "clang1600")
      - options: Compiler flags (e.g., "-O2 -std=c++17", "-O3 -march=native")
    - comparison_type: "assembly", "execution", or "diagnostics"
    - libraries: Optional list of libraries to link

    **Comparison Types:**
    - **assembly**: Detailed assembly diff with instruction analysis
    - **execution**: Compare program outputs and execution results
    - **diagnostics**: Compare compiler warnings and error messages

    **For assembly comparisons, provides:**
    - Unified diffs showing line-by-line changes
    - Statistics on instructions added/removed and function calls
    - Architecture-independent analysis (x86, ARM, RISC-V, MIPS, PowerPC)
    - Human-readable summaries of key differences

    **Example MCP Tool Calls:**

    Compare optimization levels:
    ```
    compare_compilers_tool({
        "source": "int add(int a, int b) { return a + b; }",
        "language": "c++",
        "compilers": [
            {"id": "g132", "options": "-O0"},
            {"id": "g132", "options": "-O2"},
            {"id": "g132", "options": "-O3"}
        ],
        "comparison_type": "assembly"
    })
    ```

    Compare different compilers:
    ```
    compare_compilers_tool({
        "source": "int main() { return 0; }",
        "language": "c++",
        "compilers": [
            {"id": "g132", "options": "-O2 -std=c++17"},
            {"id": "clang1600", "options": "-O2 -std=c++17"}
        ],
        "comparison_type": "assembly"
    })
    ```

    Compare execution results:
    ```
    compare_compilers_tool({
        "source": "#include <iostream>\\nint main() { std::cout << \\"Hello\\"; }",
        "language": "c++",
        "compilers": [
            {"id": "g132", "options": "-O0"},
            {"id": "g132", "options": "-O2"}
        ],
        "comparison_type": "execution"
    })
    ```
    """
    source = arguments["source"]
    language = arguments["language"]
    compilers = arguments["compilers"]
    comparison_type = arguments["comparison_type"]
    libraries = arguments.get("libraries")

    # Import assembly diff utilities
    from .assembly_diff import generate_assembly_diff

    client = CompilerExplorerClient(config)

    try:
        # Resolve libraries if provided
        resolved_libraries = []
        if libraries:
            from .library_utils import (
                validate_and_resolve_libraries,
                search_libraries,
                format_library_error_with_suggestions,
                LibraryError,
                LibraryNotFoundError,
            )

            try:
                # Use first compiler for library validation
                first_compiler = config.resolve_compiler(compilers[0]["id"])
                resolved_libraries = await validate_and_resolve_libraries(
                    libraries, language, first_compiler, client
                )
            except LibraryError as e:
                # Try to provide helpful suggestions for library errors
                if isinstance(e, LibraryNotFoundError):
                    # Extract the library name from the error for suggestions
                    error_msg = str(e)
                    if "'" in error_msg:
                        lib_name = error_msg.split("'")[1]
                        suggestions = await search_libraries(lib_name, language, client)
                        enhanced_error = format_library_error_with_suggestions(
                            e, lib_name, language, suggestions
                        )
                        raise LibraryError(enhanced_error)
                raise

        results = []

        for comp_config in compilers:
            compiler_id = config.resolve_compiler(comp_config["id"])
            options = comp_config.get("options", "")

            if comparison_type == "execution":
                result = await client.compile_and_execute(
                    source, language, compiler_id, options, libraries=resolved_libraries
                )
                results.append(
                    {
                        "compiler": compiler_id,
                        "options": options,
                        "execution_result": result.get("execResult", {}).get(
                            "stdout", ""
                        ),
                        "assembly_size": 0,
                        "warnings": 0,
                    }
                )
            elif comparison_type == "assembly":
                result = await client.compile(
                    source,
                    language,
                    compiler_id,
                    options,
                    get_assembly=True,
                    libraries=resolved_libraries,
                )
                # Extract assembly text
                asm = result.get("asm", "")
                if isinstance(asm, list):
                    asm = "\n".join(
                        item.get("text", "") for item in asm if isinstance(item, dict)
                    )

                results.append(
                    {
                        "compiler": compiler_id,
                        "options": options,
                        "execution_result": "",
                        "assembly": asm,  # Store full assembly for diff
                        "assembly_size": len(asm.splitlines()),
                        "warnings": len(
                            [
                                d
                                for d in result.get("stderr", [])
                                if "warning" in d.get("text", "").lower()
                            ]
                        ),
                    }
                )
            else:  # diagnostics
                result = await client.compile(
                    source, language, compiler_id, options, libraries=resolved_libraries
                )
                results.append(
                    {
                        "compiler": compiler_id,
                        "options": options,
                        "execution_result": "",
                        "assembly_size": 0,
                        "warnings": len(
                            [
                                d
                                for d in result.get("stderr", [])
                                if "warning" in d.get("text", "").lower()
                            ]
                        ),
                    }
                )
    finally:
        await client.close()

    # Generate differences summary
    differences = []
    assembly_diff = None

    if len(results) >= 2:
        if comparison_type == "assembly":
            # Size comparison
            size_diff = results[0]["assembly_size"] - results[1]["assembly_size"]
            if size_diff != 0:
                percent = abs(size_diff) / max(results[0]["assembly_size"], 1) * 100
                differences.append(
                    f"{results[1]['compiler']} produces {percent:.0f}% {'smaller' if size_diff > 0 else 'larger'} code"
                )

            # Generate assembly diff
            if "assembly" in results[0] and "assembly" in results[1]:
                assembly_diff = generate_assembly_diff(
                    results[0]["assembly"],
                    results[1]["assembly"],
                    label1=f"{results[0]['compiler']} {results[0]['options']}",
                    label2=f"{results[1]['compiler']} {results[1]['options']}",
                    context=3,
                )

                # Add diff summary to differences
                if assembly_diff and "summary" in assembly_diff:
                    differences.append(assembly_diff["summary"])

        elif comparison_type == "execution":
            # Compare execution results
            if results[0].get("execution_result") != results[1].get("execution_result"):
                differences.append("Execution outputs differ")

        elif comparison_type == "diagnostics":
            # Compare warning counts
            warn_diff = results[0]["warnings"] - results[1]["warnings"]
            if warn_diff != 0:
                differences.append(
                    f"{results[1]['compiler']} produces {abs(warn_diff)} {'fewer' if warn_diff > 0 else 'more'} warnings"
                )

    # Remove assembly from results to keep response concise
    for result in results:
        result.pop("assembly", None)

    response = {
        "results": results,
        "differences": differences,
    }

    # Add assembly diff details if available
    if assembly_diff:
        response["assembly_diff"] = {
            "statistics": assembly_diff["statistics"],
            "summary": assembly_diff["summary"],
            # Include truncated unified diff
            "unified_diff": "\n".join(assembly_diff["unified_diff"].splitlines()[:50])
            + "\n... (truncated)",
        }

    return response


async def generate_share_url(
    arguments: Dict[str, Any], config: Config
) -> Dict[str, Any]:
    """Generate Compiler Explorer URLs for collaboration."""
    source = arguments["source"]
    language = arguments["language"]
    compiler = config.resolve_compiler(arguments["compiler"])
    options = arguments.get("options", "")
    layout = arguments.get("layout", "simple")
    libraries = arguments.get("libraries")

    client = CompilerExplorerClient(config)

    try:
        # Resolve libraries if provided
        resolved_libraries = []
        if libraries:
            from .library_utils import (
                validate_and_resolve_libraries,
                search_libraries,
                format_library_error_with_suggestions,
                LibraryError,
                LibraryNotFoundError,
            )

            try:
                resolved_libraries = await validate_and_resolve_libraries(
                    libraries, language, compiler, client
                )
            except LibraryError as e:
                # Try to provide helpful suggestions for library errors
                if isinstance(e, LibraryNotFoundError):
                    # Extract the library name from the error for suggestions
                    error_msg = str(e)
                    if "'" in error_msg:
                        lib_name = error_msg.split("'")[1]
                        suggestions = await search_libraries(lib_name, language, client)
                        enhanced_error = format_library_error_with_suggestions(
                            e, lib_name, language, suggestions
                        )
                        raise LibraryError(enhanced_error)
                raise

        url = await client.create_short_link(
            source, language, compiler, options, layout, resolved_libraries
        )
    finally:
        await client.close()

    return {
        "url": url,
        "short_url": url,
        "configuration": {
            "compiler": compiler,
            "options": options,
        },
    }


async def find_experimental_compilers(
    arguments: Dict[str, Any], config: Config
) -> Dict[str, Any]:
    """Find experimental compilers supporting specific proposals or features."""
    language = arguments.get("language", "c++")
    proposal = arguments.get("proposal")
    feature = arguments.get("feature")
    category = arguments.get("category")
    show_all = arguments.get("show_all", False)

    client = CompilerExplorerClient(config)

    try:
        experimental_compilers = await search_experimental_compilers(
            language=language,
            client=client,
            proposal=proposal,
            feature=feature,
            category=category,
            fetch_versions=True,
        )

        # If no filters provided, categorize all experimental compilers
        if not any([proposal, feature, category]) or show_all:
            compilers = await client.get_compilers(language, include_extended_info=True)
            finder = ExperimentalCompilerFinder()
            categorized = finder.categorize_compilers(compilers)

            # Fetch version info for all nightly compilers
            from .experimental_utils import fetch_version_info_for_compilers

            for cat_compilers in categorized.values():
                await fetch_version_info_for_compilers(cat_compilers, client)

            result: Dict[str, Any] = {
                "summary": {
                    "total_experimental": sum(
                        len(compilers) for compilers in categorized.values()
                    ),
                    "categories_found": len(categorized),
                    "language": language,
                },
                "categories": {},
            }

            for cat_name, cat_compilers in categorized.items():
                result["categories"][cat_name] = {
                    "count": len(cat_compilers),
                    "compilers": [
                        {
                            "id": comp.id,
                            "name": comp.name,
                            "proposals": comp.proposal_numbers,
                            "features": comp.features,
                            "is_nightly": comp.is_nightly,
                            "description": comp.description,
                            "version_info": comp.version_info,
                            "modified": comp.modified,
                        }
                        for comp in cat_compilers
                    ],
                }

        else:
            # Return filtered results
            result = {
                "summary": {
                    "total_found": len(experimental_compilers),
                    "language": language,
                    "filter_used": proposal or feature or category,
                },
                "compilers": [
                    {
                        "id": comp.id,
                        "name": comp.name,
                        "category": comp.category,
                        "proposals": comp.proposal_numbers,
                        "features": comp.features,
                        "is_nightly": comp.is_nightly,
                        "description": comp.description,
                        "version_info": comp.version_info,
                        "modified": comp.modified,
                    }
                    for comp in experimental_compilers
                ],
            }

        # Add usage examples
        if proposal:
            result["usage_example"] = {
                "description": f"To use {proposal} features with the found compiler(s)",
                "example_compilers": [comp.id for comp in experimental_compilers[:3]],
            }

        return result

    finally:
        await client.close()

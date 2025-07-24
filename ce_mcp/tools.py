"""Tool implementations for Compiler Explorer MCP."""

from typing import Any, Dict

from .config import Config
from .api_client import CompilerExplorerClient
from .utils import extract_compile_args_from_source


async def compile_check(arguments: Dict[str, Any], config: Config) -> Dict[str, Any]:
    """Quick compilation validation."""
    source = arguments["source"]
    language = arguments["language"]
    compiler = config.resolve_compiler(arguments["compiler"])
    options = arguments.get("options", "")
    extract_args = arguments.get("extract_args", True)

    if extract_args:
        extracted_args = extract_compile_args_from_source(source, language)
        if extracted_args:
            options = f"{options} {extracted_args}".strip()

    client = CompilerExplorerClient(config)
    result = await client.compile(source, language, compiler, options)

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

    client = CompilerExplorerClient(config)
    result = await client.compile_and_execute(
        source, language, compiler, options, stdin, args, timeout
    )

    # Handle different API response formats
    build_result = result.get("buildResult", result)
    compiled = build_result.get("code", 1) == 0

    # Check for execution results
    executed = result.get("didExecute", False) or "execResult" in result
    exit_code = result.get("code", -1)
    exec_time = result.get("execTime", 0)

    # Handle stdout/stderr which might be arrays of objects or strings
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")

    if isinstance(stdout, list):
        stdout = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in stdout
        )

    if isinstance(stderr, list):
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

    if diagnostic_level == "verbose":
        options = f"{options} -Wall -Wextra -Wpedantic".strip()
    elif diagnostic_level == "normal":
        options = f"{options} -Wall".strip()

    client = CompilerExplorerClient(config)
    result = await client.compile(source, language, compiler, options)

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
    result = await client.compile(
        source,
        language,
        compiler,
        options,
        get_assembly=True,
        filter_overrides=filter_overrides if filter_overrides else None,
    )

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
        "loop_unrolling": False,
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
    """Compare output across different compilers/options."""
    source = arguments["source"]
    language = arguments["language"]
    compilers = arguments["compilers"]
    comparison_type = arguments["comparison_type"]

    client = CompilerExplorerClient(config)
    results = []

    for comp_config in compilers:
        compiler_id = config.resolve_compiler(comp_config["id"])
        options = comp_config.get("options", "")

        if comparison_type == "execution":
            result = await client.compile_and_execute(
                source, language, compiler_id, options
            )
            results.append(
                {
                    "compiler": compiler_id,
                    "options": options,
                    "execution_result": result.get("execResult", {}).get("stdout", ""),
                    "assembly_size": 0,
                    "warnings": 0,
                }
            )
        elif comparison_type == "assembly":
            result = await client.compile(
                source, language, compiler_id, options, get_assembly=True
            )
            results.append(
                {
                    "compiler": compiler_id,
                    "options": options,
                    "execution_result": "",
                    "assembly_size": len(result.get("asm", "").splitlines()),
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
            result = await client.compile(source, language, compiler_id, options)
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

    # Generate differences summary
    differences = []
    if len(results) >= 2 and comparison_type == "assembly":
        size_diff = results[0]["assembly_size"] - results[1]["assembly_size"]
        if size_diff != 0:
            percent = abs(size_diff) / max(results[0]["assembly_size"], 1) * 100
            differences.append(
                f"{results[1]['compiler']} produces {percent:.0f}% {'smaller' if size_diff > 0 else 'larger'} code"
            )

    return {
        "results": results,
        "differences": differences,
    }


async def generate_share_url(
    arguments: Dict[str, Any], config: Config
) -> Dict[str, Any]:
    """Generate Compiler Explorer URLs for collaboration."""
    source = arguments["source"]
    language = arguments["language"]
    compiler = config.resolve_compiler(arguments["compiler"])
    options = arguments.get("options", "")
    layout = arguments.get("layout", "simple")

    client = CompilerExplorerClient(config)
    url = await client.create_short_link(source, language, compiler, options, layout)

    return {
        "url": url,
        "short_url": url,
        "configuration": {
            "compiler": compiler,
            "options": options,
        },
    }

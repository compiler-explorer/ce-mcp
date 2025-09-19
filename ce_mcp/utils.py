"""Utility functions for Compiler Explorer MCP."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


def extract_compile_args_from_source(source_code: str, language: str) -> Optional[str]:
    """
    Extract compilation arguments from source code comments.

    Looks for 'compile:' or 'flags:' directives in the first 10 lines.
    Supports both C++ (//) and Pascal ({}) comment styles.
    """
    lines = source_code.split("\n")[:10]

    # Patterns for different comment styles
    patterns = [
        r"//\s*(?:compile|flags):\s*(.+)$",  # C++ style
        r"/\*\s*(?:compile|flags):\s*(.+)\*/",  # C style
        r"\{\s*(?:compile|flags):\s*(.+)\}",  # Pascal style
        r"#\s*(?:compile|flags):\s*(.+)$",  # Python/Shell style
        r"--\s*(?:compile|flags):\s*(.+)$",  # SQL/Haskell style
    ]

    for line in lines:
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip()

    return None


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"  # No Color


def truncate_output(text: str, max_lines: int, max_line_length: int = 200) -> tuple[str, bool]:
    """
    Truncate output to specified limits.

    Returns (truncated_text, was_truncated).
    """
    lines = text.splitlines()
    was_truncated = False

    # Truncate number of lines
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        was_truncated = True

    # Truncate line lengths
    truncated_lines = []
    for line in lines:
        if len(line) > max_line_length:
            truncated_lines.append(line[:max_line_length] + "...")
            was_truncated = True
        else:
            truncated_lines.append(line)

    result = "\n".join(truncated_lines)
    if was_truncated:
        result += "\n... (output truncated)"

    return result, was_truncated


def format_diagnostics(diagnostics: list) -> str:
    """Format compiler diagnostics for display."""
    if not diagnostics:
        return "No diagnostics"

    formatted = []
    for diag in diagnostics:
        diag_type = diag.get("type", "info")
        line = diag.get("line", 0)
        column = diag.get("column", 0)
        message = diag.get("message", "")

        if diag_type == "error":
            color = Colors.RED
        elif diag_type == "warning":
            color = Colors.YELLOW
        else:
            color = Colors.BLUE

        formatted.append(f"{color}{diag_type.upper()}{Colors.NC} at {line}:{column}: {message}")

    return "\n".join(formatted)


def get_default_compiler_for_language(language: str) -> str:
    """Get default compiler for a programming language."""
    defaults = {
        "c++": "g132",
        "c": "cg132",
        "rust": "r1740",
        "go": "gccgo132",
        "python": "python311",
        "pascal": "fpc322",
        "java": "java2000",
        "javascript": "nodelatest",
        "typescript": "tsc500",
        "haskell": "ghc961",
    }
    return defaults.get(language.lower(), "g132")


def parse_execution_result(exec_result: dict) -> dict:
    """Parse execution result from API response."""
    return {
        "stdout": exec_result.get("stdout", ""),
        "stderr": exec_result.get("stderr", ""),
        "code": exec_result.get("code", -1),
        "didExecute": exec_result.get("didExecute", False),
        "buildResult": exec_result.get("buildResult", {}),
        "execTime": exec_result.get("execTime", 0),
    }


def apply_text_filter(compilers_list: List[Any], search_text: Optional[str], exact_search: bool = False) -> List[Any]:
    """Filter compilers by search text in names and IDs."""
    if not search_text:
        return compilers_list

    if exact_search:
        # Exact match on compiler ID (case-sensitive)
        return [comp for comp in compilers_list if comp.id == search_text]
    else:
        # Partial match on names and IDs (case-insensitive)
        search_lower = search_text.lower()
        return [comp for comp in compilers_list if search_lower in comp.id.lower() or search_lower in comp.name.lower()]


def format_compiler_info(
    comp: Any,
    ids_only: bool = False,
    include_overrides: bool = False,
    include_runtime_tools: bool = False,
    include_compile_tools: bool = False,
) -> Union[str, Dict[str, Any]]:
    """Format compiler info with optional ids_only mode, overrides, and tools."""
    if ids_only:
        return str(comp.id)

    info = {
        "id": comp.id,
        "name": comp.name,
        "proposals": comp.proposal_numbers,
        "features": comp.features,
        "is_nightly": comp.is_nightly,
        "description": comp.description,
        "version_info": comp.version_info,
        "modified": comp.modified,
    }

    # Add possibleOverrides if requested and available
    if include_overrides and hasattr(comp, "possible_overrides"):
        info["possible_overrides"] = comp.possible_overrides

    # Add possibleRuntimeTools if requested and available
    if include_runtime_tools and hasattr(comp, "possible_runtime_tools"):
        info["possible_runtime_tools"] = comp.possible_runtime_tools

    # Add tools (compile-time tools) if requested and available
    if include_compile_tools and hasattr(comp, "tools"):
        if isinstance(comp.tools, dict):
            info["tools"] = {
                tool_id: {"id": tool_data["id"], "name": tool_data["tool"]["name"]}
                for tool_id, tool_data in comp.tools.items()
            }
        else:
            # Handle case where tools is a list
            info["tools"] = comp.tools

    return info


def extract_link_id(shortlink_url: str) -> str:
    """
    Extract the link ID from a Compiler Explorer URL.

    Args:
        shortlink_url: Full URL (https://godbolt.org/z/G38YP7eW4) or just ID (G38YP7eW4)

    Returns:
        The extracted link ID

    Raises:
        ValueError: If the URL format is invalid
    """
    # If it's already just an ID (no protocol/domain), return it
    if not shortlink_url.startswith(("http://", "https://")):
        return shortlink_url.strip()

    try:
        parsed = urlparse(shortlink_url)
        path = parsed.path.strip("/")

        # Handle /z/ prefix for godbolt URLs
        if path.startswith("z/"):
            return path[2:]  # Remove "z/" prefix

        # If no z/ prefix, assume the path is the ID
        return path
    except Exception as e:
        raise ValueError(f"Invalid shortlink URL format: {shortlink_url}") from e


async def get_language_extension(language: str, client: Optional[Any] = None) -> str:
    """
    Get the primary file extension for a language from CE's languages API.

    Args:
        language: Programming language name
        client: Optional CE client (if None, falls back to static mapping)

    Returns:
        File extension (with dot) for the language
    """
    if client:
        try:
            languages = await client.get_languages()

            # Find matching language (case-insensitive)
            for lang_data in languages:
                if lang_data.get("id", "").lower() == language.lower():
                    extensions = lang_data.get("extensions", [])
                    if extensions:
                        # Return the first extension as primary
                        return str(extensions[0])
        except Exception:
            # Fall back to static mapping if API fails
            pass

    # Static fallback mapping for common languages
    extension_map = {
        "c++": ".cpp",
        "cpp": ".cpp",
        "c": ".c",
        "rust": ".rs",
        "go": ".go",
        "python": ".py",
        "java": ".java",
        "javascript": ".js",
        "typescript": ".ts",
        "kotlin": ".kt",
        "swift": ".swift",
        "pascal": ".pas",
        "fortran": ".f90",
        "assembly": ".s",
        "haskell": ".hs",
        "csharp": ".cs",
        "fsharp": ".fs",
        "d": ".d",
        "nim": ".nim",
        "zig": ".zig",
        "v": ".v",
        "ada": ".adb",
        "cobol": ".cob",
    }

    return extension_map.get(language.lower(), ".txt")


async def generate_filename(
    original_filename: Optional[str],
    language: str,
    file_index: int,
    fallback_prefix: str = "ce",
    is_main_source: bool = False,
    client: Optional[Any] = None,
) -> str:
    """
    Generate an appropriate filename for a source file.

    Args:
        original_filename: Original filename from CE (may be None)
        language: Programming language
        file_index: Index for multiple files (1-based)
        fallback_prefix: Prefix when no original filename
        is_main_source: Whether this is marked as the main source file
        client: Optional CE client for language extension lookup

    Returns:
        Generated filename
    """
    # Use original filename if available
    if original_filename and original_filename.strip():
        filename = original_filename.strip()
        # Add main suffix if requested and not already present
        if is_main_source and not filename.endswith("_main"):
            base, ext = os.path.splitext(filename)
            filename = f"{base}_main{ext}"
        return filename

    # Get extension from API or fallback
    ext = await get_language_extension(language, client)
    main_suffix = "_main" if is_main_source else ""

    return f"{fallback_prefix}_{file_index:03d}{main_suffix}{ext}"


def resolve_filename_conflicts(target_path: Path, preferred_filename: str) -> str:
    """
    Resolve filename conflicts by adding numbers.

    Args:
        target_path: Directory where file will be saved
        preferred_filename: Desired filename

    Returns:
        Available filename (may have number suffix)
    """
    full_path = target_path / preferred_filename

    if not full_path.exists():
        return preferred_filename

    # Extract base name and extension
    base = full_path.stem
    suffix = full_path.suffix

    # Try numbered variants
    counter = 1
    while True:
        new_filename = f"{base}_{counter}{suffix}"
        if not (target_path / new_filename).exists():
            return new_filename
        counter += 1

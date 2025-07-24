"""Utility functions for Compiler Explorer MCP."""

import re
from typing import Optional


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


def truncate_output(
    text: str, max_lines: int, max_line_length: int = 200
) -> tuple[str, bool]:
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

        formatted.append(
            f"{color}{diag_type.upper()}{Colors.NC} at {line}:{column}: {message}"
        )

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

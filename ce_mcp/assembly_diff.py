"""Assembly diff and comparison utilities."""

import difflib
import re
from typing import List, Dict, Any, Tuple, Optional


def extract_function_assembly(asm_text: str, function_name: str) -> Optional[str]:
    """Extract assembly for a specific function from full assembly output."""
    lines = asm_text.splitlines()
    start_idx = None

    # Find function start
    for i, line in enumerate(lines):
        # Match function definitions (various formats)
        if function_name in line and any(marker in line for marker in [":", "(", "<"]):
            start_idx = i
            break

    if start_idx is None:
        return None

    # Find function end - look for next function or end
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        # Heuristics for function end:
        # 1. Next function definition (non-indented label with colon)
        # 2. End of file
        if lines[i] and not lines[i].startswith((" ", "\t")) and ":" in lines[i]:
            # Check if it's not just a label within the function
            if not lines[i].strip().startswith("."):
                end_idx = i
                break

    return "\n".join(lines[start_idx:end_idx])


def normalize_assembly(asm_text: str) -> List[str]:
    """Normalize assembly for better comparison."""
    lines = asm_text.splitlines()
    normalized = []

    for line in lines:
        # Skip comment-only lines
        if line.strip().startswith("#"):
            continue

        # Remove inline comments
        if "#" in line:
            line = line[: line.index("#")].rstrip()

        # Skip empty lines
        if not line.strip():
            continue

        # Normalize whitespace
        line = " ".join(line.split())

        normalized.append(line)

    return normalized


def generate_assembly_diff(
    asm1: str,
    asm2: str,
    label1: str = "Compiler 1",
    label2: str = "Compiler 2",
    context: int = 3,
) -> Dict[str, Any]:
    """Generate a structured diff between two assembly outputs."""
    lines1 = normalize_assembly(asm1)
    lines2 = normalize_assembly(asm2)

    # Generate unified diff
    diff_lines = list(
        difflib.unified_diff(
            lines1, lines2, fromfile=label1, tofile=label2, lineterm="", n=context
        )
    )

    # Analyze the diff
    stats = analyze_diff(diff_lines)

    # Generate side-by-side comparison for key differences
    side_by_side = generate_side_by_side(lines1, lines2, max_width=50)

    return {
        "unified_diff": "\n".join(diff_lines),
        "side_by_side": side_by_side,
        "statistics": stats,
        "summary": generate_diff_summary(stats, lines1, lines2),
    }


def analyze_diff(diff_lines: List[str]) -> Dict[str, Any]:
    """Analyze diff to extract statistics and patterns."""
    stats = {
        "lines_added": 0,
        "lines_removed": 0,
        "lines_changed": 0,
        "instructions_added": [],
        "instructions_removed": [],
        "function_calls_added": [],
        "function_calls_removed": [],
    }

    for line in diff_lines:
        if line.startswith("+") and not line.startswith("+++"):
            stats["lines_added"] += 1
            # Extract instruction
            instruction = extract_instruction(line[1:])
            if instruction:
                stats["instructions_added"].append(instruction)
            # Check for function calls
            call = extract_function_call(line[1:])
            if call:
                stats["function_calls_added"].append(call)

        elif line.startswith("-") and not line.startswith("---"):
            stats["lines_removed"] += 1
            instruction = extract_instruction(line[1:])
            if instruction:
                stats["instructions_removed"].append(instruction)
            call = extract_function_call(line[1:])
            if call:
                stats["function_calls_removed"].append(call)

    # Deduplicate and count
    stats["unique_instructions_added"] = list(set(stats["instructions_added"]))
    stats["unique_instructions_removed"] = list(set(stats["instructions_removed"]))
    stats["unique_calls_added"] = list(set(stats["function_calls_added"]))
    stats["unique_calls_removed"] = list(set(stats["function_calls_removed"]))

    return stats


def extract_instruction(line: str) -> Optional[str]:
    """Extract the instruction mnemonic from an assembly line.

    Architecture-independent approach:
    - Skip lines that are labels (end with :)
    - Skip directives (start with .)
    - Extract first token as instruction if it looks like one
    """
    stripped = line.strip()

    # Skip empty lines
    if not stripped:
        return None

    # Skip labels (end with colon)
    if stripped.endswith(":"):
        return None

    # Skip directives (start with dot)
    if stripped.startswith("."):
        return None

    # Skip preprocessor directives (start with #)
    if stripped.startswith("#"):
        return None

    parts = stripped.split()
    if not parts:
        return None

    # First token is likely the instruction
    potential_instruction = parts[0].lower()

    # Basic heuristic: instructions are typically short alphanumeric strings
    # May contain dots (like ARM's conditional suffixes: beq.n)
    # May contain numbers (like x86's movq, arm's ldr.w)
    if re.match(r"^[a-z][a-z0-9._]*$", potential_instruction):
        # Additional check: very long "instructions" are probably not instructions
        if len(potential_instruction) <= 10:  # reasonable length for most architectures
            return potential_instruction

    return None


def extract_function_call(line: str) -> Optional[str]:
    """Extract function call target from assembly line.

    Architecture-independent approach:
    - Look for common call instructions across architectures
    - Extract the target of the call
    """
    stripped = line.strip().lower()
    parts = stripped.split()

    if len(parts) < 2:
        return None

    # Common call/branch instructions across architectures
    # x86/x64: call
    # ARM: bl, blx, bx (branch and link)
    # MIPS: jal, jalr (jump and link)
    # RISC-V: jal, jalr (jump and link)
    # PowerPC: bl (branch and link)
    call_instructions = ["call", "bl", "blx", "jal", "jalr"]

    instruction = parts[0]
    if instruction in call_instructions:
        # The target is typically the rest of the line after the instruction
        # We need to preserve the original case and format
        original_parts = line.strip().split(None, 1)  # Split only on first space
        if len(original_parts) > 1:
            target = original_parts[1]
            # For x86 indirect calls like "call QWORD PTR [rax]"
            if "ptr" in target.lower() and "[" in target:
                # Just return the simplified form
                return f"indirect_{instruction}"
            # Remove only enclosing brackets if present, but preserve function signatures
            if target.startswith("[") and target.endswith("]"):
                target = target[1:-1]
            return target

    return None


def generate_side_by_side(
    lines1: List[str], lines2: List[str], max_width: int = 50
) -> List[Tuple[str, str]]:
    """Generate side-by-side comparison of key differences."""
    # Use sequence matcher to find differences
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    side_by_side = []

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            # Skip equal parts in side-by-side view
            continue
        elif op == "replace":
            # Show replaced lines side by side
            for i in range(max(i2 - i1, j2 - j1)):
                left = lines1[i1 + i] if i1 + i < i2 else ""
                right = lines2[j1 + i] if j1 + i < j2 else ""
                side_by_side.append((left[:max_width], right[:max_width]))
        elif op == "delete":
            # Show deleted lines on left only
            for i in range(i1, i2):
                side_by_side.append((lines1[i][:max_width], ""))
        elif op == "insert":
            # Show inserted lines on right only
            for j in range(j1, j2):
                side_by_side.append(("", lines2[j][:max_width]))

    return side_by_side


def generate_diff_summary(
    stats: Dict[str, Any], lines1: List[str], lines2: List[str]
) -> str:
    """Generate a human-readable summary of the differences."""
    summary_parts = []

    # Size comparison
    size_diff = len(lines2) - len(lines1)
    if size_diff > 0:
        summary_parts.append(f"Second version is {size_diff} lines longer")
    elif size_diff < 0:
        summary_parts.append(f"Second version is {-size_diff} lines shorter")
    else:
        summary_parts.append("Both versions have the same number of lines")

    # Instruction differences
    if stats["unique_instructions_added"]:
        # Show up to 5 new instructions
        new_insts = stats["unique_instructions_added"][:5]
        if len(stats["unique_instructions_added"]) > 5:
            summary_parts.append(
                f"New instructions: {', '.join(new_insts)} (+{len(stats['unique_instructions_added'])-5} more)"
            )
        else:
            summary_parts.append(f"New instructions: {', '.join(new_insts)}")

    if stats["unique_instructions_removed"]:
        # Show up to 5 removed instructions
        removed_insts = stats["unique_instructions_removed"][:5]
        if len(stats["unique_instructions_removed"]) > 5:
            summary_parts.append(
                f"Removed instructions: {', '.join(removed_insts)} (+{len(stats['unique_instructions_removed'])-5} more)"
            )
        else:
            summary_parts.append(f"Removed instructions: {', '.join(removed_insts)}")

    # Function call differences
    if stats["unique_calls_added"]:
        # Show up to 3 new calls
        new_calls = stats["unique_calls_added"][:3]
        if len(stats["unique_calls_added"]) > 3:
            summary_parts.append(
                f"New function calls: {', '.join(new_calls)} (+{len(stats['unique_calls_added'])-3} more)"
            )
        else:
            summary_parts.append(f"New function calls: {', '.join(new_calls)}")

    if stats["unique_calls_removed"]:
        # Show up to 3 removed calls
        removed_calls = stats["unique_calls_removed"][:3]
        if len(stats["unique_calls_removed"]) > 3:
            summary_parts.append(
                f"Removed function calls: {', '.join(removed_calls)} (+{len(stats['unique_calls_removed'])-3} more)"
            )
        else:
            summary_parts.append(f"Removed function calls: {', '.join(removed_calls)}")

    return " | ".join(summary_parts)


def compare_optimization_levels(
    source: str, compilers: List[Dict[str, str]], client: Any
) -> Dict[str, Any]:
    """Compare assembly across different optimization levels.
    
    This is a placeholder function for future optimization level comparison.
    Currently returns empty results.
    """
    # TODO: Implement optimization level comparison
    # This would compile the source with different optimization levels
    # and return a comparison of the resulting assembly
    return {}

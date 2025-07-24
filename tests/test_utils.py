"""Tests for utility functions."""

from ce_mcp.utils import extract_compile_args_from_source, truncate_output


class TestExtractCompileArgs:
    """Test compile argument extraction."""

    def test_cpp_style_comment(self):
        source = """// compile: -O2 -Wall
#include <iostream>
int main() { return 0; }"""
        assert extract_compile_args_from_source(source, "c++") == "-O2 -Wall"

    def test_c_style_comment(self):
        source = """/* flags: -std=c99 */
#include <stdio.h>
int main() { return 0; }"""
        assert extract_compile_args_from_source(source, "c") == "-std=c99"

    def test_pascal_style_comment(self):
        source = """{ compile: -O3 }
program Hello;
begin
end."""
        assert extract_compile_args_from_source(source, "pascal") == "-O3"

    def test_no_compile_args(self):
        source = """#include <iostream>
int main() { return 0; }"""
        assert extract_compile_args_from_source(source, "c++") is None

    def test_case_insensitive(self):
        source = """// COMPILE: -O2
int main() { return 0; }"""
        assert extract_compile_args_from_source(source, "c++") == "-O2"


class TestTruncateOutput:
    """Test output truncation."""

    def test_no_truncation_needed(self):
        text = "Line 1\nLine 2\nLine 3"
        result, was_truncated = truncate_output(text, 10, 100)
        assert result == text
        assert not was_truncated

    def test_line_count_truncation(self):
        text = "\n".join(f"Line {i}" for i in range(20))
        result, was_truncated = truncate_output(text, 5, 100)
        assert len(result.splitlines()) == 6  # 5 lines + truncation message
        assert was_truncated
        assert "... (output truncated)" in result

    def test_line_length_truncation(self):
        text = "A" * 300
        result, was_truncated = truncate_output(text, 10, 200)
        assert len(result.splitlines()[0]) == 203  # 200 chars + "..."
        assert was_truncated
        assert result.startswith("A" * 200)

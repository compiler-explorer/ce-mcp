"""Tests for assembly diff functionality."""

import pytest
from ce_mcp.assembly_diff import (
    extract_function_assembly,
    normalize_assembly,
    generate_assembly_diff,
    extract_instruction,
    extract_function_call,
    generate_diff_summary,
)


class TestAssemblyDiff:
    """Test assembly diff and comparison utilities."""

    def test_extract_function_assembly(self):
        """Test extracting a specific function from assembly."""
        asm = """
main:
    push rbp
    mov rbp, rsp
    mov eax, 0
    pop rbp
    ret
helper_function:
    push rbp
    mov rbp, rsp
    ret
"""
        main_asm = extract_function_assembly(asm, "main")
        assert main_asm is not None
        assert "main:" in main_asm
        assert "helper_function:" not in main_asm
        assert main_asm.count('\n') == 5  # 6 lines total

    def test_normalize_assembly(self):
        """Test assembly normalization."""
        asm = """
    # This is a comment
    mov eax, 0  # inline comment
    
    add ebx, 1
        jmp    .L2   # lots of spaces
"""
        normalized = normalize_assembly(asm)
        assert len(normalized) == 3  # Comments and empty lines removed
        assert normalized[0] == "mov eax, 0"
        assert normalized[1] == "add ebx, 1"
        assert normalized[2] == "jmp .L2"

    def test_extract_instruction(self):
        """Test instruction extraction."""
        assert extract_instruction("mov eax, 0") == "mov"
        assert extract_instruction("add rbx, 1") == "add"
        assert extract_instruction("call printf") == "call"
        assert extract_instruction(".L2:") is None  # Label
        assert extract_instruction(".section .text") is None  # Directive

    def test_extract_function_call(self):
        """Test function call extraction."""
        assert extract_function_call("call printf") == "printf"
        assert extract_function_call("call std::vector<int>::size()") == "std::vector<int>::size()"
        assert extract_function_call("mov eax, 0") is None
        assert extract_function_call("jmp .L2") is None

    def test_generate_assembly_diff(self):
        """Test generating assembly diff."""
        asm1 = """
function1:
    push rbp
    mov rbp, rsp
    mov eax, 0
    pop rbp
    ret
"""
        asm2 = """
function1:
    push rbp
    mov rbp, rsp
    xor eax, eax  # Different instruction
    leave         # Different epilogue
    ret
"""
        diff_result = generate_assembly_diff(asm1, asm2, "Version 1", "Version 2")
        
        assert "unified_diff" in diff_result
        assert "statistics" in diff_result
        assert "summary" in diff_result
        
        stats = diff_result["statistics"]
        assert stats["lines_added"] == 2  # xor and leave
        assert stats["lines_removed"] == 2  # mov and pop
        assert "xor" in stats["unique_instructions_added"]
        assert "leave" in stats["unique_instructions_added"]
        assert "mov" in stats["unique_instructions_removed"]
        assert "pop" in stats["unique_instructions_removed"]

    def test_diff_summary_generation(self):
        """Test diff summary generation."""
        stats = {
            "unique_instructions_added": ["xor", "lea", "test"],
            "unique_instructions_removed": ["mov", "cmp"],
            "unique_calls_added": ["malloc", "free"],
            "unique_calls_removed": ["new", "delete"],
        }
        lines1 = ["line1", "line2", "line3"]
        lines2 = ["line1", "line2"]
        
        summary = generate_diff_summary(stats, lines1, lines2)
        
        assert "1 lines shorter" in summary
        assert "xor" in summary
        assert "malloc" in summary

    def test_loop_comparison_diff(self):
        """Test comparing different loop implementations."""
        # Simplified assembly for index-based loop
        index_loop_asm = """
sum_index_loop:
    push rbp
    mov rbp, rsp
    mov QWORD PTR [rbp-16], 0
.L2:
    mov rax, QWORD PTR [rbp-16]
    cmp rax, QWORD PTR [rbp-8]
    jge .L3
    mov rax, QWORD PTR [rbp-24]
    mov rdx, QWORD PTR [rbp-16]
    call std::vector<int>::operator[]
    mov eax, DWORD PTR [rax]
    add DWORD PTR [rbp-4], eax
    add QWORD PTR [rbp-16], 1
    jmp .L2
.L3:
    mov eax, DWORD PTR [rbp-4]
    pop rbp
    ret
"""
        
        # Simplified assembly for range-based loop
        range_loop_asm = """
sum_range_loop:
    push rbp
    mov rbp, rsp
    sub rsp, 48
    call std::vector<int>::begin
    mov QWORD PTR [rbp-16], rax
    call std::vector<int>::end
    mov QWORD PTR [rbp-24], rax
.L2:
    lea rdx, [rbp-24]
    lea rax, [rbp-16]
    call operator!=
    test al, al
    je .L3
    lea rax, [rbp-16]
    call operator*
    mov eax, DWORD PTR [rax]
    add DWORD PTR [rbp-4], eax
    lea rax, [rbp-16]
    call operator++
    jmp .L2
.L3:
    mov eax, DWORD PTR [rbp-4]
    leave
    ret
"""
        
        diff_result = generate_assembly_diff(
            index_loop_asm, 
            range_loop_asm,
            "Index Loop",
            "Range Loop"
        )
        
        stats = diff_result["statistics"]
        
        # Check that index loop uses operator[]
        assert "std::vector<int>::operator[]" in stats["unique_calls_removed"]
        
        # Check that range loop uses iterator methods
        iterator_calls = ["std::vector<int>::begin", "std::vector<int>::end", 
                         "operator!=", "operator*", "operator++"]
        for call in stats["unique_calls_added"]:
            assert any(expected in call for expected in iterator_calls)
        
        # Check instruction differences
        assert "lea" in stats["unique_instructions_added"]  # Range loop uses lea
        assert "test" in stats["unique_instructions_added"]  # Range loop uses test
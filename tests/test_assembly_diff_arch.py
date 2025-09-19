"""Tests for architecture-independent assembly diff functionality."""

from ce_mcp.assembly_diff import (
    extract_function_call,
    extract_instruction,
    generate_assembly_diff,
)


class TestArchitectureIndependence:
    """Test assembly diff works across different architectures."""

    def test_x86_instructions(self):
        """Test x86/x64 instruction extraction."""
        assert extract_instruction("mov eax, 0") == "mov"
        assert extract_instruction("movq %rdi, %rax") == "movq"
        assert extract_instruction("xorps %xmm0, %xmm0") == "xorps"
        assert extract_instruction("vaddps %ymm1, %ymm0, %ymm0") == "vaddps"

    def test_arm_instructions(self):
        """Test ARM instruction extraction."""
        assert extract_instruction("ldr r0, [r1]") == "ldr"
        assert extract_instruction("str r2, [sp, #4]") == "str"
        assert extract_instruction("add.w r3, r3, #1") == "add.w"
        assert extract_instruction("beq.n .L2") == "beq.n"
        assert extract_instruction("bl printf") == "bl"
        assert extract_instruction("movs r0, #0") == "movs"

    def test_riscv_instructions(self):
        """Test RISC-V instruction extraction."""
        assert extract_instruction("addi sp, sp, -16") == "addi"
        assert extract_instruction("sw ra, 12(sp)") == "sw"
        assert extract_instruction("lw a0, 0(a1)") == "lw"
        assert extract_instruction("jal ra, printf") == "jal"
        assert extract_instruction("beqz a0, .L2") == "beqz"

    def test_mips_instructions(self):
        """Test MIPS instruction extraction."""
        assert extract_instruction("addiu $sp, $sp, -32") == "addiu"
        assert extract_instruction("sw $ra, 28($sp)") == "sw"
        assert extract_instruction("lw $t0, 0($a0)") == "lw"
        assert extract_instruction("jal printf") == "jal"
        assert extract_instruction("beq $t0, $zero, .L2") == "beq"

    def test_powerpc_instructions(self):
        """Test PowerPC instruction extraction."""
        assert extract_instruction("stwu 1,-16(1)") == "stwu"
        assert extract_instruction("mflr 0") == "mflr"
        assert extract_instruction("stw 0,20(1)") == "stw"
        assert extract_instruction("bl printf") == "bl"
        assert extract_instruction("cmpwi 0,3,0") == "cmpwi"

    def test_function_calls_across_architectures(self):
        """Test function call extraction for different architectures."""
        # x86/x64
        assert extract_function_call("call printf") == "printf"
        assert extract_function_call("call std::cout::operator<<") == "std::cout::operator<<"
        assert extract_function_call("call QWORD PTR [rax]") == "indirect_call"

        # ARM
        assert extract_function_call("bl printf") == "printf"
        assert extract_function_call("blx r3") == "r3"

        # RISC-V / MIPS
        assert extract_function_call("jal printf") == "printf"
        assert extract_function_call("jalr ra, 0(t0)") == "ra, 0(t0)"

        # PowerPC
        assert extract_function_call("bl __libc_start_main") == "__libc_start_main"

    def test_invalid_instructions(self):
        """Test that non-instructions are not extracted."""
        assert extract_instruction(".L2:") is None  # Label
        assert extract_instruction(".section .text") is None  # Directive
        assert extract_instruction("# Comment") is None  # Comment
        assert extract_instruction("") is None  # Empty line
        assert extract_instruction("verylonginstructionname x, y, z") is None  # Too long

    def test_arm_vs_x86_diff(self):
        """Test comparing ARM and x86 assembly (different compilers)."""
        x86_asm = """
add_numbers:
    push rbp
    mov rbp, rsp
    mov eax, edi
    add eax, esi
    pop rbp
    ret
"""

        arm_asm = """
add_numbers:
    add r0, r0, r1
    bx lr
"""

        diff_result = generate_assembly_diff(x86_asm, arm_asm, "x86-64", "ARM")
        stats = diff_result["statistics"]

        # Check that different instruction sets are detected
        assert "push" in stats["unique_instructions_removed"]
        assert "mov" in stats["unique_instructions_removed"]
        assert "pop" in stats["unique_instructions_removed"]
        assert "ret" in stats["unique_instructions_removed"]

        assert "add" in stats["unique_instructions_added"]  # ARM add is different format
        assert "bx" in stats["unique_instructions_added"]

        # Check summary shows the significant size difference
        assert "4 lines shorter" in diff_result["summary"]

"""Tests for MCP tools."""

import pytest
from unittest.mock import AsyncMock, patch

from ce_mcp.tools import (
    compile_check,
    compile_and_run,
    compile_with_diagnostics,
    analyze_optimization,
    compare_compilers,
    generate_share_url,
)
from ce_mcp.config import Config


class TestTools:
    """Test MCP tool implementations."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()

    @pytest.fixture
    def mock_client(self):
        """Create mock API client."""
        with patch("ce_mcp.tools.CompilerExplorerClient") as mock:
            client_instance = AsyncMock()
            mock.return_value = client_instance
            yield client_instance

    @pytest.mark.asyncio
    async def test_compile_check_success(self, config, mock_client):
        """Test successful compilation check."""
        mock_client.compile.return_value = {
            "code": 0,
            "diagnostics": [
                {"type": "warning", "message": "unused variable"},
            ],
        }

        result = await compile_check(
            {
                "source": "int main() { int unused; return 0; }",
                "language": "c++",
                "compiler": "g++",
                "options": "-Wall",
                "extract_args": False,
            },
            config,
        )

        assert result["success"] is True
        assert result["exit_code"] == 0
        assert result["error_count"] == 0
        assert result["warning_count"] == 1
        assert result["first_error"] is None

    @pytest.mark.asyncio
    async def test_compile_check_with_errors(self, config, mock_client):
        """Test compilation check with errors."""
        mock_client.compile.return_value = {
            "code": 1,
            "diagnostics": [
                {"type": "error", "message": "undeclared identifier 'foo'"},
                {"type": "warning", "message": "unused variable"},
            ],
        }

        result = await compile_check(
            {
                "source": "int main() { foo(); return 0; }",
                "language": "c++",
                "compiler": "g++",
            },
            config,
        )

        assert result["success"] is False
        assert result["exit_code"] == 1
        assert result["error_count"] == 1
        assert result["warning_count"] == 1
        assert result["first_error"] == "undeclared identifier 'foo'"

    @pytest.mark.asyncio
    async def test_compile_and_run_success(self, config, mock_client):
        """Test successful compile and run."""
        mock_client.compile_and_execute.return_value = {
            "buildResult": {"code": 0},
            "didExecute": True,
            "code": 0,
            "stdout": "Hello, World!\n",
            "stderr": "",
            "execTime": 42,
            "truncated": False,
        }

        result = await compile_and_run(
            {
                "source": '#include <stdio.h>\nint main() { printf("Hello, World!\\n"); return 0; }',
                "language": "c",
                "compiler": "gcc",
                "stdin": "",
                "args": [],
                "timeout": 5000,
            },
            config,
        )

        assert result["compiled"] is True
        assert result["executed"] is True
        assert result["exit_code"] == 0
        assert result["stdout"] == "Hello, World!\n"
        assert result["execution_time_ms"] == 42
        assert result["truncated"] is False

    @pytest.mark.asyncio
    async def test_compile_with_diagnostics(self, config, mock_client):
        """Test compilation with diagnostics."""
        mock_client.compile.return_value = {
            "code": 1,
            "stderr": [
                {
                    "text": "error: use of undeclared identifier 'foo'",
                    "line": 5,
                    "column": 8,
                },
                {"text": "warning: unused variable 'bar'", "line": 3, "column": 4},
            ],
        }

        result = await compile_with_diagnostics(
            {
                "source": "int main() { int bar; foo(); return 0; }",
                "language": "c++",
                "compiler": "clang++",
                "diagnostic_level": "verbose",
            },
            config,
        )

        assert result["success"] is False
        assert len(result["diagnostics"]) == 2
        assert result["diagnostics"][0]["type"] == "error"
        assert result["diagnostics"][0]["line"] == 5
        assert result["diagnostics"][1]["type"] == "warning"
        assert "clang1700" in result["command"]

    @pytest.mark.asyncio
    async def test_analyze_optimization(self, config, mock_client):
        """Test optimization analysis."""
        mock_client.compile.return_value = {
            "code": 0,
            "asm": "main:\n\tmovdqu\t%xmm0, %xmm1\n\tcall\tmemcpy\n\tret",
        }

        result = await analyze_optimization(
            {
                "source": "int main() { /* loop code */ return 0; }",
                "language": "c++",
                "compiler": "g++",
                "optimization_level": "-O3",
                "analysis_type": "all",
            },
            config,
        )

        assert "assembly_lines" in result
        assert "instruction_count" in result
        assert "assembly_output" in result
        assert "truncated" in result
        assert "total_instructions" in result
        assert result["assembly_lines"] == 4

    @pytest.mark.asyncio
    async def test_compare_compilers(self, config, mock_client):
        """Test compiler comparison."""
        # Mock responses for different compilers
        mock_client.compile.side_effect = [
            {"code": 0, "asm": "asm line 1\nasm line 2", "stderr": []},
            {
                "code": 0,
                "asm": "asm line 1",
                "stderr": [{"text": "warning: something"}],
            },
        ]

        result = await compare_compilers(
            {
                "source": "int main() { return 0; }",
                "language": "c++",
                "compilers": [
                    {"id": "g++", "options": "-O3"},
                    {"id": "clang++", "options": "-O3"},
                ],
                "comparison_type": "assembly",
            },
            config,
        )

        assert len(result["results"]) == 2
        assert result["results"][0]["compiler"] == "g132"  # Resolved from g++
        assert result["results"][0]["assembly_size"] == 2
        assert result["results"][1]["assembly_size"] == 1
        assert len(result["differences"]) > 0

    @pytest.mark.asyncio
    async def test_generate_share_url(self, config, mock_client):
        """Test share URL generation."""
        mock_client.create_short_link.return_value = "https://godbolt.org/z/abc123"

        result = await generate_share_url(
            {
                "source": "int main() { return 0; }",
                "language": "c++",
                "compiler": "g++",
                "options": "-O2",
                "layout": "simple",
            },
            config,
        )

        assert result["url"] == "https://godbolt.org/z/abc123"
        assert result["short_url"] == "https://godbolt.org/z/abc123"
        assert result["configuration"]["compiler"] == "g132"
        assert result["configuration"]["options"] == "-O2"

    @pytest.mark.asyncio
    async def test_compile_check_with_arg_extraction(self, config, mock_client):
        """Test compile check with argument extraction."""
        mock_client.compile.return_value = {"code": 0, "diagnostics": []}

        source_with_args = """// compile: -std=c++17 -O2
int main() { return 0; }"""

        await compile_check(
            {
                "source": source_with_args,
                "language": "c++",
                "compiler": "g++",
                "options": "-Wall",
                "extract_args": True,
            },
            config,
        )

        # Verify compile was called with extracted args
        mock_client.compile.assert_called_once()
        call_args = mock_client.compile.call_args
        # Check positional args (call_args[0]) instead of keyword args
        assert len(call_args[0]) >= 4  # source, language, compiler, options
        options_arg = call_args[0][3]  # 4th positional argument should be options
        assert "-std=c++17 -O2" in options_arg

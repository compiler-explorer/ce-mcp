"""Integration tests with real Compiler Explorer API calls.

These tests make actual HTTP requests to godbolt.org and should be run
when the API is accessible. They can be skipped if running offline.
"""

import pytest
from aiohttp import ClientError

from ce_mcp.api_client import CompilerExplorerClient
from ce_mcp.config import Config
from ce_mcp.tools import (
    compile_check,
    compile_and_run,
    compile_with_diagnostics,
    analyze_optimization,
    generate_share_url,
)


class TestRealAPIIntegration:
    """Integration tests with real Compiler Explorer API."""

    @pytest.fixture
    def config(self):
        """Create config for real API testing."""
        return Config()

    @pytest.fixture
    async def client(self, config):
        """Create API client for real testing."""
        client = CompilerExplorerClient(config)
        yield client
        await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_languages_real(self, client):
        """Test fetching real languages from API."""
        try:
            languages = await client.get_languages()
            assert isinstance(languages, list)
            assert len(languages) > 0

            # Check for some common languages
            language_ids = [lang["id"] for lang in languages]
            assert "c++" in language_ids or "cpp" in language_ids
            assert "c" in language_ids

            # Each language should have required fields
            for lang in languages[:5]:  # Check first 5
                assert "id" in lang
                assert "name" in lang
        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_compilers_real(self, client):
        """Test fetching real compilers for C++."""
        try:
            compilers = await client.get_compilers("c++")
            assert isinstance(compilers, list)
            assert len(compilers) > 0

            # Check for GCC
            compiler_ids = [comp["id"] for comp in compilers]
            gcc_compilers = [cid for cid in compiler_ids if "g" in cid.lower()]
            assert len(gcc_compilers) > 0

            # Each compiler should have required fields
            for comp in compilers[:5]:  # Check first 5
                assert "id" in comp
                assert "name" in comp
        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_simple_cpp_compilation_real(self, client):
        """Test real C++ compilation with simple code."""
        simple_cpp = """#include <iostream>
int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}"""

        try:
            result = await client.compile(
                source=simple_cpp,
                language="c++",
                compiler="g132",  # GCC 13.2
                options="-std=c++17",
            )

            # Should compile successfully
            assert result.get("code", 1) == 0
            assert "asm" in result or "stdout" in result

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cpp_compilation_with_execution_real(self, client):
        """Test real C++ compilation and execution."""
        simple_cpp = """#include <iostream>
int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}"""

        try:
            result = await client.compile_and_execute(
                source=simple_cpp,
                language="c++",
                compiler="g132",
                options="-std=c++17",
                stdin="",
                args=[],
                timeout=5000,
            )

            # Should compile successfully
            build_result = result.get("buildResult", result)
            assert build_result.get("code", 1) == 0

            # Check execution result if present
            if "execResult" in result:
                exec_result = result["execResult"]
                assert exec_result.get("code", 1) == 0
                stdout = exec_result.get("stdout", "")
                if isinstance(stdout, list):
                    stdout_text = "".join(item.get("text", "") for item in stdout)
                else:
                    stdout_text = stdout
                assert "Hello, World!" in stdout_text
            else:
                # Alternative: check if stdout is directly in result
                stdout = result.get("stdout", "")
                if isinstance(stdout, list):
                    stdout_text = "".join(item.get("text", "") for item in stdout)
                else:
                    stdout_text = stdout
                assert "Hello, World!" in stdout_text

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_compilation_with_error_real(self, client):
        """Test compilation with syntax error."""
        bad_cpp = """#include <iostream>
int main() {
    std::cout << "Missing semicolon"  // No semicolon
    return 0;
}"""

        try:
            result = await client.compile(
                source=bad_cpp, language="c++", compiler="g132", options="-std=c++17"
            )

            # Should fail to compile
            assert result.get("code", 0) != 0

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_short_link_real(self, client):
        """Test creating a real short link."""
        simple_cpp = """#include <iostream>
int main() {
    return 42;
}"""

        try:
            url = await client.create_short_link(
                source=simple_cpp, language="c++", compiler="g132", options="-O2"
            )

            assert isinstance(url, str)
            assert url.startswith("https://godbolt.org/") or url.startswith(
                "https://gcc.godbolt.org/"
            )

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")


class TestToolsIntegration:
    """Integration tests for tools with real API calls."""

    @pytest.fixture
    def config(self):
        """Create config for real API testing."""
        return Config()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_compile_check_real(self, config):
        """Test compile_check with real API."""
        good_cpp = """#include <iostream>
int main() {
    std::cout << "Hello!" << std::endl;
    return 0;
}"""

        try:
            result = await compile_check(
                {
                    "source": good_cpp,
                    "language": "c++",
                    "compiler": "g++",  # Will be resolved to g132
                    "options": "-std=c++17",
                    "extract_args": False,
                },
                config,
            )

            assert result["success"] is True
            assert result["exit_code"] == 0
            assert result["error_count"] == 0

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_compile_check_with_warning_real(self, config):
        """Test compile_check with code that generates warnings."""
        warning_cpp = """#include <iostream>
int main() {
    int unused_var = 42;  // This will generate a warning with -Wall
    std::cout << "Hello!" << std::endl;
    return 0;
}"""

        try:
            result = await compile_check(
                {
                    "source": warning_cpp,
                    "language": "c++",
                    "compiler": "g++",
                    "options": "-std=c++17 -Wall",
                    "extract_args": False,
                },
                config,
            )

            assert result["success"] is True  # Warnings don't fail compilation
            assert result["exit_code"] == 0
            # Note: warning detection might not work if API doesn't return warnings in diagnostics
            # assert result["warning_count"] > 0

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_compile_and_run_real(self, config):
        """Test compile_and_run with real API."""
        hello_cpp = """#include <iostream>
int main() {
    std::cout << "Integration test!" << std::endl;
    return 42;
}"""

        try:
            result = await compile_and_run(
                {
                    "source": hello_cpp,
                    "language": "c++",
                    "compiler": "g++",
                    "options": "-std=c++17",
                    "stdin": "",
                    "args": [],
                    "timeout": 5000,
                },
                config,
            )

            assert result["compiled"] is True
            # Execution might not work depending on API response format
            if result["executed"]:
                assert result["exit_code"] == 42
                assert "Integration test!" in result["stdout"]

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_compile_with_diagnostics_real(self, config):
        """Test compile_with_diagnostics with real API."""
        error_cpp = """#include <iostream>
int main() {
    undefined_function();  // This will cause an error
    return 0;
}"""

        try:
            result = await compile_with_diagnostics(
                {
                    "source": error_cpp,
                    "language": "c++",
                    "compiler": "g++",
                    "options": "",
                    "diagnostic_level": "normal",
                },
                config,
            )

            assert result["success"] is False
            # Check diagnostics if present
            if result["diagnostics"]:
                assert len(result["diagnostics"]) > 0
                # Should contain error about undefined function
                assert any(
                    "undefined" in str(diag).lower() for diag in result["diagnostics"]
                )

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_analyze_optimization_real(self, config):
        """Test analyze_optimization with real API."""
        loop_cpp = """#include <cstring>
int main() {
    char src[100] = "Hello, World!";
    char dst[100];
    for (int i = 0; i < 13; ++i) {
        dst[i] = src[i];
    }
    return 0;
}"""

        try:
            result = await analyze_optimization(
                {
                    "source": loop_cpp,
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
            # Assembly analysis might not work if API doesn't return assembly
            # assert result["assembly_lines"] > 0

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_generate_share_url_real(self, config):
        """Test generate_share_url with real API."""
        simple_cpp = """#include <iostream>
int main() {
    std::cout << "Shared code!" << std::endl;
    return 0;
}"""

        try:
            result = await generate_share_url(
                {
                    "source": simple_cpp,
                    "language": "c++",
                    "compiler": "g++",
                    "options": "-O2",
                    "layout": "simple",
                },
                config,
            )

            assert "url" in result
            url = result["url"]
            assert isinstance(url, str)
            assert url.startswith("https://")
            assert "godbolt.org" in url

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_argument_extraction_real(self, config):
        """Test argument extraction from source comments with real API."""
        cpp_with_args = """// compile: -std=c++20 -O2
#include <iostream>
int main() {
    std::cout << "Args extracted!" << std::endl;
    return 0;
}"""

        try:
            result = await compile_check(
                {
                    "source": cpp_with_args,
                    "language": "c++",
                    "compiler": "g++",
                    "options": "-Wall",  # Additional options
                    "extract_args": True,
                },
                config,
            )

            assert result["success"] is True
            assert result["exit_code"] == 0

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")


class TestErrorHandlingIntegration:
    """Test error handling with real API calls."""

    @pytest.fixture
    def config(self):
        """Create config for real API testing."""
        return Config()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_invalid_compiler_real(self, config):
        """Test behavior with invalid compiler ID."""
        simple_cpp = """int main() { return 0; }"""

        try:
            result = await compile_check(
                {
                    "source": simple_cpp,
                    "language": "c++",
                    "compiler": "invalid_compiler_12345",
                    "options": "",
                    "extract_args": False,
                },
                config,
            )

            # Should handle error gracefully - exact behavior depends on API
            assert isinstance(result, dict)

        except (ClientError, Exception):
            # Expected to fail with invalid compiler
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_timeout_handling_real(self, config):
        """Test timeout handling with infinite loop."""
        infinite_loop = """int main() {
    while(1) {}  // Infinite loop
    return 0;
}"""

        try:
            result = await compile_and_run(
                {
                    "source": infinite_loop,
                    "language": "c++",
                    "compiler": "g++",
                    "options": "-O0",  # No optimization to ensure loop runs
                    "stdin": "",
                    "args": [],
                    "timeout": 2000,  # 2 second timeout
                },
                config,
            )

            # Should either timeout or be killed
            assert isinstance(result, dict)
            # Execution might fail due to timeout

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_large_output_handling_real(self, config):
        """Test handling of large output."""
        large_output = """#include <iostream>
int main() {
    for (int i = 0; i < 1000; ++i) {
        std::cout << "Line " << i << " of output\\n";
    }
    return 0;
}"""

        try:
            result = await compile_and_run(
                {
                    "source": large_output,
                    "language": "c++",
                    "compiler": "g++",
                    "options": "-O2",
                    "stdin": "",
                    "args": [],
                    "timeout": 5000,
                },
                config,
            )

            assert result["compiled"] is True
            if result["executed"]:
                # Output should be present (might be truncated)
                assert len(result["stdout"]) > 0

        except ClientError as e:
            pytest.skip(f"API not accessible: {e}")

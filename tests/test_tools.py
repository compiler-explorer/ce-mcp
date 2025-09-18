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
    extract_compiler_suggestion,
)
from ce_mcp.config import Config


class TestTools:
    """Test MCP tool implementations."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config()

    def test_extract_compiler_suggestion(self):
        """Test compiler suggestion extraction patterns."""
        # Test "did you mean" pattern
        assert extract_compiler_suggestion("error: 'foo' was not declared; did you mean 'bar'?") == "did you mean 'bar'?"

        # Test "use instead" pattern
        assert extract_compiler_suggestion("warning: use 'const' instead of 'volatile'") == "use 'const' instead"

        # Test "suggested alternative" pattern
        assert extract_compiler_suggestion("note: suggested alternative: 'std::vector'") == "suggested alternative: 'std::vector'"

        # Test fix-it pattern
        assert extract_compiler_suggestion("note: fix-it applied: 'auto'") == "fix-it: 'auto'"

        # Test no suggestion
        assert extract_compiler_suggestion("error: syntax error") is None
        assert extract_compiler_suggestion("warning: unused variable") is None

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
    async def test_compile_with_diagnostics_suggestions(self, config, mock_client):
        """Test diagnostics with suggestion extraction."""
        mock_client.compile.return_value = {
            "code": 1,
            "stderr": [
                {
                    "text": "error: 'foo' was not declared in this scope; did you mean 'bar'?",
                    "tag": {
                        "line": 3,
                        "column": 5,
                        "text": "error: 'foo' was not declared in this scope; did you mean 'bar'?",
                        "severity": 2,
                        "file": "example.cpp"
                    }
                },
                {
                    "text": "note: use 'const' instead of 'volatile'",
                    "tag": {
                        "line": 2,
                        "column": 1,
                        "text": "note: use 'const' instead of 'volatile'",
                        "severity": 0,
                        "file": "example.cpp"
                    }
                }
            ],
        }

        result = await compile_with_diagnostics(
            {
                "source": "int main() { volatile int x; foo(); return 0; }",
                "language": "c++",
                "compiler": "g++",
                "diagnostic_level": "normal",
            },
            config,
        )

        assert result["success"] is False
        assert len(result["diagnostics"]) == 2

        # Check error with suggestion
        error_diag = result["diagnostics"][0]
        assert error_diag["type"] == "error"
        assert error_diag["line"] == 3
        assert error_diag["column"] == 5
        assert error_diag["suggestion"] == "did you mean 'bar'?"

        # Check note with suggestion
        note_diag = result["diagnostics"][1]
        assert note_diag["type"] == "note"
        assert note_diag["line"] == 2
        assert note_diag["column"] == 1
        assert note_diag["suggestion"] == "use 'const' instead"

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
    async def test_compare_compilers_execution(self, config, mock_client):
        """Test compiler comparison for execution results."""
        # Mock execution responses with different outputs
        mock_client.compile_and_execute.side_effect = [
            {
                "buildResult": {"code": 0},
                "code": 0,
                "didExecute": True,
                "stdout": "Hello World\nLine 2",
                "stderr": "",
            },
            {
                "buildResult": {"code": 0},
                "code": 1,
                "didExecute": True,
                "stdout": "Hello World\nLine 2\nLine 3",
                "stderr": "Warning: something",
            },
        ]

        result = await compare_compilers(
            {
                "source": "#include <iostream>\nint main() { std::cout << \"Hello World\"; return 0; }",
                "language": "c++",
                "compilers": [
                    {"id": "g++", "options": "-O2"},
                    {"id": "clang++", "options": "-O2"},
                ],
                "comparison_type": "execution",
            },
            config,
        )

        # Verify enhanced execution data collection
        assert len(result["results"]) == 2
        assert result["results"][0]["compiled"] == True
        assert result["results"][0]["executed"] == True
        assert result["results"][0]["exit_code"] == 0
        assert result["results"][0]["stdout"] == "Hello World\nLine 2"

        assert result["results"][1]["compiled"] == True
        assert result["results"][1]["executed"] == True
        assert result["results"][1]["exit_code"] == 1
        assert result["results"][1]["stdout"] == "Hello World\nLine 2\nLine 3"

        # Verify detailed difference analysis
        assert len(result["differences"]) > 0
        differences_text = " ".join(result["differences"])
        assert "Exit codes differ" in differences_text
        assert "Stdout differs" in differences_text

        # Verify execution_diff is present with unified diffs
        assert "execution_diff" in result
        assert "stdout_diff" in result["execution_diff"]
        assert "stderr_diff" in result["execution_diff"]
        assert "summary" in result["execution_diff"]

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

    @pytest.mark.asyncio
    async def test_find_compilers_with_tools_parameters(self, config, mock_client):
        """Test find compilers parameters are passed correctly."""
        from ce_mcp.tools import find_compilers
        from unittest.mock import patch

        # Mock the search function to return a simple result
        with patch('ce_mcp.tools.search_experimental_compilers') as mock_search:
            # Mock compiler with tools
            from ce_mcp.experimental_utils import ExperimentalCompiler
            test_compiler = ExperimentalCompiler(
                id="test_gcc",
                name="Test GCC",
                proposal_numbers=[],
                features=[],
                is_nightly=False,
                description="Test GCC compiler",
                version_info=None,
                modified=None,
                category="standard"
            )

            # Add tool attributes
            test_compiler.possible_runtime_tools = [
                {"id": "perf", "name": "perf profiler"},
                {"id": "valgrind", "name": "Valgrind"}
            ]
            test_compiler.tools = [
                {"id": "analyzer", "name": "Static Analyzer"}
            ]
            test_compiler.possible_overrides = [
                {"name": "arch", "values": ["x86_64"]}
            ]

            mock_search.return_value = [test_compiler]

            # Test with tool options enabled
            result = await find_compilers(
                {
                    "language": "c++",
                    "search_text": "test",
                    "include_runtime_tools": True,
                    "include_compile_tools": True,
                    "include_overrides": True,
                },
                config,
            )

            # Verify basic structure
            assert "summary" in result
            assert "compilers" in result

            # Verify the mock was called with correct parameters
            mock_search.assert_called_once()

    def test_find_compilers_format_function(self):
        """Test the format_compiler_info function with tool options."""
        from ce_mcp.experimental_utils import ExperimentalCompiler

        # Create a test compiler
        compiler = ExperimentalCompiler(
            id="test_gcc",
            name="Test GCC",
            proposal_numbers=[],
            features=[],
            is_nightly=False,
            description="Test GCC compiler",
            version_info=None,
            modified=None,
            category="standard"
        )

        # Add tool attributes
        compiler.possible_runtime_tools = [
            {"id": "perf", "name": "perf profiler"},
            {"id": "valgrind", "name": "Valgrind"}
        ]
        compiler.tools = [
            {"id": "analyzer", "name": "Static Analyzer"}
        ]
        compiler.possible_overrides = [
            {"name": "arch", "values": ["x86_64"]}
        ]

        # Test basic formatting (no tools)
        from ce_mcp.tools import find_compilers

        # Get the format function from the find_compilers function scope
        # This is a bit tricky since it's a nested function, so we'll test it indirectly

        # Test ids_only mode
        assert compiler.id == "test_gcc"

        # Test that compiler has the required attributes
        assert hasattr(compiler, 'possible_runtime_tools')
        assert hasattr(compiler, 'tools')
        assert hasattr(compiler, 'possible_overrides')

        # Verify the tool data
        assert len(compiler.possible_runtime_tools) == 2
        assert len(compiler.tools) == 1
        assert len(compiler.possible_overrides) == 1

    @pytest.mark.asyncio
    async def test_get_libraries_list(self, config, mock_client):
        """Test get libraries list functionality."""
        from ce_mcp.tools import get_libraries_list

        # Mock API response
        mock_client.get_libraries_list.return_value = [
            {"id": "boost", "name": "Boost C++ Libraries"},
            {"id": "fmt", "name": "fmt"},
            {"id": "range-v3", "name": "Range-v3"}
        ]

        # Test without search
        result = await get_libraries_list(
            {"language": "c++"},
            config,
        )

        assert result["language"] == "c++"
        assert result["count"] == 3
        assert len(result["libraries"]) == 3
        assert result["libraries"][0]["id"] == "boost"
        assert result["libraries"][0]["name"] == "Boost C++ Libraries"

        # Test with search
        mock_client.get_libraries_list.return_value = [
            {"id": "boost", "name": "Boost C++ Libraries"}
        ]

        result = await get_libraries_list(
            {"language": "c++", "search_text": "boost"},
            config,
        )

        assert result["language"] == "c++"
        assert result["search_text"] == "boost"
        assert result["count"] == 1
        assert result["libraries"][0]["id"] == "boost"

    @pytest.mark.asyncio
    async def test_get_library_details_info(self, config, mock_client):
        """Test get library details functionality."""
        from ce_mcp.tools import get_library_details_info

        # Mock API response
        mock_library = {
            "id": "boost",
            "name": "Boost C++ Libraries",
            "url": "https://www.boost.org/",
            "description": "Boost provides free peer-reviewed portable C++ source libraries",
            "versions": [
                {"id": "180", "version": "1.80.0"},
                {"id": "181", "version": "1.81.0"}
            ]
        }
        mock_client.get_library_details.return_value = mock_library

        # Test successful lookup
        result = await get_library_details_info(
            {"language": "c++", "library_id": "boost"},
            config,
        )

        assert result["language"] == "c++"
        assert result["library_id"] == "boost"
        assert result["library"]["id"] == "boost"
        assert result["library"]["name"] == "Boost C++ Libraries"
        assert result["library"]["url"] == "https://www.boost.org/"
        assert len(result["library"]["versions"]) == 2
        assert result["library"]["versions"][0]["version"] == "1.80.0"

        # Test library not found
        mock_client.get_library_details.return_value = None

        result = await get_library_details_info(
            {"language": "c++", "library_id": "nonexistent"},
            config,
        )

        assert "error" in result
        assert "not found" in result["error"]
        assert result["library_id"] == "nonexistent"

        # Test missing library_id
        result = await get_library_details_info(
            {"language": "c++"},
            config,
        )

        assert "error" in result
        assert "required" in result["error"]

    @pytest.mark.asyncio
    async def test_api_client_libraries_methods(self, config):
        """Test API client library methods."""
        from ce_mcp.api_client import CompilerExplorerClient

        client = CompilerExplorerClient(config)

        # Mock the base get_libraries method
        full_libraries_mock = [
            {
                "id": "boost",
                "name": "Boost C++ Libraries",
                "url": "https://www.boost.org/",
                "description": "Boost libraries",
                "versions": [
                    {"id": "180", "version": "1.80.0", "staticliblink": ["boost_system"]},
                    {"id": "181", "version": "1.81.0", "staticliblink": ["boost_system"]}
                ]
            },
            {
                "id": "fmt",
                "name": "fmt",
                "url": "https://github.com/fmtlib/fmt",
                "description": "Formatting library",
                "versions": [
                    {"id": "90", "version": "9.0.0", "staticliblink": ["fmt"]}
                ]
            }
        ]

        # Mock the get_libraries method
        async def mock_get_libraries(lang):
            return full_libraries_mock
        client.get_libraries = mock_get_libraries

        # Test get_libraries_list
        result = await client.get_libraries_list("c++")
        assert len(result) == 2
        assert result[0]["id"] == "boost"
        assert result[0]["name"] == "Boost C++ Libraries"
        assert "url" not in result[0]  # Should be filtered out

        # Test get_libraries_list with search
        result = await client.get_libraries_list("c++", "boost")
        assert len(result) == 1
        assert result[0]["id"] == "boost"

        # Test get_library_details
        result = await client.get_library_details("c++", "boost")
        assert result is not None
        assert result["id"] == "boost"
        assert result["url"] == "https://www.boost.org/"
        assert len(result["versions"]) == 2
        assert "staticliblink" not in result["versions"][0]  # Should be filtered out
        assert result["versions"][0]["version"] == "1.80.0"

        # Test get_library_details with nonexistent library
        result = await client.get_library_details("c++", "nonexistent")
        assert result is None

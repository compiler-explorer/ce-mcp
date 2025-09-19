"""Tests for MCP server."""

import pytest

from ce_mcp.config import Config
from ce_mcp.server import create_server, mcp


class TestCompilerExplorerMCP:
    """Test MCP server initialization and setup."""

    def test_server_creation(self):
        """Test server can be created."""
        server = create_server()
        assert server.name == "ce-mcp"

    def test_server_with_custom_config(self):
        """Test server with custom configuration."""
        config = Config()
        config.defaults.language = "rust"
        server = create_server(config)
        assert server.name == "ce-mcp"

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test all tools are registered correctly."""
        # Check all 11 tools are registered
        expected_tools = [
            "compile_check_tool",
            "compile_and_run_tool",
            "compile_with_diagnostics_tool",
            "analyze_optimization_tool",
            "compare_compilers_tool",
            "generate_share_url_tool",
            "find_compilers_tool",
            "get_libraries_tool",
            "get_library_details_tool",
            "get_languages_tool",
            "download_shortlink_tool",
        ]

        # Get tools from FastMCP server
        registered_tools = await mcp.list_tools()
        tool_names = [tool.name for tool in registered_tools]

        for tool_name in expected_tools:
            assert tool_name in tool_names

    def test_tool_functions_exist(self):
        """Test tool functions are properly defined."""
        from ce_mcp.server import (
            analyze_optimization_tool,
            compare_compilers_tool,
            compile_and_run_tool,
            compile_check_tool,
            compile_with_diagnostics_tool,
            download_shortlink_tool,
            find_compilers_tool,
            generate_share_url_tool,
            get_languages_tool,
            get_libraries_tool,
            get_library_details_tool,
        )

        # Check functions exist and are callable
        assert callable(compile_check_tool)
        assert callable(compile_and_run_tool)
        assert callable(compile_with_diagnostics_tool)
        assert callable(analyze_optimization_tool)
        assert callable(compare_compilers_tool)
        assert callable(generate_share_url_tool)
        assert callable(find_compilers_tool)
        assert callable(get_libraries_tool)
        assert callable(get_library_details_tool)
        assert callable(get_languages_tool)
        assert callable(download_shortlink_tool)

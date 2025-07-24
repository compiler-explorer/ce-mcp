"""Tests for API client."""

import pytest
from aioresponses import aioresponses

from ce_mcp.api_client import CompilerExplorerClient
from ce_mcp.config import Config


class TestCompilerExplorerClient:
    """Test API client functionality."""

    @pytest.fixture
    def client(self):
        """Create API client with default config."""
        config = Config()
        return CompilerExplorerClient(config)

    @pytest.fixture
    def mock_api(self):
        """Create mock API responses."""
        with aioresponses() as m:
            yield m

    @pytest.mark.asyncio
    async def test_compile_request(self, client, mock_api):
        """Test basic compilation request."""
        # Mock successful compilation
        mock_api.post(
            "https://godbolt.org/api/compiler/g132/compile",
            payload={
                "code": 0,
                "stdout": [],
                "stderr": [],
                "asm": [{"text": "main:"}],
            },
        )

        result = await client.compile(
            source="int main() { return 0; }",
            language="c++",
            compiler="g132",
            options="-O2",
        )

        assert result["code"] == 0
        assert "asm" in result

        # Verify request was made
        assert len(mock_api.requests) == 1

    @pytest.mark.asyncio
    async def test_compile_with_execution(self, client, mock_api):
        """Test compilation with execution."""
        mock_api.post(
            "https://godbolt.org/api/compiler/g132/compile",
            payload={
                "code": 0,
                "buildResult": {"code": 0},
                "execResult": {
                    "code": 0,
                    "stdout": "Hello, World!\n",
                    "stderr": "",
                    "execTime": 42,
                },
            },
        )

        result = await client.compile_and_execute(
            source='#include <stdio.h>\nint main() { printf("Hello, World!\\n"); return 0; }',
            language="c",
            compiler="g132",
            stdin="",
            args=[],
            timeout=5000,
        )

        assert result["buildResult"]["code"] == 0
        assert result["execResult"]["stdout"] == "Hello, World!\n"
        assert result["execResult"]["execTime"] == 42

    @pytest.mark.asyncio
    async def test_get_languages(self, client, mock_api):
        """Test fetching supported languages."""
        mock_api.get(
            "https://godbolt.org/api/languages",
            payload=[
                {"id": "c++", "name": "C++"},
                {"id": "c", "name": "C"},
                {"id": "rust", "name": "Rust"},
            ],
        )

        languages = await client.get_languages()
        assert len(languages) == 3
        assert languages[0]["id"] == "c++"

    @pytest.mark.asyncio
    async def test_get_compilers(self, client, mock_api):
        """Test fetching compilers for a language."""
        mock_api.get(
            "https://godbolt.org/api/compilers/c++",
            payload=[
                {"id": "g132", "name": "GCC 13.2"},
                {"id": "clang1700", "name": "Clang 17.0"},
            ],
        )

        compilers = await client.get_compilers("c++")
        assert len(compilers) == 2
        assert compilers[0]["id"] == "g132"

    @pytest.mark.asyncio
    async def test_create_short_link(self, client, mock_api):
        """Test creating a short link."""
        mock_api.post(
            "https://godbolt.org/api/shortener",
            payload={"url": "https://godbolt.org/z/abc123"},
        )

        url = await client.create_short_link(
            source="int main() { return 0; }",
            language="c++",
            compiler="g132",
            options="-O2",
        )

        assert url == "https://godbolt.org/z/abc123"

    @pytest.mark.asyncio
    async def test_session_cleanup(self, client):
        """Test session is properly cleaned up."""
        # Make a request to create session
        with aioresponses() as m:
            m.get("https://godbolt.org/api/languages", payload=[])
            await client.get_languages()
            assert client.session is not None

        # Close session
        await client.close()
        assert client.session is None

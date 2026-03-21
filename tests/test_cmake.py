"""Tests for CMake build tool."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from ce_mcp.config import Config
from ce_mcp.tools import (
    _extract_build_step_text,
    _resolve_cmake_inputs,
    _strip_ansi,
    cmake_build,
    generate_cmake_share_url,
)


class TestCmakeBuild:
    """Test CMake build tool implementation."""

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def mock_client(self):
        with patch("ce_mcp.tools.CompilerExplorerClient") as mock:
            client_instance = AsyncMock()
            mock.return_value = client_instance
            yield client_instance

    @pytest.mark.asyncio
    async def test_cmake_build_success(self, config, mock_client):
        """Test successful cmake build without execution."""
        mock_client.cmake_build.return_value = {
            "code": 0,
            "buildsteps": [
                {
                    "step": "cmake",
                    "code": 0,
                    "stdout": [{"text": "-- Configuring done"}],
                    "stderr": [],
                },
                {
                    "step": "build",
                    "code": 0,
                    "stdout": [{"text": "[100%] Built target output.s"}],
                    "stderr": [],
                },
            ],
            "result": {"code": 0},
        }

        result = await cmake_build(
            {
                "cmake_source": "cmake_minimum_required(VERSION 3.10)\nproject(test)\nadd_executable(output.s main.cpp)",
                "files": [{"filename": "main.cpp", "contents": "int main() { return 0; }"}],
                "compiler": "g++",
            },
            config,
        )

        assert result["success"] is True
        assert len(result["build_steps"]) == 2
        assert result["build_steps"][0]["step"] == "cmake"
        assert result["build_steps"][0]["code"] == 0
        assert result["build_steps"][1]["step"] == "build"
        assert result["build_steps"][1]["code"] == 0
        assert "executed" not in result

    @pytest.mark.asyncio
    async def test_cmake_build_with_execution(self, config, mock_client):
        """Test cmake build with execution."""
        mock_client.cmake_build.return_value = {
            "code": 0,
            "buildsteps": [
                {"step": "cmake", "code": 0, "stdout": [], "stderr": []},
                {"step": "build", "code": 0, "stdout": [], "stderr": []},
            ],
            "result": {"code": 0},
            "didExecute": True,
            "execResult": {
                "code": 0,
                "stdout": [{"text": "Hello from CMake!"}],
                "stderr": [],
                "execTime": 15,
            },
        }

        result = await cmake_build(
            {
                "cmake_source": "cmake_minimum_required(VERSION 3.10)\nproject(test)\nadd_executable(output.s main.cpp)",
                "files": [
                    {
                        "filename": "main.cpp",
                        "contents": '#include <cstdio>\nint main() { printf("Hello from CMake!"); }',
                    }
                ],
                "compiler": "g++",
                "execute": True,
            },
            config,
        )

        assert result["success"] is True
        assert result["executed"] is True
        assert result["exit_code"] == 0
        assert result["stdout"] == "Hello from CMake!"
        assert result["execution_time_ms"] == 15

    @pytest.mark.asyncio
    async def test_cmake_configure_failure(self, config, mock_client):
        """Test cmake configure failure."""
        mock_client.cmake_build.return_value = {
            "code": 0,
            "buildsteps": [
                {
                    "step": "cmake",
                    "code": 1,
                    "stdout": [],
                    "stderr": [
                        {"text": "CMake Error: The source directory does not appear to contain CMakeLists.txt."}
                    ],
                },
            ],
            "result": {"code": 1},
        }

        result = await cmake_build(
            {
                "cmake_source": "invalid cmake",
                "files": [{"filename": "main.cpp", "contents": "int main() {}"}],
                "compiler": "g++",
            },
            config,
        )

        assert result["success"] is False
        assert result["build_steps"][0]["code"] == 1
        assert "CMake Error" in result["build_steps"][0]["stderr"]

    @pytest.mark.asyncio
    async def test_cmake_compile_error(self, config, mock_client):
        """Test compile error in build step."""
        mock_client.cmake_build.return_value = {
            "code": 0,
            "buildsteps": [
                {"step": "cmake", "code": 0, "stdout": [], "stderr": []},
                {
                    "step": "build",
                    "code": 2,
                    "stdout": [],
                    "stderr": [{"text": "error: 'foo' was not declared in this scope"}],
                },
            ],
            "result": {"code": 2},
        }

        result = await cmake_build(
            {
                "cmake_source": "cmake_minimum_required(VERSION 3.10)\nproject(test)\nadd_executable(output.s main.cpp)",
                "files": [{"filename": "main.cpp", "contents": "int main() { foo(); }"}],
                "compiler": "g++",
            },
            config,
        )

        assert result["success"] is False
        assert result["build_steps"][0]["code"] == 0
        assert result["build_steps"][1]["code"] == 2
        assert "not declared" in result["build_steps"][1]["stderr"]

    @pytest.mark.asyncio
    async def test_cmake_build_multifile(self, config, mock_client):
        """Test multifile cmake build."""
        mock_client.cmake_build.return_value = {
            "code": 0,
            "buildsteps": [
                {"step": "cmake", "code": 0, "stdout": [], "stderr": []},
                {"step": "build", "code": 0, "stdout": [], "stderr": []},
            ],
            "result": {"code": 0},
            "didExecute": True,
            "execResult": {
                "code": 0,
                "stdout": [{"text": "3"}],
                "stderr": [],
                "execTime": 10,
            },
        }

        result = await cmake_build(
            {
                "cmake_source": "cmake_minimum_required(VERSION 3.10)\nproject(test)\nadd_executable(output.s main.cpp math.cpp)",
                "files": [
                    {
                        "filename": "main.cpp",
                        "contents": '#include "math.h"\n#include <cstdio>\nint main() { printf("%d", add(1,2)); }',
                    },
                    {"filename": "math.cpp", "contents": '#include "math.h"\nint add(int a, int b) { return a + b; }'},
                    {"filename": "math.h", "contents": "#pragma once\nint add(int a, int b);"},
                ],
                "compiler": "g++",
                "execute": True,
            },
            config,
        )

        assert result["success"] is True
        assert result["executed"] is True
        assert result["stdout"] == "3"

    @pytest.mark.asyncio
    async def test_cmake_build_with_cmake_args(self, config, mock_client):
        """Test cmake build passes cmake_args correctly."""
        mock_client.cmake_build.return_value = {
            "code": 0,
            "buildsteps": [
                {"step": "cmake", "code": 0, "stdout": [], "stderr": []},
                {"step": "build", "code": 0, "stdout": [], "stderr": []},
            ],
            "result": {"code": 0},
        }

        await cmake_build(
            {
                "cmake_source": "cmake_minimum_required(VERSION 3.10)\nproject(test)\nadd_executable(output.s main.cpp)",
                "files": [{"filename": "main.cpp", "contents": "int main() {}"}],
                "compiler": "g++",
                "cmake_args": "-DCMAKE_BUILD_TYPE=Release",
                "options": "-O2",
            },
            config,
        )

        mock_client.cmake_build.assert_called_once()
        call_kwargs = mock_client.cmake_build.call_args
        assert call_kwargs.kwargs["cmake_args"] == "-DCMAKE_BUILD_TYPE=Release"
        assert call_kwargs.kwargs["options"] == "-O2"


class TestCmakeShareUrl:
    """Test CMake share URL generation."""

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def mock_client(self):
        with patch("ce_mcp.tools.CompilerExplorerClient") as mock:
            client_instance = AsyncMock()
            mock.return_value = client_instance
            yield client_instance

    @pytest.mark.asyncio
    async def test_generate_cmake_share_url(self, config, mock_client):
        """Test generating a share URL for a cmake project."""
        mock_client.create_cmake_short_link.return_value = "https://godbolt.org/z/abc123"

        result = await generate_cmake_share_url(
            {
                "cmake_source": "cmake_minimum_required(VERSION 3.10)\nproject(test)\nadd_executable(output.s main.cpp)",
                "files": [{"filename": "main.cpp", "contents": "int main() { return 0; }"}],
                "compiler": "g++",
            },
            config,
        )

        assert result["url"] == "https://godbolt.org/z/abc123"
        mock_client.create_cmake_short_link.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_cmake_share_url_with_options(self, config, mock_client):
        """Test share URL with cmake args and compiler options."""
        mock_client.create_cmake_short_link.return_value = "https://godbolt.org/z/xyz789"

        result = await generate_cmake_share_url(
            {
                "cmake_source": "cmake_minimum_required(VERSION 3.10)\nproject(test)\nadd_executable(output.s main.cpp)",
                "files": [{"filename": "main.cpp", "contents": "int main() {}"}],
                "compiler": "g++",
                "options": "-O2 -Wall",
                "cmake_args": "-DCMAKE_BUILD_TYPE=Release",
            },
            config,
        )

        assert result["url"] == "https://godbolt.org/z/xyz789"
        call_kwargs = mock_client.create_cmake_short_link.call_args
        assert call_kwargs.kwargs["options"] == "-O2 -Wall"
        assert call_kwargs.kwargs["cmake_args"] == "-DCMAKE_BUILD_TYPE=Release"

    @pytest.mark.asyncio
    async def test_generate_cmake_share_url_multifile(self, config, mock_client):
        """Test share URL with multiple files."""
        mock_client.create_cmake_short_link.return_value = "https://godbolt.org/z/multi"

        result = await generate_cmake_share_url(
            {
                "cmake_source": "cmake_minimum_required(VERSION 3.10)\nproject(test)\nadd_executable(output.s main.cpp helper.cpp)",
                "files": [
                    {"filename": "main.cpp", "contents": '#include "helper.h"\nint main() { return add(1,2); }'},
                    {
                        "filename": "helper.cpp",
                        "contents": '#include "helper.h"\nint add(int a, int b) { return a+b; }',
                    },
                    {"filename": "helper.h", "contents": "#pragma once\nint add(int a, int b);"},
                ],
                "compiler": "g++",
            },
            config,
        )

        assert result["url"] == "https://godbolt.org/z/multi"
        call_kwargs = mock_client.create_cmake_short_link.call_args
        assert len(call_kwargs.kwargs["files"]) == 3


class TestAnsiStripping:
    """Test ANSI escape code stripping."""

    def test_strip_ansi_codes(self):
        assert _strip_ansi("\x1b[31merror\x1b[0m: bad thing") == "error: bad thing"

    def test_strip_ansi_no_codes(self):
        assert _strip_ansi("plain text") == "plain text"

    def test_extract_build_step_text_list(self):
        items = [{"text": "\x1b[1mBold\x1b[0m"}, {"text": "plain"}]
        assert _extract_build_step_text(items) == "Bold\nplain"

    def test_extract_build_step_text_string(self):
        assert _extract_build_step_text("\x1b[31mred\x1b[0m") == "red"

    def test_extract_build_step_text_empty(self):
        assert _extract_build_step_text(None) == ""
        assert _extract_build_step_text([]) == ""


class TestResolveCmakeInputs:
    """Test _resolve_cmake_inputs file resolution."""

    def test_inline_content(self):
        """Test mode 1: inline cmake_source + files with contents."""
        cmake_source, files = _resolve_cmake_inputs(
            {
                "cmake_source": "cmake_minimum_required(VERSION 3.10)",
                "files": [{"filename": "main.cpp", "contents": "int main() {}"}],
            }
        )
        assert cmake_source == "cmake_minimum_required(VERSION 3.10)"
        assert len(files) == 1
        assert files[0]["filename"] == "main.cpp"
        assert files[0]["contents"] == "int main() {}"

    def test_file_paths(self, tmp_path):
        """Test mode 2: cmake_path + files with path field."""
        cmake_file = tmp_path / "CMakeLists.txt"
        cmake_file.write_text("cmake_minimum_required(VERSION 3.10)")
        src_file = tmp_path / "main.cpp"
        src_file.write_text("int main() { return 0; }")

        cmake_source, files = _resolve_cmake_inputs(
            {
                "cmake_path": str(cmake_file),
                "files": [{"path": str(src_file)}],
            }
        )
        assert cmake_source == "cmake_minimum_required(VERSION 3.10)"
        assert len(files) == 1
        assert files[0]["filename"] == "main.cpp"
        assert files[0]["contents"] == "int main() { return 0; }"

    def test_file_path_with_rename(self, tmp_path):
        """Test path entry with explicit filename override."""
        src_file = tmp_path / "my_main.cpp"
        src_file.write_text("int main() {}")

        _, files = _resolve_cmake_inputs(
            {
                "cmake_source": "project(test)",
                "files": [{"path": str(src_file), "filename": "main.cpp"}],
            }
        )
        assert files[0]["filename"] == "main.cpp"
        assert files[0]["contents"] == "int main() {}"

    def test_project_dir(self, tmp_path):
        """Test mode 3: auto-discover from project directory."""
        (tmp_path / "CMakeLists.txt").write_text("project(test)")
        (tmp_path / "main.cpp").write_text("int main() {}")
        (tmp_path / "helper.h").write_text("#pragma once")
        (tmp_path / "helper.cpp").write_text("void help() {}")
        # Non-source files should be ignored
        (tmp_path / "README.md").write_text("readme")
        (tmp_path / "build.sh").write_text("#!/bin/bash")

        cmake_source, files = _resolve_cmake_inputs({"project_dir": str(tmp_path)})
        assert cmake_source == "project(test)"
        filenames = {f["filename"] for f in files}
        assert filenames == {"helper.cpp", "helper.h", "main.cpp"}
        assert "README.md" not in filenames

    def test_project_dir_with_subdirs(self, tmp_path):
        """Test project_dir discovers files in subdirectories."""
        (tmp_path / "CMakeLists.txt").write_text("project(test)")
        (tmp_path / "main.cpp").write_text("int main() {}")
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "lib.cpp").write_text("void lib() {}")
        inc_dir = tmp_path / "include"
        inc_dir.mkdir()
        (inc_dir / "lib.h").write_text("#pragma once")

        cmake_source, files = _resolve_cmake_inputs({"project_dir": str(tmp_path)})
        filenames = {f["filename"] for f in files}
        assert filenames == {"main.cpp", os.path.join("src", "lib.cpp"), os.path.join("include", "lib.h")}

    def test_missing_cmake_source_error(self):
        """Test error when no cmake source is provided."""
        with pytest.raises(ValueError, match="One of cmake_source, cmake_path, or project_dir is required"):
            _resolve_cmake_inputs({"files": [{"filename": "main.cpp", "contents": ""}]})

    def test_missing_cmakelists_in_project_dir(self, tmp_path):
        """Test error when project_dir has no CMakeLists.txt."""
        (tmp_path / "main.cpp").write_text("int main() {}")
        with pytest.raises(ValueError, match="No CMakeLists.txt found"):
            _resolve_cmake_inputs({"project_dir": str(tmp_path)})

    def test_no_source_files_in_project_dir(self, tmp_path):
        """Test error when project_dir has no source files."""
        (tmp_path / "CMakeLists.txt").write_text("project(test)")
        with pytest.raises(ValueError, match="No source files found"):
            _resolve_cmake_inputs({"project_dir": str(tmp_path)})

    def test_file_path_not_found(self, tmp_path):
        """Test error when a file path doesn't exist."""
        with pytest.raises(ValueError, match="File not found"):
            _resolve_cmake_inputs(
                {
                    "cmake_source": "project(test)",
                    "files": [{"path": str(tmp_path / "nonexistent.cpp")}],
                }
            )

    def test_cmake_path_not_found(self, tmp_path):
        """Test error when cmake_path doesn't exist."""
        with pytest.raises(ValueError, match="cmake_path is not a file"):
            _resolve_cmake_inputs(
                {
                    "cmake_path": str(tmp_path / "nonexistent.txt"),
                    "files": [],
                }
            )

    def test_file_entry_missing_contents_and_path(self):
        """Test error when file entry has neither contents nor path."""
        with pytest.raises(ValueError, match="must have either 'contents' or 'path'"):
            _resolve_cmake_inputs(
                {
                    "cmake_source": "project(test)",
                    "files": [{"filename": "main.cpp"}],
                }
            )

    def test_mixed_inline_and_path_files(self, tmp_path):
        """Test mixing inline content and path-based files."""
        src_file = tmp_path / "helper.cpp"
        src_file.write_text("void help() {}")

        _, files = _resolve_cmake_inputs(
            {
                "cmake_source": "project(test)",
                "files": [
                    {"filename": "main.cpp", "contents": "int main() {}"},
                    {"path": str(src_file)},
                ],
            }
        )
        assert len(files) == 2
        assert files[0]["filename"] == "main.cpp"
        assert files[0]["contents"] == "int main() {}"
        assert files[1]["filename"] == "helper.cpp"
        assert files[1]["contents"] == "void help() {}"

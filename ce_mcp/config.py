"""Configuration management for Compiler Explorer MCP."""

import os
from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, Field


class APIConfig(BaseModel):
    """API configuration."""

    endpoint: str = "https://godbolt.org/api"
    timeout: int = 30
    retry_count: int = 3
    retry_backoff: float = 1.5

    @property
    def user_agent(self) -> str:
        """Hardcoded user agent that cannot be overridden by configuration."""
        return "CompilerExplorerMCP/1.0"


class CacheConfig(BaseModel):
    """Cache configuration."""

    enabled: bool = True
    directory: str = "~/.cache/compiler_explorer_mcp"
    ttl_seconds: int = 3600
    max_size_mb: int = 100


class DefaultsConfig(BaseModel):
    """Default settings."""

    language: str = "c++"
    compiler: str = "g132"
    extract_args_from_source: bool = True


class FiltersConfig(BaseModel):
    """Compiler Explorer output filters."""

    binary: bool = False
    binaryObject: bool = False
    commentOnly: bool = False
    demangle: bool = True
    directives: bool = True
    execute: bool = False
    intel: bool = True
    labels: bool = True
    libraryCode: bool = True
    trim: bool = True
    debugCalls: bool = True


class OutputLimitsConfig(BaseModel):
    """Output size limits."""

    max_stdout_lines: int = 100
    max_stderr_lines: int = 50
    max_assembly_lines: int = 500
    max_line_length: int = 200
    truncation_message: str = "... (truncated)"


class Config(BaseModel):
    """Main configuration class."""

    api: APIConfig = Field(default_factory=APIConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    output_limits: OutputLimitsConfig = Field(default_factory=OutputLimitsConfig)
    compiler_mappings: Dict[str, str] = Field(
        default_factory=lambda: {
            "g++": "g132",
            "gcc-latest": "g132",
            "clang++": "clang1700",
            "clang-latest": "clang1700",
            "fpc": "fpc322",
            "rustc": "r1740",
            "go": "gccgo132",
        }
    )

    @classmethod
    def load_from_file(cls, path: Optional[Path] = None) -> "Config":
        """Load configuration from YAML file."""
        if path is None:
            path = Path.home() / ".config" / "compiler_explorer_mcp" / "config.yaml"

        if not path.exists():
            return cls()

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        if data and "compiler_explorer_mcp" in data:
            return cls(**data["compiler_explorer_mcp"])

        return cls()

    def resolve_compiler(self, compiler: str) -> str:
        """Resolve user-friendly compiler name to CE compiler ID."""
        return self.compiler_mappings.get(compiler, compiler)

    def get_cache_dir(self) -> Path:
        """Get resolved cache directory path."""
        cache_dir = os.path.expanduser(self.cache.directory)
        return Path(cache_dir)

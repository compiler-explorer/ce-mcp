"""Tests for configuration management."""

import tempfile
from pathlib import Path

import yaml

from ce_mcp.config import APIConfig, Config, FiltersConfig


class TestConfig:
    """Test configuration loading and defaults."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()

        # API defaults
        assert config.api.endpoint == "https://godbolt.org/api"
        assert config.api.user_agent == "CompilerExplorerMCP/1.0"
        assert config.api.timeout == 30

        # Cache defaults
        assert config.cache.enabled is True
        assert config.cache.ttl_seconds == 3600

        # Language defaults
        assert config.defaults.language == "c++"
        assert config.defaults.compiler == "g132"

        # Filter defaults
        assert config.filters.commentOnly is False
        assert config.filters.binary is False
        assert config.filters.intel is True

    def test_load_from_file(self):
        """Test loading configuration from YAML file."""
        config_data = {
            "compiler_explorer_mcp": {
                "api": {
                    "endpoint": "https://custom.api/",
                    "timeout": 60,
                },
                "defaults": {
                    "language": "rust",
                    "compiler": "rustc",
                },
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            config = Config.load_from_file(temp_path)
            assert config.api.endpoint == "https://custom.api/"
            assert config.api.timeout == 60
            assert config.defaults.language == "rust"
            assert config.defaults.compiler == "rustc"
            # Check that other defaults are preserved
            assert config.api.user_agent == "CompilerExplorerMCP/1.0"
        finally:
            temp_path.unlink()

    def test_compiler_resolution(self):
        """Test compiler name resolution."""
        config = Config()

        # Test built-in mappings
        assert config.resolve_compiler("g++") == "g132"
        assert config.resolve_compiler("clang++") == "clang1700"
        assert config.resolve_compiler("rustc") == "r1740"

        # Test passthrough for unknown compilers
        assert config.resolve_compiler("unknown123") == "unknown123"

    def test_cache_directory_expansion(self):
        """Test cache directory path expansion."""
        config = Config()
        cache_dir = config.get_cache_dir()

        # Should expand ~ to home directory
        assert not str(cache_dir).startswith("~")
        assert cache_dir.is_absolute()


class TestAPIConfig:
    """Test API configuration."""

    def test_retry_settings(self):
        """Test retry configuration."""
        api_config = APIConfig()
        assert api_config.retry_count == 3
        assert api_config.retry_backoff == 1.5

    def test_hardcoded_user_agent(self):
        """Test that user agent is hardcoded and cannot be overridden."""
        api_config = APIConfig()
        assert api_config.user_agent == "CompilerExplorerMCP/1.0"

        # Even with different config, user_agent should remain hardcoded
        api_config_custom = APIConfig(timeout=60)
        assert api_config_custom.user_agent == "CompilerExplorerMCP/1.0"


class TestFiltersConfig:
    """Test filter configuration."""

    def test_all_filters_present(self):
        """Ensure all CE filters are configurable."""
        filters = FiltersConfig()

        # Check key filters mentioned in spec
        assert hasattr(filters, "binary")
        assert hasattr(filters, "binaryObject")
        assert hasattr(filters, "commentOnly")
        assert hasattr(filters, "demangle")
        assert hasattr(filters, "directives")
        assert hasattr(filters, "execute")
        assert hasattr(filters, "intel")
        assert hasattr(filters, "labels")
        assert hasattr(filters, "libraryCode")
        assert hasattr(filters, "trim")
        assert hasattr(filters, "debugCalls")

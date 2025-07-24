#!/usr/bin/env python3
"""Test runner script for ce-mcp."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")

    try:
        subprocess.run(cmd, check=True, cwd=Path(__file__).parent)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False


def main():
    """Run different test suites."""
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "all"

    # Activate virtual environment prefix
    venv_prefix = ["source", ".venv/bin/activate", "&&"]

    success = True

    if test_type in ("all", "unit"):
        # Run unit tests (excluding integration tests)
        cmd = venv_prefix + [
            "pytest",
            "tests/",
            "-v",
            "-m",
            "not integration",
            "--cov=ce_mcp",
        ]
        success &= run_command(cmd, "Unit Tests")

    if test_type in ("all", "integration"):
        # Run integration tests
        cmd = venv_prefix + [
            "pytest",
            "tests/test_integration.py",
            "-v",
            "-m",
            "integration",
        ]
        success &= run_command(cmd, "Integration Tests")

    if test_type in ("all", "lint"):
        # Run linting
        cmd = venv_prefix + ["black", "--check", "."]
        success &= run_command(cmd, "Black Code Formatting Check")

        cmd = venv_prefix + ["isort", "--check-only", "."]
        success &= run_command(cmd, "Import Sorting Check")

        cmd = venv_prefix + ["flake8", "ce_mcp/"]
        success &= run_command(cmd, "Flake8 Linting")

    if test_type in ("all", "typecheck"):
        # Run type checking
        cmd = venv_prefix + ["mypy", "ce_mcp/"]
        success &= run_command(cmd, "MyPy Type Checking")

    if test_type == "format":
        # Format code
        cmd = venv_prefix + ["black", "."]
        success &= run_command(cmd, "Black Code Formatting")

        cmd = venv_prefix + ["isort", "."]
        success &= run_command(cmd, "Import Sorting")

    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python run_tests.py [test_type]")
        print("  test_type: all, unit, integration, lint, typecheck, format")
        print("  Default: all")
        sys.exit(0)

    main()

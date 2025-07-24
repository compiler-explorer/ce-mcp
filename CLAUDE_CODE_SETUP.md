# 🚀 Quick Setup for Claude Code

This guide gets you up and running with the Compiler Explorer MCP server in Claude Code in under 2 minutes.

## One-Line Setup

```bash
git clone https://github.com/compiler-explorer/ce-mcp && cd ce-mcp && ./setup-claude-code.sh
```

That's it! The script handles everything automatically.

## What the Script Does

1. **Checks prerequisites** - Ensures Python 3.8+ and UV/pip are installed
2. **Installs the MCP server** - Sets up ce-mcp in your project environment
3. **Creates configuration files**:
   - `.claude.json` - Project MCP server configuration  
   - `~/.claude/settings.json` - Global auto-approval settings
   - `.ce-mcp-config.yaml` - Your project-specific settings
4. **Creates automatic backups** - Backs up existing settings before modifying
5. **Verifies installation** - Tests that everything works
6. **Shows usage examples** - Ready-to-copy tool commands

## Usage Options

### Setup in Current Directory
```bash
./setup-claude-code.sh
```

### Setup in Specific Project
```bash
./setup-claude-code.sh --project-dir ~/my-cpp-project
```

### Global Installation
```bash
./setup-claude-code.sh --global
```

## Interactive Configuration

The script will ask you:
- **Primary language**: c++, c, rust, go, python (default: c++)
- **Preferred compiler**: g++, clang++, rustc, etc. (default: g++)

## Verification

After setup, test in Claude Code:

```
@compiler-explorer compile_check_tool source="int main(){return 0;}" language="c++" compiler="g++"
```

## What You Get

### Available Tools
- `compile_check_tool` - Quick syntax validation
- `compile_and_run_tool` - Compile and execute code  
- `compile_with_diagnostics_tool` - Detailed error analysis
- `analyze_optimization_tool` - Assembly optimization analysis
- `generate_share_url_tool` - Create shareable Compiler Explorer links
- `compare_compilers_tool` - Side-by-side compiler comparison

### Smart Features
- **Argument extraction**: Add `// compile: -std=c++20 -O2` to source files
- **Language detection**: Automatic language detection from file extensions
- **Token optimization**: Responses designed for efficient Claude Code usage
- **Project-specific configs**: Different settings per project

## Configuration Files Created

### `.claude.json` (Project Configuration)
```json
{
  "mcp_servers": {
    "compiler-explorer": {
      "command": "/path/to/ce-mcp",
      "args": ["--config", "./.ce-mcp-config.yaml"]
    }
  }
}
```

### `~/.claude/settings.json` (Global Settings)
```json
{
  "enableAllProjectMcpServers": true
}
```

### `.ce-mcp-config.yaml`
```yaml
compiler_explorer_mcp:
  defaults:
    language: "c++"
    compiler: "g++"
  output_limits:
    max_stdout_lines: 50
    max_stderr_lines: 25
```

## Troubleshooting

**Script fails with "python3 not found"**
- Install Python 3.8+: https://python.org/downloads

**Script fails with "uv not found"**  
- The script will auto-install UV, or use pip instead

**"ce-mcp command not found" in Claude Code**
- Make sure you're in the project directory where setup was run
- Try: `source .venv/bin/activate && ce-mcp --help`

**Tools not showing up in Claude Code**
- Restart Claude Code after setup
- Check that `~/.claude/settings.json` contains the compiler-explorer server
- Verify MCP server is running: `ce-mcp --help`

**Existing MCP servers stopped working**
- Check `~/.claude/settings.json` for syntax errors
- Restore from backup: `cp ~/.claude/settings.json.backup.YYYYMMDD_HHMMSS ~/.claude/settings.json`
- The script creates automatic backups before making changes

**"compiler-explorer already exists" error**
- The script will update the existing entry
- Use `--force` flag to overwrite without prompting (if implemented)
- Manually edit `~/.claude/settings.json` to remove the old entry

## Example Usage in Claude Code

Once setup is complete, you can use these commands in Claude Code:

### Quick Syntax Check
```
@compiler-explorer compile_check_tool source="int main() { return 0; }" language="c++" compiler="g++"
```

### Compile and Run
```
@compiler-explorer compile_and_run_tool source="#include <iostream>\nint main() { std::cout << \"Hello World!\" << std::endl; return 0; }" language="c++" compiler="g++"
```

### Error Analysis
```
@compiler-explorer compile_with_diagnostics_tool source="int main() { undefined_function(); }" language="c++" compiler="g++" diagnostic_level="verbose"
```

### Optimization Analysis
```
@compiler-explorer analyze_optimization_tool source="int main() { int sum = 0; for(int i = 0; i < 100; i++) sum += i; return sum; }" language="c++" compiler="g++" optimization_level="-O3"
```

### Generate Share URL
```
@compiler-explorer generate_share_url_tool source="int main() { return 42; }" language="c++" compiler="g++" options="-O2"
```

Happy coding! 🎉
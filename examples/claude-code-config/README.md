# Claude Code Configuration Example

This directory contains example configuration files for using the Compiler Explorer MCP server with Claude Code.

## Files

- **`.claude.json`** - MCP server configuration for Claude Code
- **`.ce-mcp-config.yaml`** - Project-specific settings for the Compiler Explorer MCP server

## Setup

1. Copy these files to your C++/coding project root:
   ```bash
   cp .claude.json /path/to/your/project/
   cp .ce-mcp-config.yaml /path/to/your/project/
   ```

2. Install the MCP server in your project:
   ```bash
   cd /path/to/your/project
   uv pip install ce-mcp
   ```

3. Open your project in Claude Code and the MCP server will be automatically available.

## Usage Examples

Once configured, you can use these tools in Claude Code:

### Quick Syntax Check
```
@compiler-explorer compile_check_tool source="int main() { return 0; }" language="c++" compiler="g++"
```

### Compile and Run
```
@compiler-explorer compile_and_run_tool source="#include <iostream>\nint main() { std::cout << \"Hello!\" << std::endl; return 0; }" language="c++" compiler="g++"
```

### Get Compilation Diagnostics
```
@compiler-explorer compile_with_diagnostics_tool source="int main() { undefined_function(); }" language="c++" compiler="g++" diagnostic_level="verbose"
```

### Analyze Optimizations
```
@compiler-explorer analyze_optimization_tool source="int main() { int arr[100]; for(int i=0; i<100; i++) arr[i] = i; return 0; }" language="c++" compiler="g++" optimization_level="-O3"
```

### Generate Share URL
```
@compiler-explorer generate_share_url_tool source="int main() { return 42; }" language="c++" compiler="g++" options="-O2"
```

## Configuration Options

The `.ce-mcp-config.yaml` file can be customized for your project:

- **Language/Compiler defaults**: Set your preferred language and compiler
- **Output limits**: Control how much output is shown
- **Compiler mappings**: Use friendly names like "g++" instead of "g132"
- **Filters**: Customize what appears in assembly output

## Tips

- Add compilation flags to your source files:
  ```cpp
  // compile: -std=c++20 -Wall -O2
  #include <iostream>
  int main() { return 0; }
  ```

- The server automatically extracts these flags when `extract_args_from_source: true`
# Claude Code Setup

## Quick Setup

```bash
git clone https://github.com/compiler-explorer/ce-mcp && cd ce-mcp && ./setup-claude-code.sh
```

## Test Installation

```
@compiler-explorer compile_check_tool source="int main(){return 0;}" language="c++" compiler="g++"
```

## Troubleshooting

**Tools not showing up**: Restart Claude Code after setup
**Command not found**: Run `source .venv/bin/activate && ce-mcp --help`
**Backup restore**: `cp ~/.claude/settings.json.backup.* ~/.claude/settings.json`
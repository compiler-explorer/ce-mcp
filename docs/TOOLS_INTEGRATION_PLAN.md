# Compiler Explorer Tools Integration Plan

## Overview

This document outlines the plan to integrate Compiler Explorer's static analysis and code quality tools into the ce-mcp project. This enhancement will transform ce-mcp from a compilation-focused service into a comprehensive code analysis platform.

## Background

Compiler Explorer (godbolt.org) supports various static analysis tools including:
- **clang-tidy** - Clang-based C++ linter with hundreds of checks
- **cppcheck** - Static analysis tool for C/C++ detecting bugs compilers miss
- **GCC Static Analyzer** - Built-in static analysis via `-fanalyzer`
- **PVS-Studio** - Commercial static analyzer
- **Other tools** - Language-specific analyzers and formatters

Currently, these tools are accessible through the web interface but not programmatically via the API.

## Catalyst: New API Endpoint

**PR #7950** adds `/api/tools/<language>` endpoint:
- Lists available tools for each language
- Provides tool metadata (id, name, type, languageId, allowStdin)
- Enables programmatic tool discovery

**Example Response:**
```json
[
  {
    "id": "clangtidy",
    "name": "Clang-Tidy", 
    "type": "postprocessor",
    "languageId": "c++",
    "allowStdin": true
  },
  {
    "id": "cppcheck",
    "name": "Cppcheck",
    "type": "postprocessor", 
    "languageId": "c++",
    "allowStdin": false
  }
]
```

## Implementation Plan

### Phase 1: Foundation (Immediate)
**Prerequisites:** PR #7950 merged

1. **Add tools discovery to API client**
   - Implement `get_tools(language)` method
   - Cache tool availability per language
   - Handle tool metadata parsing

2. **Extend existing MCP tools with tools parameter**
   - Add optional `tools: list[str]` to all compilation functions
   - Pass tools to Compiler Explorer API payload
   - Parse and return tool outputs alongside compilation results

3. **Enhanced API client methods**
   - Update `compile()` to accept tools parameter
   - Parse tool outputs from API responses
   - Structure tool results for easy consumption

### Phase 2: New MCP Tools (Core Features)

1. **`list_available_tools_tool`** - Discovery function
   ```python
   @mcp.tool()
   async def list_available_tools_tool(language: str) -> str:
       """List all static analysis tools available for a language."""
   ```

2. **`run_static_analysis_tool`** - Dedicated analysis function
   ```python
   @mcp.tool()
   async def run_static_analysis_tool(
       source: str,
       language: str, 
       tools: list[str],
       compiler: str = "g132"
   ) -> str:
       """Run static analysis tools without compilation."""
   ```

3. **`analyze_code_quality_tool`** - Comprehensive analysis
   ```python
   @mcp.tool()
   async def analyze_code_quality_tool(
       source: str,
       language: str,
       analysis_level: str = "standard"  # basic, standard, comprehensive
   ) -> str:
       """Run multiple static analysis tools and aggregate results."""
   ```

### Phase 3: Advanced Features

1. **Tool-specific analyzers**
   - `run_clang_tidy_tool` with check selection
   - `run_cppcheck_tool` with severity filtering
   - Language-specific tool wrappers

2. **Intelligent tool selection**
   - Auto-select relevant tools based on code patterns
   - Severity-based filtering and reporting
   - Performance impact analysis

3. **Comparative analysis**
   - Compare tool outputs across compiler versions
   - Before/after code quality metrics
   - Tool recommendation engine

## Technical Architecture

### API Client Extensions

```python
class CompilerExplorerClient:
    async def get_tools(self, language: str) -> List[Dict[str, Any]]:
        """Get available tools for language."""
        
    async def compile_with_tools(
        self, 
        source: str, 
        language: str, 
        compiler: str,
        tools: List[str] = None
    ) -> Dict[str, Any]:
        """Compile with static analysis tools."""
```

### Tool Output Parsing

```python
class ToolOutputParser:
    def parse_clang_tidy(self, output: str) -> List[Dict]:
        """Parse clang-tidy warnings into structured format."""
        
    def parse_cppcheck(self, output: str) -> List[Dict]:
        """Parse cppcheck reports into structured format."""
        
    def aggregate_tool_results(self, tool_outputs: Dict) -> Dict:
        """Combine multiple tool outputs into unified report."""
```

### Enhanced MCP Tool Structure

```python
{
    "compilation": {
        "success": true,
        "warnings": [],
        "errors": []
    },
    "static_analysis": {
        "tools_used": ["clang-tidy", "cppcheck"],
        "total_issues": 15,
        "by_severity": {
            "error": 2,
            "warning": 8, 
            "info": 5
        },
        "by_tool": {
            "clang-tidy": [...],
            "cppcheck": [...]
        }
    },
    "recommendations": [
        "Consider using std::array instead of C arrays",
        "Add const qualifiers to improve optimization"
    ]
}
```

## Use Cases

### Code Review Enhancement
```python
# Analyze pull request changes
result = await analyze_code_quality_tool(
    source=modified_code,
    language="c++", 
    analysis_level="comprehensive"
)
# Returns: structured issues, severity counts, recommendations
```

### Educational Code Analysis
```python
# Help students understand code quality
result = await run_static_analysis_tool(
    source=student_code,
    language="c++",
    tools=["clang-tidy"]
)
# Returns: learning-focused explanations of issues
```

### CI/CD Integration
```python
# Automated quality gates
issues = await analyze_code_quality_tool(source, "c++", "strict")
if issues["static_analysis"]["by_severity"]["error"] > 0:
    # Fail build
```

## Implementation Todos

### Immediate (Phase 1)
- [ ] Monitor PR #7950 merge status
- [ ] Implement `get_tools()` in API client
- [ ] Add `tools` parameter to existing MCP functions
- [ ] Create tool output parsing utilities
- [ ] Add tool integration tests

### Short-term (Phase 2)  
- [ ] Implement `list_available_tools_tool`
- [ ] Implement `run_static_analysis_tool`
- [ ] Implement `analyze_code_quality_tool`
- [ ] Create structured tool output format
- [ ] Add comprehensive tool documentation

### Medium-term (Phase 3)
- [ ] Add tool-specific MCP functions
- [ ] Implement intelligent tool selection
- [ ] Create comparative analysis features
- [ ] Add tool performance metrics
- [ ] Build recommendation engine

### Long-term (Future)
- [ ] Custom tool configurations
- [ ] Tool result caching and analytics
- [ ] Integration with IDE plugins
- [ ] Real-time collaborative analysis
- [ ] Machine learning for code quality insights

## Success Metrics

1. **Tool Coverage**: Support for 90%+ of Compiler Explorer's available tools
2. **Response Quality**: Structured, actionable analysis results
3. **Performance**: Tool analysis within 5s for typical code samples
4. **Usability**: Clear documentation and examples for each tool
5. **Integration**: Seamless workflow with existing compilation tools

## Risks and Mitigations

### Technical Risks
- **API Changes**: Compiler Explorer tool API may evolve
  - *Mitigation*: Version-aware client with fallback support
- **Tool Output Variability**: Different tools have inconsistent formats
  - *Mitigation*: Robust parsing with error handling
- **Performance Impact**: Multiple tools may slow response times
  - *Mitigation*: Async processing and result caching

### User Experience Risks
- **Information Overload**: Too many tool results may overwhelm users
  - *Mitigation*: Intelligent filtering and severity-based presentation
- **Tool Selection Confusion**: Users may not know which tools to use
  - *Mitigation*: Smart defaults and guided recommendations

## Future Opportunities

1. **Custom Tool Chains**: Allow users to define tool sequences
2. **Code Quality Trends**: Track improvement over time
3. **Team Analytics**: Aggregate analysis across projects
4. **Integration Partnerships**: Connect with other development tools
5. **Educational Platform**: Teach code quality best practices

## References

- [Compiler Explorer PR #7950](https://github.com/compiler-explorer/compiler-explorer/pull/7950) - New tools API endpoint
- [Clang-Tidy Documentation](https://clang.llvm.org/extra/clang-tidy/) - Comprehensive check reference
- [Cppcheck Manual](https://cppcheck.sourceforge.io/manual.pdf) - Static analysis capabilities
- [GCC Static Analyzer](https://gcc.gnu.org/onlinedocs/gcc/Static-Analyzer-Options.html) - Built-in analysis options
- [MCP Specification](https://spec.modelcontextprotocol.io/) - Protocol requirements for tool integration

---

**Status**: Planning phase - awaiting PR #7950 merge
**Priority**: High - significant enhancement to ce-mcp capabilities
**Estimated Implementation Time**: 3-4 weeks across all phases
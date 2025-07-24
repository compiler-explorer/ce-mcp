# Library Support Implementation Plan

## Overview

This document outlines the plan to add library support to all Compiler Explorer MCP tools, starting with a single tool as a prototype and then expanding to the remaining tools.

## Requirements Summary

- **Scope**: All MCP tools, starting with one prototype
- **Library Format**: `[{"id": "abseil", "version": "latest"}, {"id": "boost", "version": "1.82.0"}]`
- **Version Handling**: Auto-resolve "latest" by sorting version lists
- **Compiler Compatibility**: Fail fast if compiler doesn't support requested libraries
- **Error Handling**: Provide library search functionality for failures
- **Integration**: Add optional `libraries` parameter to tools
- **Output**: No additional library info in responses (keep current format)
- **Performance**: No caching initially, implement later as needed

## Implementation Phases

### Phase 1: Foundation Components

#### 1.1 Library Parameter Schema
```python
LibrarySpec = {
    "id": str,           # Library identifier (e.g., "abseil")
    "version": str       # Version spec: specific version, "latest", or alias
}

libraries: Optional[List[LibrarySpec]] = None
```

#### 1.2 Core Library Functions
Extend `ce_mcp/library_utils.py`:

```python
async def resolve_libraries_for_compilation(
    libraries: List[Dict[str, str]],
    language: str,
    compiler_id: str,
    client: CompilerExplorerClient
) -> List[Dict[str, str]]:
    """
    Resolve library specifications to concrete library configs for compilation.
    
    Returns:
        List of resolved library specs ready for CE API
        
    Raises:
        LibraryNotFoundError: If library doesn't exist
        LibraryVersionError: If version doesn't exist  
        CompilerLibraryError: If compiler doesn't support library
    """

async def search_libraries(
    search_term: str,
    language: str,
    client: CompilerExplorerClient,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search libraries by name/ID and return suggestions."""

class LibraryError(Exception):
    """Base class for library-related errors."""

class LibraryNotFoundError(LibraryError):
    """Library not found."""
    
class LibraryVersionError(LibraryError):
    """Library version not found."""
    
class CompilerLibraryError(LibraryError):
    """Compiler doesn't support library."""
```

#### 1.3 Library Validation Pipeline
```python
async def validate_and_resolve_libraries(
    libraries: Optional[List[Dict[str, str]]],
    language: str,
    compiler_id: str,
    client: CompilerExplorerClient
) -> List[Dict[str, str]]:
    """
    Complete validation and resolution pipeline:
    1. Fetch available libraries for language
    2. Fetch compiler info with libsArr
    3. Validate each library exists
    4. Resolve versions (including "latest")
    5. Check compiler compatibility
    6. Return resolved library specs for CE API
    """
```

### Phase 2: Prototype Implementation

#### 2.1 Starting Tool: `compile_and_run_tool`

**Rationale**: Most complete workflow, demonstrates all library features including execution.

**Modified Tool Signature**:
```python
async def compile_and_run_tool(
    source: str,
    language: str,
    compiler: str,
    options: str = "",
    stdin: str = "",
    args: List[str] = None,
    timeout: int = 5000,
    libraries: Optional[List[Dict[str, str]]] = None  # NEW PARAMETER
) -> Dict[str, Any]:
```

**Implementation Steps**:
1. Add library parameter to tool schema
2. Integrate library validation pipeline
3. Pass resolved libraries to `client.compile_and_execute()`
4. Update error handling with library search suggestions
5. Add comprehensive tests

#### 2.2 API Client Updates

Modify `compile_and_execute()` method:
```python
async def compile_and_execute(
    self,
    source: str,
    language: str,
    compiler: str,
    options: str = "",
    stdin: str = "",
    args: List[str] = None,
    timeout: int = 5000,
    libraries: List[Dict[str, str]] = None  # NEW PARAMETER
) -> Dict[str, Any]:
```

Update payload to include libraries in the CE API format:
```python
payload = {
    # ... existing fields ...
    "options": {
        # ... existing options ...
        "libraries": libraries or [],  # Add resolved libraries
    }
}
```

### Phase 3: Error Handling & User Experience

#### 3.1 Library Search Integration
```python
def format_library_error_with_suggestions(
    error: LibraryError,
    search_term: str,
    language: str,
    client: CompilerExplorerClient
) -> str:
    """
    Format library errors with helpful suggestions.
    
    Example output:
    Library 'absail' not found for C++. Did you mean:
    - abseil (Abseil Common Libraries) - versions: 20250127.0
    - boost (Boost C++ Libraries) - versions: 1.82.0, 1.81.0, trunk
    
    Use: [{"id": "abseil", "version": "latest"}]
    """
```

#### 3.2 Version Resolution Logic
```python
def resolve_latest_version(versions: List[Dict[str, Any]]) -> str:
    """
    Resolve "latest" version using CE ordering logic:
    1. Use $order field if available (lower = newer)
    2. Parse semantic versions if possible
    3. Fallback to string comparison
    4. Final fallback to first version
    """
```

#### 3.3 Compiler Compatibility Check
```python
def check_compiler_library_compatibility(
    compiler_info: Dict[str, Any],
    requested_libraries: List[str],
    all_libraries: List[Dict[str, Any]]
) -> List[str]:
    """
    Check if compiler supports all requested libraries.
    
    Logic:
    - If libsArr is empty: all libraries supported
    - If libsArr has entries: only those libraries supported
    
    Returns:
        List of unsupported library IDs (empty if all supported)
    """
```

### Phase 4: Testing Strategy

#### 4.1 Unit Tests
- Library resolution with various version specs
- Error handling for missing libraries/versions
- Compiler compatibility checking
- Search functionality

#### 4.2 Integration Tests
- End-to-end compilation with real libraries
- Cross-compiler library support validation
- Error scenarios with actual CE API

#### 4.3 Test Cases
```python
test_cases = [
    # Basic functionality
    {"libraries": [{"id": "abseil", "version": "latest"}]},
    {"libraries": [{"id": "boost", "version": "1.82.0"}]},
    
    # Error scenarios  
    {"libraries": [{"id": "nonexistent", "version": "latest"}]},  # Library not found
    {"libraries": [{"id": "abseil", "version": "99.99.99"}]},     # Version not found
    
    # Edge cases
    {"libraries": []},  # Empty list
    {"libraries": None},  # No libraries
    {"libraries": [{"id": "abseil", "version": "trunk"}]},  # Alias version
]
```

### Phase 5: Rollout to Remaining Tools

After prototype validation, add libraries parameter to:

#### 5.1 Tool Priority Order
1. ✅ `compile_and_run_tool` (prototype)
2. `compile_with_diagnostics_tool` - diagnostics benefit from library context
3. `compile_check_tool` - basic syntax checking with libraries
4. `analyze_optimization_tool` - optimization analysis may differ with libraries
5. `compare_compilers_tool` - compare how different compilers handle same libraries
6. `generate_share_url_tool` - share examples with libraries

#### 5.2 Tool-Specific Considerations

**`compile_with_diagnostics_tool`**:
- Library-related errors may appear in diagnostics
- Include library resolution in diagnostic context

**`analyze_optimization_tool`**:
- Library code may affect optimization analysis
- Consider library code filtering options

**`compare_compilers_tool`**:
- Ensure all compared compilers support requested libraries
- Add library compatibility to comparison criteria

**`generate_share_url_tool`**:
- Include library configurations in shared URLs
- Ensure libraries persist in generated links

### Phase 6: Documentation & Examples

#### 6.1 Tool Documentation Updates
- Add library parameter to all tool descriptions
- Include example library specifications
- Document error handling behavior

#### 6.2 Example Usage
```python
# Basic usage with latest version
libraries = [{"id": "abseil", "version": "latest"}]

# Specific versions
libraries = [
    {"id": "abseil", "version": "20250127.0"},
    {"id": "boost", "version": "1.82.0"}
]

# Mixed version specs
libraries = [
    {"id": "abseil", "version": "latest"},
    {"id": "boost", "version": "trunk"},
    {"id": "eigen", "version": "3.4.0"}
]
```

## Implementation Timeline

| Phase | Description | Estimated Effort |
|-------|-------------|------------------|
| 1 | Foundation components | 2-3 days |
| 2 | Prototype tool implementation | 2-3 days |
| 3 | Error handling & UX | 1-2 days |
| 4 | Testing | 2-3 days |
| 5 | Rollout to remaining tools | 3-4 days |
| 6 | Documentation | 1 day |

**Total: ~11-16 days**

## Risk Mitigation

1. **CE API Changes**: Monitor CE API stability during implementation
2. **Library Compatibility**: Extensive testing across different compilers
3. **Performance Impact**: Monitor API response times, implement caching if needed
4. **Error Scenarios**: Comprehensive error testing with various invalid inputs

## Success Criteria

- ✅ All tools support library parameter
- ✅ "latest" version resolution works correctly
- ✅ Compiler compatibility checking prevents invalid combinations
- ✅ Clear error messages with library search suggestions
- ✅ Comprehensive test coverage (>90%)
- ✅ Documentation complete with examples
- ✅ No performance regression in existing functionality
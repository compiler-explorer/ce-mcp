# Library Support Documentation

## Overview

Library support has been successfully implemented for the `compile_and_run_tool` MCP Tool. This document describes how to use the library feature and its implementation details.

## Usage

### Basic Library Usage

```python
# Using MCP tool with libraries
result = await compile_and_run_tool(
    source='#include <iostream>\nint main() { std::cout << "Hello"; return 0; }',
    language="c++",
    compiler="g132",
    libraries=[
        {"id": "abseil", "version": "latest"},
        {"id": "boost", "version": "latest"}
    ]
)
```

### Library Specification Format

Libraries are specified as a list of dictionaries with the following format:

```python
libraries = [
    {
        "id": "library_name",    # Required: Library identifier
        "version": "version_spec" # Required: Version specification  
    }
]
```

### Version Specifications

| Version Spec | Description | Example |
|-------------|-------------|---------|
| `"latest"` | Automatically resolves to the most recent **stable** version (excludes trunk/dev) | `{"id": "fmt", "version": "latest"}` → `11.0.0` |
| Specific version | Use exact version string | `{"id": "abseil", "version": "20250127.0"}` |
| Development version | Explicitly request development versions | `{"id": "fmt", "version": "trunk"}` |
| Version alias | Use predefined aliases when available | `{"id": "boost", "version": "stable"}` |

## Features

### ✅ Automatic Version Resolution

The system automatically resolves `"latest"` to the most recent **stable** version:
1. **Filters out development versions**: Excludes `trunk`, `master`, `main`, `dev`, `nightly`, `snapshot`, `head`
2. **Uses `$order` field**: Higher values = newer versions in Compiler Explorer API
3. **Semantic version fallback**: Parses version strings when `$order` unavailable
4. **Stable preference**: Users must explicitly request `"trunk"` for development versions

**Examples:**
- `"latest"` → `fmt 11.0.0` (not `trunk`)
- `"trunk"` → `fmt trunk` (development version)
- `"latest"` → `boost 1.87.0` (most recent stable)

### ✅ Compiler Compatibility Checking

Before compilation, the system verifies that the selected compiler supports all requested libraries:
- **Empty `libsArr`**: Compiler supports ALL libraries for the language
- **Non-empty `libsArr`**: Compiler supports only those specific libraries
- **Fail-fast**: Compilation is rejected if any library is unsupported

### ✅ Intelligent Error Handling

When library errors occur, the system provides helpful suggestions:

```
Library 'absail' not found for c++

Did you mean:
  - abseil (Abseil) - versions: 20250127.0

Example usage: [{"id": "abseil", "version": "latest"}]
```

### ✅ Fuzzy Search for Typos

The error handling includes fuzzy matching to catch common typos:
- Character similarity matching
- Length similarity scoring  
- Character order preservation
- Ranked suggestions by relevance

## Implementation Architecture

### Core Components

```
ce_mcp/
├── library_utils.py          # Core library functions
├── api_client.py             # Updated with library support
├── tools.py                  # Updated compile_and_run function
└── server.py                 # Updated MCP tool signature
```

### Key Functions

#### `validate_and_resolve_libraries()`
Main validation pipeline that:
1. Fetches available libraries for the language
2. Fetches compiler information 
3. Validates library existence
4. Resolves version specifications
5. Checks compiler compatibility
6. Returns resolved library specs for CE API

#### `search_libraries()`
Provides library search with fuzzy matching for error suggestions.

#### `format_library_error_with_suggestions()`
Formats error messages with helpful suggestions and usage examples.

### Error Classes

```python
class LibraryError(Exception):
    """Base class for library-related errors."""

class LibraryNotFoundError(LibraryError):
    """Library not found."""

class LibraryVersionError(LibraryError):
    """Library version not found."""

class CompilerLibraryError(LibraryError):
    """Compiler doesn't support library."""
```

## API Integration

### Compiler Explorer API Usage

The implementation leverages these CE API endpoints:

1. **`/api/libraries/{language}`** - Get all available libraries
2. **`/api/compilers/{language}?fields=...`** - Get compiler info with `libsArr`
3. **`/compiler/{compiler}/compile`** - Compile with libraries in payload

### Library Payload Format

Libraries are passed to the CE API in this format:

```json
{
  "options": {
    "libraries": [
      {"id": "abseil", "version": "202501270"},
      {"id": "boost", "version": "1_82_0"}
    ]
  }
}
```

## Testing

### Test Coverage

The implementation includes comprehensive tests:

- ✅ **Unit tests**: Utility functions, version resolution, fuzzy matching
- ✅ **Integration tests**: End-to-end compilation with real libraries  
- ✅ **Error handling tests**: Invalid libraries, versions, suggestions
- ✅ **MCP tool tests**: Full tool integration with various scenarios

### Test Files

- `test_library_support.py` - Basic functionality tests
- `test_mcp_library_integration.py` - MCP tool integration tests
- `test_real_library_usage.py` - Real-world usage scenarios
- `test_library_comprehensive.py` - Full test suite

### Running Tests

```bash
# Run individual test files
uv run python test_library_support.py
uv run python test_mcp_library_integration.py
uv run python test_real_library_usage.py
uv run python test_library_comprehensive.py

# Or run all tests
pytest tests/
```

## Performance Considerations

### Current Implementation
- **No caching**: Library lists are fetched fresh for each request
- **API efficiency**: Uses optimized field selection for compiler queries
- **Memory efficient**: Processes libraries on-demand

### Future Optimizations (Phase 6)
- Library list caching per language
- Compiler info caching
- Batch library validation
- Connection pooling

## Error Scenarios & Solutions

| Error Type | Cause | Solution |
|------------|-------|----------|
| `LibraryNotFoundError` | Typo in library name | Fuzzy search suggestions provided |
| `LibraryVersionError` | Invalid version specified | Available versions listed |
| `CompilerLibraryError` | Compiler doesn't support library | Choose different compiler |
| `LibraryError` | API communication failure | Retry or check network |

## Examples

### Simple Usage
```python
libraries = [{"id": "abseil", "version": "latest"}]
```

### Multiple Libraries
```python
libraries = [
    {"id": "abseil", "version": "latest"},
    {"id": "boost", "version": "1.82.0"},
    {"id": "eigen", "version": "latest"}
]
```

### Version-Specific Usage
```python
libraries = [
    {"id": "abseil", "version": "20250127.0"},  # Specific version
    {"id": "boost", "version": "trunk"},        # Alias
    {"id": "eigen", "version": "latest"}        # Auto-resolve
]
```

## Limitations

1. **Single Tool**: Currently only implemented for `compile_and_run_tool`
2. **No Caching**: Fresh API calls for each request
3. **Basic Fuzzy Matching**: Simple algorithm, could be improved
4. **Language Support**: Depends on CE API library availability

## Next Steps (Future Phases)

1. **Phase 5**: Roll out to remaining MCP tools
2. **Phase 6**: Add performance optimizations
3. **Enhanced Search**: Better fuzzy matching algorithms
4. **Library Documentation**: Integrate library usage docs
5. **Version Management**: Smart version recommendation

## Troubleshooting

### Common Issues

**Q: "Library not found" error**
- Check spelling of library ID
- Use fuzzy search suggestions
- Verify library exists for the language

**Q: "Version not found" error**  
- Use `"latest"` for newest version
- Check available versions in error message
- Verify version string format

**Q: "Compiler doesn't support library" error**
- Try a different compiler (most support all libraries)
- Check if compiler has `libsArr` restrictions

**Q: Compilation works but library features don't**
- Ensure proper include headers in source code
- Check if library requires specific compiler flags
- Verify library is actually being linked

## Status

✅ **Phase 1**: Foundation Components - **COMPLETE**
✅ **Phase 2**: Prototype Implementation - **COMPLETE**  
✅ **Phase 3**: Error Handling & UX - **COMPLETE**
✅ **Phase 4**: Testing - **COMPLETE**
⏳ **Phase 5**: Rollout to Remaining Tools - **PENDING**
⏳ **Phase 6**: Documentation & Optimization - **PENDING**

The library support implementation is production-ready for the `compile_and_run_tool` and can be extended to other tools following the same pattern.
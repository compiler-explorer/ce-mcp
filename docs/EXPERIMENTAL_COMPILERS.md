# Experimental Compiler Support

The Compiler Explorer MCP now includes comprehensive support for finding and using experimental compilers that support cutting-edge C++ proposals and features.

## 🎯 Problem Solved

Previously, users had to:
- Manually search through 900+ compilers to find experimental ones
- Hardcode compiler IDs for specific proposals (like P3385)  
- Guess which compilers support which experimental features
- Keep track of changing experimental compiler names

## ✅ Solution

The new `find_experimental_compilers_tool` automatically discovers and categorizes experimental compilers without hardcoding, making it easy to:
- Find compilers for specific proposals (P3385, P2996, etc.)
- Discover compilers supporting experimental features (reflection, concepts, modules)
- Stay up-to-date as new experimental compilers are added

## 🛠️ Usage

### Find P3385 Compiler
```python
# Find the compiler supporting P3385
find_experimental_compilers_tool(proposal="P3385")
# Returns: clang_p3385 - x86-64 clang (experimental P3385)

# Use it in compilation
compile_and_run_tool(
    source=your_p3385_code,
    compiler="clang_p3385", 
    language="c++"
)
```

### Find Reflection Compilers
```python
# Find all compilers supporting reflection
find_experimental_compilers_tool(feature="reflection")
# Returns: edg-experimental-reflection, clang_reflection

# Test reflection code
compile_and_run_tool(
    source=reflection_code,
    compiler="clang_reflection",
    language="c++"
)
```

### Browse All Experimental Compilers
```python
# See all experimental compilers organized by category
find_experimental_compilers_tool(show_all=True)
```

## 📊 Available Categories

### **Proposals** (16 compilers)
Support specific C++ proposals:
- `clang_p3385` - P3385 (your example!)
- `clang_p2996` - P2996 (Reflection)
- `clang_p1144` - P1144 (Object relocation)
- `clang_p1061` - P1061 (Structured bindings)
- `clang_p3068` - P3068 (Allowing exception throwing in constant-evaluation)
- And more...

### **Reflection** (2 compilers)
- `edg-experimental-reflection` - EDG experimental reflection
- `clang_reflection` - Clang reflection support

### **Concepts** (1 compiler)
- `clang_concepts` - Old concepts branch

### **Modules** (1 compiler) 
- `gcxx-modules-trunk` - GCC modules support

### **Coroutines** (1 compiler)
- `gcxx-coroutines-trunk` - GCC coroutines

### **Contracts** (5 compilers)
- `clang_ericwf_contracts` - EricWF contracts implementation
- `clang_dascandy_contracts` - DasCandY contracts
- And more...

### **Other Experimental Features**
- `clang_lifetime` - Lifetime analysis
- `clang_autonsdmi` - Metaprogramming (P2632)

## 🔍 Search Options

| Parameter | Description | Example |
|-----------|-------------|---------|
| `proposal` | Find compilers for specific proposal | `"P3385"`, `"3385"`, `"p3385"` |
| `feature` | Find by experimental feature | `"reflection"`, `"concepts"`, `"modules"` |
| `category` | Filter by category | `"proposals"`, `"reflection"`, `"contracts"` |
| `show_all` | Show all experimental compilers | `True` |
| `language` | Programming language | `"c++"` (default) |

## 💡 Real-World Examples

### Testing P3385 Features
```python
# 1. Find the P3385 compiler
result = find_experimental_compilers_tool(proposal="P3385")
# Returns: clang_p3385

# 2. Test your P3385 code
code = """
// Your P3385 experimental code here
#include <iostream>
int main() {
    // P3385 specific features
    return 0;
}
"""

result = compile_and_run_tool(
    source=code,
    compiler="clang_p3385",
    language="c++"
)
```

### Exploring Reflection
```python
# Find all reflection compilers
compilers = find_experimental_compilers_tool(feature="reflection")

# Test with each one
for compiler_info in compilers['compilers']:
    print(f"Testing with {compiler_info['name']}")
    result = compile_and_run_tool(
        source=reflection_test_code,
        compiler=compiler_info['id'],
        language="c++"
    )
```

## 🚀 Benefits

1. **Dynamic Discovery** - No hardcoded compiler lists
2. **Always Up-to-Date** - Automatically finds new experimental compilers
3. **Smart Categorization** - Organizes by proposals and features  
4. **Easy Integration** - Works with all existing MCP tools
5. **Comprehensive Coverage** - Finds compilers you might miss manually

## 🔧 Integration with Other Tools

All existing MCP tools work seamlessly with experimental compilers:

```python
# Compile and run with P3385
compile_and_run_tool(source=code, compiler="clang_p3385")

# Check compilation with reflection
compile_check_tool(source=code, compiler="clang_reflection")

# Analyze optimization with experimental features
analyze_optimization_tool(source=code, compiler="clang_p2996")

# Generate shareable links
generate_share_url_tool(source=code, compiler="clang_p3385")
```

## 📈 Future-Proof

As new experimental compilers are added to Compiler Explorer:
- P3XXX proposals → Automatically detected by proposal number
- New experimental features → Detected by keywords in compiler names
- Trunk/nightly builds → Identified by metadata flags

No code changes needed - the system adapts automatically!

## 🎉 Summary

This feature transforms experimental compiler discovery from:
```python
# OLD: Manual hardcoding
compiler = "clang_p3385"  # Hope this still exists!
```

To:
```python  
# NEW: Dynamic discovery
compilers = find_experimental_compilers_tool(proposal="P3385")
compiler = compilers['compilers'][0]['id']  # Always current!
```

Perfect for researchers, standards committee members, and developers who want to test cutting-edge C++ features without the hassle of manually tracking experimental compiler availability.
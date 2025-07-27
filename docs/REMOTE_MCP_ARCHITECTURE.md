# Remote MCP Architecture and File Handling Strategies

## Overview

This document explains how Model Context Protocol (MCP) servers can be deployed remotely and the various strategies for handling file content without consuming LLM tokens.

## Remote MCP Architecture

### Local MCP (Standard)
```
Client (Claude Desktop) ↔ STDIO ↔ MCP Server (same machine)
```
- Direct process communication via stdin/stdout
- File system access to client's local files
- Zero network latency

### Remote MCP
```
Client (Claude Desktop) ↔ HTTP/WebSocket ↔ MCP Server (remote machine)
```
- Network-based communication using JSON-RPC over HTTP with Server-Sent Events
- Server has its own isolated file system
- Authentication and security considerations required

## Communication Flow

1. **Client connects** to remote MCP server via HTTP endpoint
2. **Authentication** handled through headers, tokens, or API keys
3. **Tool calls** sent as JSON-RPC requests over HTTP
4. **Server responses** streamed back via Server-Sent Events (SSE)
5. **Resource access** limited to server's filesystem and network

## Use Cases for Remote MCP

### Development Teams
- Shared Compiler Explorer access across team members
- Centralized compilation infrastructure with consistent environments
- Cost optimization by running expensive compilation on dedicated servers

### Enterprise Deployments
- Corporate firewall compliance - MCP server inside network, clients outside
- Scalable compilation services for multiple developers
- Audit trails and usage monitoring

### Cloud Services
- SaaS providers offering specialized MCP tools
- Pay-per-use compilation services
- Geographic distribution for performance

## File Handling Strategies

The key challenge with remote MCP is how to provide file content to tools without tokenizing large files in the LLM context.

### 1. MCP Resources (Recommended)

**How it works:**
- MCP servers expose file-like data as "resources" with URIs
- LLM requests resource by URI, server reads file and returns content
- File content never enters LLM's context window

**Example:**
```python
# Server exposes resources
@mcp.resource("file://{path}")
async def read_file_resource(uri: str) -> str:
    path = extract_path_from_uri(uri)
    return read_file(path)

# LLM makes resource request (not tokenized)
content = await mcp.read_resource("file:///home/user/main.cpp")
# Then calls tool with the content
result = await compile_check_tool(source=content, ...)
```

### 2. Client-Side File Reading

**How it works:**
- Claude Desktop/client reads files locally
- Passes content directly to MCP tool calls
- LLM orchestrates but doesn't see file content

**Implementation:**
```typescript
// Client reads file
const sourceCode = fs.readFileSync('/path/to/file.cpp', 'utf8');

// LLM instructs tool call (content not in prompt)
await mcpTool.compile_check({
  source: sourceCode,  // Raw content, not tokenized
  language: "c++",
  compiler: "g132"
});
```

### 3. Hybrid Approach (File References + Streaming)

**How it works:**
- LLM works with file references/metadata only
- Tool calls include file paths
- Server streams file content directly (bypassing LLM)

**Example workflow:**
```python
# LLM sees only metadata
file_info = {
  "path": "/project/src/main.cpp", 
  "size": "2.1KB",
  "modified": "2024-01-15"
}

# Tool call includes path reference
result = await compile_check_tool(
  source_file="/project/src/main.cpp",  # Path only
  language="c++"
)
```

### 4. Current Implementation: Source String (ce-mcp approach)

**Why `source: str` is optimal:**

1. **Universal compatibility** - works local and remote
2. **Explicit control** - LLM decides what code to compile
3. **No file system dependencies** - server doesn't need file access
4. **Security** - no path traversal vulnerabilities
5. **Caching friendly** - content-based rather than path-based

**Tradeoffs:**
- Large files consume tokens
- For typical code snippets (< 1000 lines), this is acceptable
- Provides the most flexible architecture

## Security Implications

### Remote MCP Considerations
- **File access** limited to server's filesystem (not client's local files)
- **Network isolation** - server can't access client's local network
- **Authentication required** for production deployments
- **Rate limiting** and resource controls needed
- **CORS and security headers** must be configured

### File Handling Security
- **Path traversal prevention** when using file paths
- **Content validation** for uploaded/referenced files
- **Size limits** to prevent resource exhaustion
- **Access controls** for file system resources

## Technical Implementation for ce-mcp

The ce-mcp server could be deployed remotely by:

1. **Adding HTTP transport layer** alongside STDIO
2. **Implementing authentication middleware**
3. **Configuring CORS and security headers**
4. **Adding deployment scripts** for cloud platforms
5. **Resource management** for concurrent compilations

## References and Source Material

- [MCP Specification](https://spec.modelcontextprotocol.io/) - Official MCP specification
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) - Reference implementation
- [FastMCP Documentation](https://github.com/jlowin/fastmcp) - Python framework for building MCP servers
- [Claude Desktop MCP Integration](https://claude.ai/docs/mcp) - How Claude Desktop integrates with MCP
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification) - Wire protocol used by MCP
- [Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) - Streaming protocol for real-time updates

## Conclusion

Remote MCP enables powerful distributed computing scenarios while maintaining the tool-based interaction model. The choice of file handling strategy depends on your specific requirements:

- **Use MCP Resources** for server-side file access with token efficiency
- **Use Client-Side Reading** for local file access with remote processing
- **Use Source Strings** (current ce-mcp approach) for maximum compatibility and security

The ce-mcp's current `source: str` approach provides the best balance of security, compatibility, and simplicity for a compilation service.
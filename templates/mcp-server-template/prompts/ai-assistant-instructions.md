# MCP Development Guardrails and Instructions

This prompt file contains specific instructions and guardrails for AI assistants working with MCP (Model Context Protocol) implementations.

## 🚨 CRITICAL CONTEXT

The Model Context Protocol (MCP) and its TypeScript SDK are **NOT in your training data**. You must strictly follow the patterns and examples provided in this template directory.

### Reference Implementation Location
- **Canonical Server**: `mcp-servers/auth-mcp-server/`
- **Template Files**: `templates/mcp-server-template/`
- **Validation Script**: `test-auth-mcp-with-session.js`

## 🔒 MANDATORY REQUIREMENTS

### 1. SDK Usage (NON-NEGOTIABLE)
```typescript
// REQUIRED: These exact imports
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';

// CLIENT VALIDATION
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
```

### 2. Registration Pattern (MANDATORY)
```typescript
// CORRECT: Use server.registerTool(), NOT setRequestHandler()
server.registerTool(toolName, {
  description: 'Tool description',
  inputSchema: zodSchema  // Must be Zod schema, not JSON Schema
}, handlerFunction);

// WRONG: Do not use these patterns
server.setRequestHandler(CallToolRequest, ...);  // ❌ Wrong
app.post('/tools', ...);                         // ❌ Wrong
```

### 3. Session Management (CRITICAL)
```typescript
// CORRECT: Transport handles sessions
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => randomUUID(),
  onsessioninitialized: (sessionId) => {
    // Initialize session-specific data here
  }
});

// WRONG: Manual session management
const sessions = {}; // ❌ Don't manage sessions manually
```

### 4. Authentication (SECURITY)
```typescript
// CLIENT: Headers in requestInit
const transport = new StreamableHTTPClientTransport(url, {
  requestInit: {
    headers: { 'x-api-key': apiKey }
  }
});

// SERVER: Extract headers in tool handlers
// Note: Exact method may vary - follow working examples
```

## 🛡️ GUARDRAILS FOR AI ASSISTANTS

### When Creating MCP Servers:

1. **ALWAYS start with the template**:
   - Copy `templates/mcp-server-template/` as base
   - Modify tool/resource definitions in separate files
   - Keep registration pattern identical

2. **NEVER invent new patterns**:
   - Don't create custom transport layers
   - Don't use Express/Fastify for MCP endpoints
   - Don't implement custom session management

3. **FOLLOW the validated patterns**:
   - Use `server.registerTool()` for tools
   - Use `server.registerResource()` for resources
   - Convert JSON Schema to Zod schemas using provided utility

4. **VALIDATE every implementation**:
   - Must work with the MCP SDK client
   - Must pass validation scripts
   - Must handle authentication correctly

### When Creating Validation Scripts:

1. **ALWAYS use MCP SDK client**:
   ```typescript
   import { Client } from '@modelcontextprotocol/sdk/client/index.js';
   import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
   ```

2. **Include authentication headers**:
   ```typescript
   const transport = new StreamableHTTPClientTransport(url, {
     requestInit: { headers: { 'x-api-key': apiKey } }
   });
   ```

3. **Test all capabilities**:
   - `client.listTools()`
   - `client.listResources()`
   - `client.callTool()`
   - `client.readResource()`

### When Debugging Issues:

1. **Check against working reference**:
   - Compare with `mcp-servers/auth-mcp-server/`
   - Use `test-auth-mcp-with-session.js` as validation baseline

2. **Common issues**:
   - Wrong import paths (must use `.js` extensions)
   - Missing Zod schema conversion
   - Incorrect authentication header handling
   - Session management problems

3. **Validation steps**:
   ```bash
   npm run build    # Check TypeScript compilation
   npm run test     # Run MCP SDK client validation
   npm run validate # Run simple validation
   ```

## 📋 IMPLEMENTATION CHECKLIST

Before considering any MCP implementation complete:

### Server Implementation
- [ ] Uses `StreamableHTTPServerTransport`
- [ ] Registers tools with `server.registerTool()`
- [ ] Uses Zod schemas (converted from JSON Schema)
- [ ] Implements session management via transport
- [ ] Validates API keys in headers
- [ ] Uses environment variables for all config
- [ ] Includes proper error handling

### Client Validation
- [ ] Uses `StreamableHTTPClientTransport`
- [ ] Includes authentication in `requestInit.headers`
- [ ] Tests all server capabilities
- [ ] Handles errors gracefully
- [ ] Connects and disconnects properly

### Project Structure
- [ ] Separates definitions from handlers
- [ ] Includes Docker deployment configuration
- [ ] Has comprehensive validation scripts
- [ ] Documents all environment variables
- [ ] Follows TypeScript best practices

## 🚫 COMMON ANTI-PATTERNS TO AVOID

### 1. Wrong Transport Usage
```typescript
// ❌ WRONG: Custom HTTP server
const express = require('express');
const app = express();

// ❌ WRONG: Raw HTTP requests
const http = require('http');
const server = http.createServer();

// ✅ CORRECT: MCP SDK transport
const transport = new StreamableHTTPServerTransport();
```

### 2. Wrong Registration Method
```typescript
// ❌ WRONG: Manual request handlers
server.setRequestHandler(CallToolRequest, ...);

// ❌ WRONG: HTTP route handlers
app.post('/tools/call', ...);

// ✅ CORRECT: MCP SDK registration
server.registerTool(name, schema, handler);
```

### 3. Wrong Schema Format
```typescript
// ❌ WRONG: JSON Schema directly
server.registerTool(name, {
  inputSchema: { type: 'object', properties: {...} }
});

// ✅ CORRECT: Zod schema
const zodSchema = jsonSchemaToZod(jsonSchema);
server.registerTool(name, { inputSchema: zodSchema });
```

## 🎯 SUCCESS CRITERIA

An MCP implementation is successful when:

1. **It validates with MCP SDK client**: The `test-mcp-client.js` script connects and lists capabilities
2. **All capabilities work**: Tools, resources, and prompts respond correctly
3. **Authentication functions**: API key validation works properly
4. **Session management works**: Multiple clients can connect simultaneously
5. **Error handling is robust**: Graceful responses for all error conditions
6. **Production ready**: Docker deployment, environment variables, health checks

## 🔗 REFERENCE FILES

Always refer to these files when implementing MCP functionality:

- `templates/mcp-server-template/src/index.ts` - Server initialization
- `templates/mcp-server-template/src/registrations.ts` - Capability registration
- `templates/mcp-server-template/validation/test-mcp-client.js` - Client validation
- `templates/mcp-server-template/prompts/` - All prompt files in this directory
- `mcp-servers/auth-mcp-server/` - Working production server

**NEVER deviate from these patterns without explicit justification and validation.**

# MCP Development Guidelines

Use this prompt file as a reference when developing MCP servers or clients.

## 🎯 Development Context

You are developing with the Model Context Protocol (MCP) TypeScript SDK. The MCP protocol enables AI assistants to connect to external data sources and tools through a standardized interface.

### Critical SDK Information
- **Package**: `@modelcontextprotocol/sdk`
- **Transport**: Use `StreamableHTTPServerTransport` for servers, `StreamableHTTPClientTransport` for clients
- **Session Management**: Handled by transport layer, not application code
- **Authentication**: Implemented via HTTP headers in `requestInit.headers`

## 🏗️ Core Architecture Requirements

### 1. Server Structure (MANDATORY)
```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';

// Initialize server with proper metadata
const server = new McpServer({
  name: 'your-server-name',
  version: '1.0.0',
});

// Transport with session management
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => randomUUID(),
  onsessioninitialized: (sessionId) => {
    console.error(`[${sessionId}] Session initialized`);
  }
});
```

### 2. Dynamic Registration (REQUIRED)
- **DO NOT** hardcode tool/resource definitions in handlers
- **DO** import definitions from separate modules
- **DO** use registration functions that iterate over imported objects
- **DO** maintain separation between definitions and handlers

### 3. Session Management (CRITICAL)
- Sessions are managed by `StreamableHTTPServerTransport`
- Each session gets a unique ID via `sessionIdGenerator`
- Store session-specific data in a Map keyed by session ID
- Initialize clients (like API clients) per session to avoid conflicts

### 4. Authentication (SECURITY)
- **ALWAYS** validate API keys in request headers
- Check both `x-api-key` and `authorization` headers
- Use environment variables for API key storage
- Return proper error responses for invalid authentication

## 🔧 Implementation Patterns

### Tool Registration Pattern
```typescript
// 1. Define tools in separate module (tools/definitions.ts)
export const toolDefinitions = {
  tool_name: {
    name: 'tool_name',
    description: 'Clear, detailed description',
    inputSchema: {
      type: 'object',
      properties: {
        param: { type: 'string', description: 'Parameter description' }
      },
      required: ['param']
    }
  }
};

// 2. Define handlers in separate module (tools/handlers.ts)
export const toolHandlers = {
  tool_name: async (args: any, sessionId: string) => {
    // Implementation with session-aware logic
    return { content: [{ type: 'text', text: 'Result' }] };
  }
};

// 3. Register dynamically (registrations.ts)
server.setRequestHandler(ListToolsRequest, async () => ({
  tools: Object.values(toolDefinitions)
}));
```

### Error Handling Pattern
```typescript
// ALWAYS wrap tool handlers in try-catch
async function handleTool(request: CallToolRequest): Promise<CallToolResult> {
  try {
    // Tool logic
    return { content: [{ type: 'text', text: 'Success' }] };
  } catch (error) {
    return {
      content: [{ type: 'text', text: `Error: ${error.message}` }],
      isError: true
    };
  }
}
```

## 🔍 Validation Requirements

### Server Validation
- **MUST** be testable with MCP SDK client
- **MUST** respond to `listTools`, `listResources`, `listPrompts`
- **MUST** handle authentication properly
- **MUST** maintain session state correctly

### Client Validation Script
```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

// This pattern MUST work for any compliant MCP server
const transport = new StreamableHTTPClientTransport({
  url: serverUrl,
  requestInit: { headers: { 'x-api-key': apiKey } }
});

const client = new Client({ name: 'test', version: '1.0.0' }, { capabilities: {} });
await client.connect(transport);
const tools = await client.listTools();
await client.close();
```

## 🚫 Common Pitfalls to Avoid

### 1. Session Management Mistakes
- ❌ Don't store session data in global variables
- ❌ Don't create clients at server startup
- ✅ DO create session-specific clients in `onsessioninitialized`

### 2. Authentication Errors
- ❌ Don't check authentication only at startup
- ❌ Don't ignore `requestInit.headers` in transport
- ✅ DO validate headers in each request handler

### 3. Registration Anti-patterns
- ❌ Don't hardcode tool definitions in handlers
- ❌ Don't register handlers inside other handlers
- ✅ DO separate definitions, handlers, and registration logic

### 4. Transport Configuration Issues
- ❌ Don't use default transport settings for production
- ❌ Don't ignore DNS rebinding protection settings
- ✅ DO configure `allowedHosts` and security settings properly

## 📋 Pre-deployment Checklist

- [ ] Server uses `StreamableHTTPServerTransport` with session management
- [ ] Tools/resources registered dynamically from imported definitions
- [ ] Authentication validated in all request handlers
- [ ] Environment variables used for all configuration
- [ ] Validation script successfully connects and lists capabilities
- [ ] Docker deployment configured with security best practices
- [ ] Error handling provides meaningful responses
- [ ] Session-specific clients initialized properly
- [ ] All hardcoded values replaced with environment variables

## 🔧 Development Commands

```bash
# Development
npm run dev          # Start with hot reload
npm run build        # TypeScript compilation
npm run test         # Run validation tests

# Validation
node validate-simple.js     # Quick validation
./validate-bash.sh         # Command-line validation

# Deployment
docker build -t mcp-server .
docker run -p 3000:3000 --env-file .env mcp-server
```

## 📚 Reference Implementation

Refer to `mcp-servers/auth-mcp-server/` for the canonical implementation that demonstrates all these patterns correctly.

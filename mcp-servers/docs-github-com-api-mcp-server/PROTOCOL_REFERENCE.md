# MCP Protocol Implementation Reference

This document captures the exact patterns and implementations that work correctly with the MCP TypeScript SDK, based on our validated auth-mcp-server implementation.

## 🎯 Core Protocol Rules

### 1. Server Architecture

**REQUIRED PATTERN:**
```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';

// Server initialization
const server = new McpServer({
  name: 'your-server-name',
  version: '1.0.0',
});

// Transport with session management
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => randomUUID(),
  onsessioninitialized: id => {
    console.error(`[${id}] Session initialized`);
    // Store session reference
  },
  enableDnsRebindingProtection: false, // For production
  allowedHosts: [] // Configure based on deployment
});
```

### 2. Session Management

**CRITICAL:** Sessions are managed by the transport, not the application:

```typescript
// Session storage (stateful mode)
const sessions: Map<string, SessionData> = new Map();

// Initialize clients per session
function initializeSessionClients(sessionId: string): SessionData {
  const session = {
    // ... client initialization
    sessionId,
    initialized: true,
  };
  
  sessions.set(sessionId, session);
  return session;
}
```

### 3. HTTP Request Handling

**EXACT PATTERN** for POST /mcp endpoint:

```typescript
app.post('/mcp', validateApiKey, async (req: Request, res: Response) => {
  const sessionId = req.headers['mcp-session-id'] as string | undefined;
  let transport: StreamableHTTPServerTransport;
  let server: McpServer;

  if (sessionId && transports[sessionId]) {
    // Reuse existing session
    transport = transports[sessionId];
  } else if (!sessionId && isInitializeRequest(req.body)) {
    // Create new session for initialize request
    const newSessionId = randomUUID();
    const session = initializeSessionClients(newSessionId);
    server = createMCPServer(newSessionId);
    
    transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => newSessionId,
      onsessioninitialized: id => {
        transports[id] = transport;
      },
      // ... other options
    });
    
    await server.connect(transport);
  } else {
    // Invalid request
    return res.status(400).json({
      jsonrpc: '2.0',
      error: { code: -32000, message: 'Bad Request: No valid session ID provided' },
      id: null,
    });
  }

  // Handle the request
  await transport.handleRequest(req, res, req.body);
});
```

### 4. Tool Registration

**REQUIRED PATTERN:**
```typescript
// Tool definition structure
interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: JSONSchema;
}

// Dynamic registration
function registerTools(server: McpServer, session: SessionData) {
  const toolMethods: { [key: string]: (args: any) => Promise<any> } = {
    'tool_name': (args) => client.methodName(args),
  };

  for (const tool of toolDefinitions) {
    const methodHandler = toolMethods[tool.name];
    if (methodHandler) {
      const zodSchema = jsonSchemaToZod(tool.inputSchema);
      server.registerTool(tool.name, {
        description: tool.description,
        inputSchema: zodSchema
      }, async (args: any) => {
        try {
          const result = await methodHandler(args);
          return {
            content: [{
              type: "text" as const,
              text: JSON.stringify(result, null, 2)
            }]
          };
        } catch (error: any) {
          return {
            content: [{
              type: "text" as const,
              text: `Error executing ${tool.name}: ${error.message}`
            }],
            isError: true
          };
        }
      });
    }
  }
}
```

### 5. Resource Registration

**REQUIRED PATTERN:**
```typescript
// Resource definition structure
interface ResourceDefinition {
  name: string;
  uri: string;
  description: string;
  mimeType: string;
}

// Dynamic registration with templates
function registerResources(server: McpServer, session: SessionData) {
  const resourceHandlers: { [key: string]: (uri: URL, params: any) => Promise<any> } = {
    'resource://pattern': async (uri, params) => {
      return await client.fetchData(params);
    },
  };

  for (const resource of resourceDefinitions) {
    const handler = resourceHandlers[resource.uri];
    if (handler) {
      if (resource.uri.includes('{')) {
        // Template resource
        server.registerResource(
          resource.name.toLowerCase().replace(/\s+/g, '-'),
          new ResourceTemplate(resource.uri, { list: undefined }),
          { title: resource.name, description: resource.description, mimeType: resource.mimeType },
          async (uri, params) => {
            const result = await handler(uri, params);
            return {
              contents: [{
                uri: uri.href,
                text: JSON.stringify(result, null, 2),
                mimeType: resource.mimeType,
              }]
            };
          }
        );
      } else {
        // Static resource
        server.registerResource(
          resource.name.toLowerCase().replace(/\s+/g, '-'),
          resource.uri,
          { title: resource.name, description: resource.description, mimeType: resource.mimeType },
          async (uri) => {
            const result = await handler(uri, {});
            return {
              contents: [{
                uri: uri.href,
                text: JSON.stringify(result, null, 2),
                mimeType: resource.mimeType,
              }]
            };
          }
        );
      }
    }
  }
}
```

## 🔒 Authentication Patterns

### API Key Authentication

**EXACT MIDDLEWARE PATTERN:**
```typescript
function validateApiKey(req: Request, res: Response, next: any) {
  const requiredApiKey = process.env.API_KEY;
  
  if (!requiredApiKey) {
    console.error('Warning: No API_KEY configured - authentication disabled');
    return next();
  }
  
  const providedApiKey = req.headers['api_key'] as string;
  
  if (!providedApiKey) {
    return res.status(401).json({
      jsonrpc: '2.0',
      error: { code: -32001, message: 'Authentication required: Missing API_KEY header' },
      id: null,
    });
  }
  
  if (providedApiKey !== requiredApiKey) {
    return res.status(401).json({
      jsonrpc: '2.0',
      error: { code: -32001, message: 'Authentication failed: Invalid API_KEY' },
      id: null,
    });
  }
  
  next();
}
```

## 🌐 Client Implementation Patterns

### StreamableHTTPClientTransport Usage

**EXACT PATTERN:**
```typescript
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';

// Transport creation
const transport = new StreamableHTTPClientTransport(new URL(mcpUrl), {
  requestInit: {
    headers: {
      'API_KEY': apiKey
    }
  }
});

// Client creation
const client = new Client({
  name: 'client-name',
  version: '1.0.0'
}, {
  capabilities: {
    resources: {},
    tools: {}
  }
});

// Connection
await client.connect(transport);

// Session ID is automatically managed by the transport
console.log(`Session ID: ${transport.sessionId}`);
```

## ⚠️ Common Pitfalls

1. **Headers**: Use `requestInit.headers` for StreamableHTTPClientTransport, NOT a separate headers parameter
2. **Session Management**: Never manually manage session IDs - let the transport handle it
3. **Tool Registration**: Always convert JSON Schema to Zod before registering tools
4. **Error Handling**: Always return proper JSON-RPC error format
5. **Resource Templates**: Use `ResourceTemplate` for parameterized URIs
6. **Environment Variables**: Always provide fallbacks and clear error messages

## 🧪 Validation Requirements

Every MCP server implementation MUST:

1. ✅ Pass health check endpoint test
2. ✅ Handle unauthenticated requests properly (401)
3. ✅ Accept authenticated initialize requests
4. ✅ Generate and manage session IDs
5. ✅ List all registered tools and resources
6. ✅ Handle tool calls with proper validation
7. ✅ Serve resources with correct MIME types
8. ✅ Return proper JSON-RPC responses

Use the validation scripts in `/validation/` to verify compliance.

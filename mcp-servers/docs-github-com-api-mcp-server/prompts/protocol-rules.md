# MCP Protocol Compliance Rules

These are the absolute requirements for MCP protocol compliance based on our validated implementations.

## 🔒 Non-Negotiable Protocol Rules

### 1. Transport Layer Compliance

**RULE**: MUST use StreamableHTTP transports for HTTP-based MCP servers/clients

```typescript
// SERVER (REQUIRED)
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';

// CLIENT (REQUIRED)
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
```

**VIOLATION EXAMPLES:**
- ❌ Using raw HTTP servers (Express, Fastify, etc.)
- ❌ Custom WebSocket implementations
- ❌ Non-MCP transport protocols

### 2. Session Management Compliance

**RULE**: Sessions MUST be managed by the transport layer

```typescript
// CORRECT: Transport handles sessions
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => randomUUID(),
  onsessioninitialized: (sessionId) => {
    // Store session-specific data here
    sessions.set(sessionId, initializeSession(sessionId));
  }
});

// VIOLATION: Manual session handling
app.post('/session', (req, res) => { /* ❌ Wrong approach */ });
```

### 3. Request Handler Compliance

**RULE**: MUST use MCP server's `setRequestHandler` method

```typescript
// CORRECT: MCP request handlers
server.setRequestHandler(ListToolsRequest, async () => ({
  tools: Object.values(toolDefinitions)
}));

server.setRequestHandler(CallToolRequest, async (request) => {
  // Handle tool call
});

// VIOLATION: Direct HTTP route handling
app.get('/tools', (req, res) => { /* ❌ Wrong approach */ });
```

### 4. Authentication Protocol Compliance

**RULE**: Authentication MUST be handled via HTTP headers in transport

```typescript
// CLIENT: Headers in requestInit
const transport = new StreamableHTTPClientTransport({
  url: serverUrl,
  requestInit: {
    headers: { 'x-api-key': apiKey }
  }
});

// SERVER: Validate headers in request handlers
const headers = (request as any).headers || new Headers();
const apiKey = headers.get('x-api-key');
```

**VIOLATIONS:**
- ❌ URL parameters for authentication
- ❌ Request body authentication
- ❌ Custom authentication middleware outside MCP

### 5. Capability Declaration Compliance

**RULE**: Server capabilities MUST be declared properly

```typescript
// REQUIRED: Server metadata
const server = new McpServer({
  name: 'server-name',        // REQUIRED
  version: '1.0.0',          // REQUIRED
});

// REQUIRED: List handlers for all capability types
server.setRequestHandler(ListToolsRequest, async () => ({
  tools: [...] // Must return array of tool definitions
}));

server.setRequestHandler(ListResourcesRequest, async () => ({
  resources: [...] // Must return array of resource definitions
}));
```

## 📋 Protocol Message Compliance

### Tool Response Format

**RULE**: Tool responses MUST follow MCP CallToolResult schema

```typescript
// CORRECT: Valid MCP tool response
return {
  content: [
    { type: 'text', text: 'Response text' },
    { type: 'image', data: 'base64data', mimeType: 'image/png' }
  ]
};

// ACCEPTABLE: Error response
return {
  content: [{ type: 'text', text: 'Error message' }],
  isError: true
};

// VIOLATION: Invalid response format
return { result: 'text' }; // ❌ Wrong schema
```

### Resource Response Format

**RULE**: Resource responses MUST follow MCP ReadResourceResult schema

```typescript
// CORRECT: Valid MCP resource response
return {
  contents: [
    { uri: 'resource://path', mimeType: 'text/plain', text: 'content' }
  ]
};

// VIOLATION: Wrong content structure
return { data: 'content' }; // ❌ Wrong schema
```

## 🔧 Development Process Compliance

### 1. Environment Variable Usage

**RULE**: ALL configuration MUST use environment variables

```typescript
// REQUIRED: Environment validation
const requiredVars = ['API_KEY', 'PORT'];
const missingVars = requiredVars.filter(v => !process.env[v]);
if (missingVars.length > 0) {
  console.error(`Missing: ${missingVars.join(', ')}`);
  process.exit(1);
}

// VIOLATION: Hardcoded values
const apiKey = 'hardcoded-key'; // ❌ Security violation
const port = 3000; // ❌ Should use process.env.PORT
```

### 2. Validation Script Compliance

**RULE**: ALL servers MUST be testable with MCP SDK client

```typescript
// REQUIRED: Client validation pattern
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

async function validateServer() {
  const transport = new StreamableHTTPClientTransport({
    url: serverUrl,
    requestInit: { headers: authHeaders }
  });
  
  const client = new Client(
    { name: 'validator', version: '1.0.0' },
    { capabilities: {} }
  );
  
  await client.connect(transport);
  
  // MUST test all capabilities
  await client.listTools();
  await client.listResources();
  await client.listPrompts();
  
  await client.close();
}
```

### 3. Registration Pattern Compliance

**RULE**: Dynamic registration MUST separate definitions from handlers

```typescript
// CORRECT: Separated concerns
// File: tools/definitions.ts
export const toolDefinitions = { /* ... */ };

// File: tools/handlers.ts
export const toolHandlers = { /* ... */ };

// File: registrations.ts
export function registerCapabilities(server: McpServer) {
  // Dynamic registration logic
}

// VIOLATION: Mixed concerns
server.setRequestHandler(CallToolRequest, async (request) => {
  if (request.params.name === 'hardcoded-tool') { /* ❌ Wrong */ }
});
```

## 🚫 Protocol Violations That Break Compatibility

### 1. Transport Protocol Violations
- Using non-MCP HTTP implementations
- Custom WebSocket protocols
- Raw TCP connections
- GraphQL or REST API endpoints

### 2. Session Management Violations
- Manual session creation/management
- Storing sessions in external databases
- Cross-session data sharing without proper isolation
- Ignoring transport-provided session IDs

### 3. Authentication Violations
- URL-based authentication
- Body-based authentication
- Custom JWT implementations outside MCP headers
- Session-based authentication without MCP session support

### 4. Message Format Violations
- Non-standard response schemas
- Missing required fields
- Incorrect MIME types
- Invalid JSON-RPC format

### 5. Capability Declaration Violations
- Missing list handlers
- Incorrect capability metadata
- Static capability lists
- Undeclared capabilities

## ✅ Compliance Verification Checklist

### Server Compliance
- [ ] Uses `StreamableHTTPServerTransport`
- [ ] Implements session management via transport
- [ ] Uses `setRequestHandler` for all endpoints
- [ ] Validates authentication in headers
- [ ] Returns proper MCP response schemas
- [ ] Declares capabilities correctly
- [ ] Uses environment variables for all config

### Client Compliance
- [ ] Uses `StreamableHTTPClientTransport`
- [ ] Includes authentication in `requestInit.headers`
- [ ] Handles MCP response schemas correctly
- [ ] Connects and disconnects properly
- [ ] Tests all server capabilities

### Development Compliance
- [ ] Validation script using MCP SDK client passes
- [ ] No hardcoded configuration values
- [ ] Proper error handling with MCP error format
- [ ] Session isolation implemented correctly
- [ ] Dynamic registration pattern followed

### Deployment Compliance
- [ ] Environment variables documented
- [ ] Docker deployment configured
- [ ] Security best practices implemented
- [ ] Health checks available
- [ ] Logging includes session information

## 🔗 Reference Implementations

- **Server**: `mcp-servers/auth-mcp-server/` (canonical reference)
- **Client**: `test-auth-mcp-with-session.js` (SDK client validation)
- **Patterns**: `templates/mcp-server-template/SDK_PATTERNS.md`

Any deviation from these rules may result in MCP client incompatibility or protocol violations.

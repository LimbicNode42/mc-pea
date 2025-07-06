# MCP SDK Usage Patterns

This document contains proven patterns for using the MCP TypeScript SDK, based on our validated implementations.

## 🏗️ Core SDK Import Patterns

### Server-Side Imports
```typescript
// REQUIRED: Core server and transport
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';

// REQUIRED: Types for strong typing
import {
  CallToolRequest,
  CallToolResult,
  ListToolsRequest,
  ListResourcesRequest,
  ReadResourceRequest,
  ReadResourceResult,
  GetPromptRequest,
  GetPromptResult,
} from '@modelcontextprotocol/sdk/types.js';

// UTILITY: For session IDs
import { randomUUID } from 'crypto';
```

### Client-Side Imports (Validation)
```typescript
// REQUIRED: Client and transport
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
```

## 🔧 Dynamic Registration Pattern

### Tool Registration System
```typescript
// Define tool schema
export const toolDefinitions = {
  tool_name: {
    name: 'tool_name',
    description: 'Tool description',
    inputSchema: {
      type: 'object',
      properties: {
        param: { type: 'string', description: 'Parameter description' }
      },
      required: ['param']
    }
  }
};

// Define tool handlers
export const toolHandlers = {
  tool_name: async (args: any, sessionId: string) => {
    // Handler implementation
    return { content: [{ type: 'text', text: 'Result' }] };
  }
};

// Register dynamically
function registerToolsAndResources(server: McpServer) {
  // Register all tools
  Object.values(toolDefinitions).forEach(tool => {
    server.setRequestHandler(CallToolRequest, async (request) => {
      if (request.params.name === tool.name) {
        const sessionId = (request as any).sessionId || 'default';
        return await toolHandlers[tool.name](request.params.arguments, sessionId);
      }
    });
  });
  
  // Register list handler
  server.setRequestHandler(ListToolsRequest, async () => ({
    tools: Object.values(toolDefinitions)
  }));
}
```

## 🔐 Authentication Patterns

### API Key Middleware
```typescript
// Header-based authentication
const isValidApiKey = (headers: Headers): boolean => {
  const apiKey = headers.get('x-api-key') || headers.get('authorization')?.replace('Bearer ', '');
  return apiKey === process.env.API_KEY;
};

// Validate in request handlers
server.setRequestHandler(CallToolRequest, async (request) => {
  const headers = (request as any).headers || new Headers();
  if (!isValidApiKey(headers)) {
    throw new Error('Unauthorized: Invalid API key');
  }
  // ... handler logic
});
```

### Environment Variable Patterns
```typescript
// REQUIRED: Environment validation
const requiredEnvVars = ['API_KEY', 'PORT'];
const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
if (missingVars.length > 0) {
  console.error(`Missing required environment variables: ${missingVars.join(', ')}`);
  process.exit(1);
}

// PATTERN: Default values with validation
const config = {
  port: parseInt(process.env.PORT || '3000'),
  apiKey: process.env.API_KEY!,
  nodeEnv: process.env.NODE_ENV || 'development',
};
```

## 🚀 Client Validation Pattern

### MCP SDK Client Setup
```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

async function validateMCPServer() {
  const serverUrl = process.env.MCP_SERVER_URL || 'http://localhost:3000';
  const apiKey = process.env.API_KEY;
  
  // REQUIRED: Headers for authentication
  const headers = apiKey ? { 'x-api-key': apiKey } : {};
  
  // Create transport with headers
  const transport = new StreamableHTTPClientTransport({
    url: serverUrl,
    requestInit: { headers }
  });
  
  // Connect client
  const client = new Client({
    name: 'validation-client',
    version: '1.0.0'
  }, {
    capabilities: {}
  });
  
  try {
    await client.connect(transport);
    
    // Test capabilities
    const tools = await client.listTools();
    const resources = await client.listResources();
    
    console.log('✅ MCP Server validation successful');
    console.log(`📋 Tools: ${tools.tools?.length || 0}`);
    console.log(`📚 Resources: ${resources.resources?.length || 0}`);
    
  } finally {
    await client.close();
  }
}
```

## 🎯 Error Handling Patterns

### Graceful Error Responses
```typescript
// Tool error handling
async function handleToolCall(request: CallToolRequest): Promise<CallToolResult> {
  try {
    // Tool logic here
    return {
      content: [{ type: 'text', text: 'Success result' }]
    };
  } catch (error) {
    console.error('Tool error:', error);
    return {
      content: [{
        type: 'text',
        text: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
      }],
      isError: true
    };
  }
}
```

### Transport Error Handling
```typescript
// Server startup with error handling
async function startServer() {
  try {
    await server.connect(transport);
    console.log(`🚀 MCP Server running on port ${port}`);
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}
```

## 📦 Docker Deployment Patterns

### Multi-stage Dockerfile
```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Runtime stage
FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Security: Non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S mcp -u 1001
USER mcp

EXPOSE 3000
CMD ["npm", "start"]
```

## 🔍 Validation Checklist

### Server Implementation
- [ ] Uses `StreamableHTTPServerTransport` for HTTP transport
- [ ] Implements session management with `sessionIdGenerator`
- [ ] Registers tools/resources dynamically using imported definitions
- [ ] Validates API keys in request headers
- [ ] Uses environment variables for all configuration
- [ ] Handles errors gracefully with proper MCP response format

### Client Implementation
- [ ] Uses `StreamableHTTPClientTransport` for HTTP requests
- [ ] Includes authentication headers in `requestInit`
- [ ] Tests all server capabilities (tools, resources, prompts)
- [ ] Handles connection errors and cleanup properly
- [ ] Uses environment variables for server URL and credentials

### Deployment
- [ ] Dockerfile uses multi-stage build for security
- [ ] Environment variables are documented in `.env.example`
- [ ] Production deployment uses non-root user
- [ ] Health check endpoint is available
- [ ] Logs are structured and include session information

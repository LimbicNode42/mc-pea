---
applyTo: 'mcp-servers/**/*.ts'
description: 'MCP protocol compliance requirements and TypeScript implementation standards'
---

# MCP Protocol Compliance Instructions

## 🚨 CRITICAL PROTOCOL REQUIREMENTS

**When template patterns don't cover your specific use case, reference the official MCP TypeScript SDK**: https://github.com/modelcontextprotocol/typescript-sdk

### SDK Reference Guidelines
- Check `/examples/` for official implementation patterns
- Review `/src/` for SDK internals and advanced usage
- Consult `/docs/` for protocol specifications  
- Always validate SDK patterns against template structure
- Test any SDK-derived patterns with MCP SDK client

### Transport Layer (MANDATORY)
```typescript
// ✅ CORRECT: Use MCP SDK stdio transport
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';

const server = new Server(
  {
    name: "server-name",
    version: "1.0.0"
  },
  {
    capabilities: {
      tools: {},
      resources: {}
    }
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);

// ❌ FORBIDDEN: Custom HTTP servers
// Never create Express/HTTP servers for MCP
```

### Tool Registration (MANDATORY)
```typescript
// ✅ CORRECT: Use server.registerTool()
server.registerTool(
  {
    name: "tool_name",
    description: "Clear description of what this tool does",
    inputSchema: {
      type: "object",
      properties: {
        param1: {
          type: "string",
          description: "Description of parameter"
        }
      },
      required: ["param1"]
    }
  },
  async (params) => {
    // Implementation here
    return {
      content: [
        {
          type: "text",
          text: "Response content"
        }
      ]
    };
  }
);

// ❌ FORBIDDEN: setRequestHandler()
// Never use setRequestHandler for tools
```

### Resource Registration (MANDATORY)
```typescript
// ✅ CORRECT: Use server.registerResource()
server.registerResource(
  {
    uri: "resource://namespace/resource-name",
    name: "Resource Name",
    description: "Resource description"
  },
  async (uri) => {
    return {
      contents: [
        {
          uri,
          mimeType: "text/plain",
          text: "Resource content"
        }
      ]
    };
  }
);
```

## 📝 TypeScript Implementation Standards

### Type Safety Requirements
```typescript
// Import proper types from MCP SDK
import {
  Tool,
  Resource,
  TextContent,
  McpError,
  ErrorCode
} from '@modelcontextprotocol/sdk/types.js';

// Define tool parameter interfaces
interface ToolParams {
  param1: string;
  param2?: number;
}

// Use proper error handling
if (!params.param1) {
  throw new McpError(
    ErrorCode.InvalidParams,
    "Required parameter 'param1' is missing"
  );
}
```

### Error Handling Patterns
```typescript
// ✅ CORRECT: Use MCP error codes
import { McpError, ErrorCode } from '@modelcontextprotocol/sdk/types.js';

try {
  // Tool implementation
} catch (error) {
  if (error instanceof McpError) {
    throw error; // Re-throw MCP errors
  }
  
  // Convert other errors to MCP errors
  throw new McpError(
    ErrorCode.InternalError,
    `Tool execution failed: ${error.message}`
  );
}
```

### Input Validation Requirements
```typescript
// ✅ MANDATORY: Validate all inputs
function validateToolParams(params: any): ToolParams {
  if (!params || typeof params !== 'object') {
    throw new McpError(
      ErrorCode.InvalidParams,
      "Parameters must be an object"
    );
  }
  
  if (!params.param1 || typeof params.param1 !== 'string') {
    throw new McpError(
      ErrorCode.InvalidParams,
      "param1 must be a non-empty string"
    );
  }
  
  return params as ToolParams;
}
```

## 🔒 Security Requirements

### Authentication Integration
```typescript
// ✅ REQUIRED: Integrate with Keycloak and Infisical
import { validateKeycloakToken } from './auth/keycloak.js';
import { getSecret } from './secrets/infisical.js';

// Validate session/token before tool execution
async function executeWithAuth(params: any, context: any) {
  const token = context.session?.token;
  if (!token) {
    throw new McpError(
      ErrorCode.InvalidRequest,
      "Authentication required"
    );
  }
  
  const isValid = await validateKeycloakToken(token);
  if (!isValid) {
    throw new McpError(
      ErrorCode.InvalidRequest,
      "Invalid or expired token"
    );
  }
  
  // Proceed with tool execution
}
```

### Input Sanitization
```typescript
// ✅ MANDATORY: Sanitize all inputs
function sanitizeInput(input: string): string {
  // Remove potential injection patterns
  return input
    .replace(/[<>'"]/g, '') // Basic XSS prevention
    .replace(/;|--|\/\*/g, '') // SQL injection prevention
    .trim();
}
```

## 📊 Response Format Standards

### Tool Response Format
```typescript
// ✅ CORRECT: Proper response structure
return {
  content: [
    {
      type: "text",
      text: "Response content here"
    }
  ]
};

// For structured data
return {
  content: [
    {
      type: "text", 
      text: JSON.stringify(responseData, null, 2)
    }
  ]
};
```

### Resource Response Format
```typescript
// ✅ CORRECT: Resource response structure
return {
  contents: [
    {
      uri: requestedUri,
      mimeType: "application/json", // or appropriate type
      text: JSON.stringify(resourceData)
    }
  ]
};
```

## 🧪 Testing Requirements

### MCP SDK Client Testing
```typescript
// ✅ REQUIRED: Test with MCP SDK client
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

// Test tool invocation
const client = new Client(
  { name: "test-client", version: "1.0.0" },
  { capabilities: {} }
);

const transport = new StdioClientTransport({
  command: "node",
  args: ["dist/index.js"]
});

await client.connect(transport);

// Test tool execution
const result = await client.request(
  {
    method: "tools/call",
    params: {
      name: "tool_name",
      arguments: { param1: "test_value" }
    }
  }
);
```

## ❌ Common Violations to Avoid

### Protocol Violations
- Creating HTTP/Express servers instead of using stdio transport
- Using `setRequestHandler()` instead of `registerTool()`
- Malformed JSON-RPC messages
- Missing capability announcements

### Implementation Anti-Patterns
- Hardcoded credentials or secrets
- Missing input validation
- Improper error handling
- Non-standard response formats

### Security Violations
- Bypassing authentication checks
- SQL injection vulnerabilities
- XSS vulnerabilities
- Information disclosure in error messages

## ✅ Compliance Checklist

Before considering implementation complete:
- [ ] Uses `StdioServerTransport` for communication
- [ ] All tools registered with `server.registerTool()`
- [ ] All resources registered with `server.registerResource()`
- [ ] Proper TypeScript types imported and used
- [ ] Input validation on all parameters
- [ ] MCP error codes for all error scenarios
- [ ] Authentication integration implemented
- [ ] Security measures in place
- [ ] MCP SDK client testing completed
- [ ] Response formats follow MCP standards

Every implementation must pass MCP SDK client testing - this is the definitive validation of protocol compliance.

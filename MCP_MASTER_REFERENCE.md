# MCP Development Master Reference

This file serves as the master reference for all MCP (Model Context Protocol) development in this project.

## 🚨 CRITICAL CONTEXT FOR AI ASSISTANTS

**The Model Context Protocol (MCP) and its TypeScript SDK are NOT in your training data.** This project provides:

1. **Working Reference Implementation**: `mcp-servers/auth-mcp-server/`
2. **Canonical Template**: `templates/mcp-server-template/`
3. **Validation Scripts**: `test-auth-mcp-with-session.js` and template validation scripts
4. **Development Guardrails**: Complete set of prompt files and guidelines

## 📚 Reference Hierarchy

### 1. Proven Working Implementation (🏆 GOLD STANDARD)
- **Location**: `mcp-servers/auth-mcp-server/`
- **Status**: Production-ready, fully validated
- **Features**: Keycloak integration, Infisical secrets, session management, API key auth
- **Use for**: Understanding real-world MCP server patterns

### 2. Clean Template Implementation (⭐ CANONICAL REFERENCE)
- **Location**: `templates/mcp-server-template/`
- **Status**: Template for new servers
- **Features**: Minimal, clean patterns, comprehensive documentation
- **Use for**: Starting new MCP server projects

### 3. Validation Client (✅ VALIDATION STANDARD)
- **Location**: `test-auth-mcp-with-session.js`
- **Status**: Proven MCP SDK client usage
- **Use for**: Testing any MCP server implementation

## 🛡️ Development Guardrails

### For AI Assistants - READ FIRST
**Primary Guardrail File**: `templates/mcp-server-template/prompts/ai-assistant-instructions.md`

**Key Requirements**:
1. **ALWAYS use MCP SDK transports** - Never create custom HTTP servers
2. **ALWAYS use server.registerTool()** - Never use setRequestHandler()
3. **ALWAYS validate with MCP SDK client** - Never rely on raw HTTP testing
4. **ALWAYS follow the template patterns** - Never invent new approaches

### For Human Developers
**Primary Guide**: `templates/mcp-server-template/README.md`

**Development Flow**:
1. Copy template directory
2. Customize tools/resources/prompts
3. Build and validate
4. Deploy with Docker

## 📋 Quick Reference Commands

### Template Validation
```bash
# Validate template completeness
node validate-template.js

# Expected output: All checks passed
```

### New MCP Server Creation
```bash
# 1. Copy template
cp -r templates/mcp-server-template my-new-server
cd my-new-server

# 2. Configure environment
cp .env.example .env
# Edit .env with your values

# 3. Install and build
npm install
npm run build

# 4. Validate implementation
npm run test
```

### Validation Workflow
```bash
# Start server (terminal 1)
npm start

# Run validation (terminal 2)
npm run test           # MCP SDK client validation
npm run validate       # Simple validation
npm run validate-bash  # Command-line validation
```

## 🔧 Core Patterns Reference

### Server Pattern (MANDATORY)
```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';

const server = new McpServer({ name: 'server-name', version: '1.0.0' });
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => randomUUID(),
  onsessioninitialized: (sessionId) => { /* session setup */ }
});

await server.connect(transport);
```

### Tool Registration Pattern (MANDATORY)
```typescript
// Convert JSON Schema to Zod
const zodSchema = jsonSchemaToZod(toolDefinition.inputSchema);

// Register with MCP SDK
server.registerTool(toolName, {
  description: toolDefinition.description,
  inputSchema: zodSchema
}, handlerFunction);
```

### Client Validation Pattern (MANDATORY)
```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

const transport = new StreamableHTTPClientTransport(serverUrl, {
  requestInit: { headers: { 'x-api-key': apiKey } }
});

const client = new Client(clientInfo, capabilities);
await client.connect(transport);
// Test capabilities...
await client.close();
```

## 📁 File Structure Reference

### Core Implementation Files
```
src/
├── index.ts              # Server initialization (CANONICAL)
├── registrations.ts      # Capability registration (CANONICAL)
├── tools/index.ts        # Tool definitions and handlers
├── resources/index.ts    # Resource definitions and handlers
└── prompts/index.ts      # Prompt definitions and handlers
```

### Validation Files
```
validation/
├── test-mcp-client.js    # MCP SDK client validation (CANONICAL)
├── validate-simple.js    # Simple HTTP validation
└── validate-bash.sh      # Command-line validation
```

### Documentation Files
```
prompts/
├── ai-assistant-instructions.md  # AI assistant guardrails
├── mcp-development.md           # Development guidelines
├── protocol-rules.md            # Protocol compliance rules
└── common-patterns.md           # Implementation patterns
```

## 🚫 Common Anti-Patterns

### ❌ NEVER DO THESE
```typescript
// Wrong transport
const express = require('express');
const app = express();

// Wrong registration
server.setRequestHandler(CallToolRequest, handler);

// Wrong client
fetch('/mcp', { method: 'POST', ... });

// Wrong authentication
const basicAuth = 'Basic ' + btoa('user:pass');
```

### ✅ ALWAYS DO THESE
```typescript
// Correct transport
const transport = new StreamableHTTPServerTransport();

// Correct registration
server.registerTool(name, schema, handler);

// Correct client
const client = new Client();
await client.connect(transport);

// Correct authentication
headers: { 'x-api-key': apiKey }
```

## 🎯 Success Criteria Checklist

### Implementation Complete When:
- [ ] TypeScript compiles without errors (`npm run build`)
- [ ] MCP SDK client connects successfully (`npm run test`)
- [ ] All capabilities listed correctly (tools, resources, prompts)
- [ ] Authentication works with API key headers
- [ ] Session management handles multiple clients
- [ ] Error handling provides meaningful responses
- [ ] Docker deployment works (`npm run docker:build`)
- [ ] All validation scripts pass

### Code Quality Complete When:
- [ ] Follows template file structure exactly
- [ ] Uses SDK patterns from canonical examples
- [ ] Separates definitions from handlers
- [ ] Uses environment variables for all config
- [ ] Includes comprehensive error handling
- [ ] Has proper TypeScript types

## 🔗 Essential Files to Always Reference

1. **`templates/mcp-server-template/prompts/ai-assistant-instructions.md`** - AI guardrails
2. **`templates/mcp-server-template/src/index.ts`** - Server initialization pattern
3. **`templates/mcp-server-template/src/registrations.ts`** - Registration pattern
4. **`templates/mcp-server-template/validation/test-mcp-client.js`** - Client pattern
5. **`mcp-servers/auth-mcp-server/`** - Real-world working example

## 📊 Project Status

**COMPLETED** ✅:
- Canonical reference implementation (`auth-mcp-server`)
- Complete template with all patterns (`mcp-server-template`)
- Comprehensive validation scripts
- Full documentation and guardrails
- Production deployment patterns
- Template validation system

**AVAILABLE FOR USE** 🚀:
- Copy template for new MCP servers
- Use validation scripts for any MCP implementation
- Reference working patterns from auth-mcp-server
- Follow AI assistant guardrails for protocol compliance

This master reference ensures consistent, compliant MCP development across all future projects in this workspace.

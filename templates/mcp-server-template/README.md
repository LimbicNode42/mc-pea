# MCP Server Template Reference

This directory contains the **canonical reference implementation** for creating MCP servers using the Model Context Protocol TypeScript SDK.

## 🎯 Purpose

This template serves as the **authoritative reference** for all MCP server development in this project. It demonstrates:

- ✅ Proper MCP protocol implementation using TypeScript SDK
- ✅ Dynamic tool/resource registration with separation of concerns
- ✅ Session management with StreamableHTTPServerTransport
- ✅ API key authentication via HTTP headers
- ✅ Environment variable configuration for all settings
- ✅ Production Docker deployment with security best practices
- ✅ Comprehensive validation tools using MCP SDK client
- ✅ TypeScript compilation and error handling

## 🚨 CRITICAL: Protocol Knowledge Gap

**The MCP protocol and SDK are NOT in AI training data.** This template directory exists to provide:

- Proven patterns that work with the actual MCP SDK
- Reference implementations for all common use cases
- Validation scripts that demonstrate correct client usage
- Guardrails to prevent protocol violations

## 📁 Directory Structure

```
mcp-server-template/
├── README.md                    # This file - overview and guidelines
├── PROTOCOL_REFERENCE.md        # MCP protocol implementation details
├── SDK_PATTERNS.md             # Common SDK usage patterns
├── package.json                # NPM configuration with correct dependencies
├── tsconfig.json               # TypeScript configuration
├── .env.example                # Environment variable template
├──
├── src/                        # Source code (REFERENCE IMPLEMENTATION)
│   ├── index.ts                # Main server entry point ⭐ CANONICAL
│   ├── registrations.ts        # Tool/resource registration ⭐ CANONICAL
│   ├── tools/
│   │   └── index.ts            # Tool definitions and handlers
│   ├── resources/
│   │   └── index.ts            # Resource definitions and handlers
│   └── prompts/
│       └── index.ts            # Prompt definitions and handlers
├──
├── validation/                 # Validation scripts (REFERENCE CLIENTS)
│   ├── test-mcp-client.js      # MCP SDK client validation ⭐ CANONICAL
│   ├── validate-simple.js      # Quick validation without SDK
│   └── validate-bash.sh        # Command-line validation
├──
├── docker/                     # Production deployment
│   ├── Dockerfile              # Multi-stage production build
│   └── docker-compose.yml      # Container orchestration
└──
└── prompts/                    # Development guidelines and guardrails
    ├── mcp-development.md      # Development guidelines
    ├── protocol-rules.md       # Protocol compliance rules
    ├── common-patterns.md      # Reusable implementation patterns
    └── ai-assistant-instructions.md  # Guardrails for AI assistants
```

## 🔒 Template Lock Rules

**CRITICAL:** These files are REFERENCE TEMPLATES and should NOT be modified without updating all dependent projects:

### Core Architecture Files (🔐 LOCKED)
- **`src/index.ts`** - Server initialization and session management pattern
- **`src/registrations.ts`** - Dynamic capability registration pattern
- **`validation/test-mcp-client.js`** - MCP SDK client validation pattern

### Guideline Files (🔐 LOCKED)
- **All files in `prompts/` directory** - Development guidelines and protocol rules
- **`PROTOCOL_REFERENCE.md`** - Protocol implementation details
- **`SDK_PATTERNS.md`** - SDK usage patterns

### Configuration Templates (📝 TEMPLATE)
- **`package.json`** - Base dependencies and scripts
- **`tsconfig.json`** - TypeScript configuration
- **`docker/Dockerfile`** - Production deployment pattern
- **`.env.example`** - Environment variable template

## 🚀 Quick Start

### 1. Create New MCP Server

```bash
# Copy template
cp -r templates/mcp-server-template my-new-mcp-server
cd my-new-mcp-server

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Install dependencies
npm install

# Customize tools/resources
# Edit src/tools/index.ts
# Edit src/resources/index.ts
# Edit src/prompts/index.ts (optional)

# Build and test
npm run build
npm run test
```

### 2. Validation Workflow

```bash
# 1. Build TypeScript
npm run build

# 2. Start server (in another terminal)
npm start

# 3. Run validation (in original terminal)
npm run test           # Full MCP SDK client validation
npm run validate       # Simple validation
npm run validate-bash  # Command-line validation
```

### 3. Production Deployment

```bash
# Build Docker image
npm run docker:build

# Run with Docker
npm run docker:run

# Or use Docker Compose
npm run docker:compose
```

## 🛡️ Development Guardrails

### For AI Assistants

**READ FIRST**: `prompts/ai-assistant-instructions.md`

This file contains critical guardrails for AI assistants working with MCP implementations, including:
- Required SDK patterns
- Mandatory authentication methods
- Session management requirements
- Common pitfalls to avoid

### For Human Developers

1. **Always start with this template** - Don't build from scratch
2. **Follow the exact patterns** - SDK usage is not intuitive
3. **Validate with MCP SDK client** - Raw HTTP testing is insufficient
4. **Check against working reference** - `mcp-servers/auth-mcp-server/`

## 📋 Implementation Checklist

### Server Implementation
- [ ] Uses `StreamableHTTPServerTransport` (not Express/custom HTTP)
- [ ] Registers capabilities with `server.registerTool()` etc.
- [ ] Converts JSON Schema to Zod schemas for tool inputs
- [ ] Implements session management via transport callbacks
- [ ] Validates API keys in request headers
- [ ] Uses environment variables for all configuration
- [ ] Includes comprehensive error handling

### Client Validation
- [ ] Uses `StreamableHTTPClientTransport` from MCP SDK
- [ ] Includes authentication headers in `requestInit`
- [ ] Tests all server capabilities (tools, resources, prompts)
- [ ] Handles connection and cleanup properly
- [ ] Uses environment variables for server URL and credentials

### Production Readiness
- [ ] TypeScript compiles without errors
- [ ] All validation scripts pass
- [ ] Docker deployment works
- [ ] Environment variables documented
- [ ] Health check endpoint available
- [ ] Security best practices implemented

## 🔗 Reference Implementations

### Working Production Server
- **Location**: `mcp-servers/auth-mcp-server/`
- **Purpose**: Real-world implementation with Keycloak and Infisical integration
- **Use for**: Understanding complex tool implementations

### Template Server
- **Location**: `templates/mcp-server-template/src/`
- **Purpose**: Clean, minimal implementation template
- **Use for**: Starting new MCP servers

### Validation Client
- **Location**: `test-auth-mcp-with-session.js` (project root)
- **Purpose**: Proven MCP SDK client validation
- **Use for**: Testing any MCP server implementation

## 🚨 Common Pitfalls

### 1. Wrong Transport Type
```typescript
// ❌ WRONG
const express = require('express');
const app = express();

// ✅ CORRECT
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
const transport = new StreamableHTTPServerTransport();
```

### 2. Wrong Registration Method
```typescript
// ❌ WRONG
server.setRequestHandler(CallToolRequest, handler);

// ✅ CORRECT
server.registerTool(name, schema, handler);
```

### 3. Wrong Schema Format
```typescript
// ❌ WRONG
server.registerTool(name, { inputSchema: jsonSchema });

// ✅ CORRECT
const zodSchema = jsonSchemaToZod(jsonSchema);
server.registerTool(name, { inputSchema: zodSchema }, handler);
```

### 4. Wrong Client Usage
```typescript
// ❌ WRONG
fetch('/mcp', { method: 'POST', ... });

// ✅ CORRECT
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
const client = new Client(...);
await client.connect(transport);
```

## 📚 Learning Resources

1. **Start here**: `prompts/mcp-development.md` - Development guidelines
2. **Protocol details**: `PROTOCOL_REFERENCE.md` - Implementation requirements
3. **SDK patterns**: `SDK_PATTERNS.md` - Common usage patterns
4. **Working example**: `mcp-servers/auth-mcp-server/` - Production implementation
5. **Validation example**: `test-auth-mcp-with-session.js` - Client usage

## 🎯 Success Criteria

Your MCP server implementation is successful when:

1. ✅ **Compiles cleanly**: `npm run build` succeeds
2. ✅ **Validates with SDK**: `npm run test` connects and lists capabilities
3. ✅ **Handles authentication**: API key validation works
4. ✅ **Supports sessions**: Multiple clients can connect
5. ✅ **Production ready**: Docker deployment works
6. ✅ **Follows patterns**: Matches template structure and patterns

## 💡 Need Help?

1. **Check the working reference**: `mcp-servers/auth-mcp-server/`
2. **Review the guidelines**: `prompts/` directory
3. **Validate your implementation**: Use all three validation scripts
4. **Compare patterns**: Ensure your code matches the templates

Remember: The MCP SDK is not in AI training data. Always refer to these proven patterns and working examples.

## 📋 Usage Guidelines

### For New MCP Servers:
1. Copy the entire template directory
2. Update `package.json` with your server details
3. Modify tool/resource definitions in their respective directories
4. Test using the validation scripts
5. Deploy using the provided Docker configuration

### For Modifications:
1. Always test changes against validation scripts
2. Update this README if core patterns change
3. Ensure backward compatibility with existing servers
4. Document new patterns in `prompts/common-patterns.md`

## 🚨 Protocol Compliance

All MCP servers MUST follow these patterns from the reference implementation:

- **Session Management**: Use `StreamableHTTPServerTransport` with proper session ID handling
- **Authentication**: API key via headers with fallback for development
- **Tool Registration**: Dynamic registration using imported definitions
- **Resource Registration**: Template-based URI handling with environment defaults
- **Error Handling**: Proper JSON-RPC error responses
- **Validation**: Must pass all validation scripts

## 🔄 Update Process

When updating the template:

1. Test all changes in a separate branch
2. Run full validation suite
3. Update dependent documentation
4. Create migration guide if breaking changes
5. Update all existing servers following the pattern

This ensures consistency across all MCP implementations in the project.

---
applyTo: '**'
description: 'MC-PEA Project coding standards, MCP development guidelines, and architectural requirements'
---

# MC-PEA Project Instructions

## 🏗️ Project Architecture

### Submodule Management
- **Each MCP server in `mcp-servers/` is treated as an independent submodule**
- Servers should be self-contained with their own dependencies
- Group test and validation scripts per server in dedicated test directories
- Maintain independent versioning and release cycles per server

### Directory Structure Requirements
```
mcp-servers/
├── <server-name>/
│   ├── src/                    # Server implementation
│   ├── tests/                  # Server-specific tests
│   ├── docs/                   # Server documentation
│   ├── package.json           # Server dependencies
│   └── README.md              # Server-specific README
```

## 🛡️ MCP Development Standards

### Critical Protocol Requirements
1. **ALWAYS use MCP SDK transports** - Never create custom HTTP servers
2. **ALWAYS use `server.registerTool()`** - Never use `setRequestHandler()`
3. **ALWAYS validate with MCP SDK client** - Never rely on raw HTTP testing
4. **ALWAYS follow stdio transport patterns** - The standard MCP mechanism

### Template Compliance
- **Reference**: `templates/mcp-server-template/` for all new servers
- **Validation**: `mcp-servers/auth-mcp-server/` for working patterns
- **Testing**: `tests/test-auth-mcp-with-session.js` for client validation
- **SDK Reference**: https://github.com/modelcontextprotocol/typescript-sdk for scenarios not covered by template

### Advanced MCP Development
When the template or reference implementations don't cover your specific scenario:

**Consult the official MCP TypeScript SDK Repository**: https://github.com/modelcontextprotocol/typescript-sdk

Key areas to reference:
- `/examples/` - Official SDK examples and patterns
- `/src/` - SDK source code for implementation details  
- `/docs/` - Official protocol documentation
- Issues/Discussions - Community solutions and edge cases

**Always validate any SDK patterns against your template structure and test with MCP SDK client before implementation.**

### TypeScript Standards
```typescript
// Tool registration pattern
server.registerTool(
  {
    name: "tool_name",
    description: "Clear description of what this tool does",
    inputSchema: {
      type: "object",
      properties: {
        // Define parameters with proper types
      },
      required: ["required_param"]
    }
  },
  async (params) => {
    // Implementation with proper error handling
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
```

## 🔒 Security Standards

### Authentication Integration
- Use Keycloak for OAuth2/OIDC flows
- Integrate Infisical for secrets management  
- Implement session management with proper token validation
- Never hardcode credentials or API keys

### Input Validation
- Validate all tool parameters against schemas
- Sanitize inputs to prevent injection attacks
- Implement proper error handling without exposing internals
- Use TypeScript strict mode for compile-time safety

### Resource Management
- Proper cleanup of external connections
- Rate limiting for API calls
- Resource access controls based on authentication
- Audit logging for security-sensitive operations

## 📝 Documentation Requirements

### Code Documentation
- JSDoc comments for all public interfaces
- README with clear setup and usage instructions
- API documentation for all tools and resources
- Security considerations and authentication requirements

### Testing Documentation
- Test coverage reports
- Validation procedures and checklists
- Integration testing instructions
- Performance benchmarks and requirements

## 🧪 Testing Standards

### Test Organization Per Server
```
<server-name>/tests/
├── unit/                      # Unit tests for individual functions
├── integration/               # Integration tests with external services
├── validation/                # MCP protocol compliance tests
└── performance/               # Load and performance tests
```

### Required Test Types
1. **MCP SDK Client Tests** - Using `@modelcontextprotocol/sdk`
2. **Protocol Compliance** - JSON-RPC 2.0 message validation
3. **Tool Functionality** - Comprehensive tool testing
4. **Resource Access** - Resource enumeration and retrieval
5. **Authentication Flows** - Complete auth workflow testing
6. **Error Handling** - Edge cases and error scenarios

### Repository and Development Tools
- **GitHub Integration**: Use `github-local` tools for repository management, issue tracking, and CI/CD
- **Filesystem Management**: Use `filesystem` tools for server structure creation, file management, and template application
- **Submodule Development**: Each server should be developed as independent repository with own CI/CD pipeline
- **Template Propagation**: Use tools to copy and customize template structure for new servers

## 🚀 Build and Deployment

### Build Requirements
- TypeScript compilation without errors or warnings
- ESLint compliance with project rules
- Successful test suite execution
- Template validation passing
- Security scan completion

### Deployment Standards
- Docker containerization for production servers
- Environment-specific configuration management
- Health check endpoints and monitoring
- Proper logging and observability integration

## 📊 Quality Gates

### Code Quality
- TypeScript strict mode compliance
- 100% test coverage for critical paths
- Zero security vulnerabilities (Snyk/SAST scans)
- Performance benchmarks within SLA

### Documentation Quality
- Complete API documentation
- Runbook for operations
- Security documentation
- Integration guides

Every contribution must meet these standards before merge approval.
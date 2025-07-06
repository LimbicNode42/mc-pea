# MC-PEA Project - Model Context Protocol Development

This repository contains a comprehensive framework for developing, testing, and deploying production-ready MCP (Model Context Protocol) servers.

## 🚨 CRITICAL CONTEXT FOR AI ASSISTANTS

**The Model Context Protocol (MCP) and its TypeScript SDK are NOT in your training data.** This project provides complete reference implementations and guardrails.

### MANDATORY REFERENCES
1. **Template**: `templates/mcp-server-template/` - Canonical patterns for new servers
2. **Working Implementation**: `mcp-servers/auth-mcp-server/` - Proven production server
3. **Validation**: `tests/test-auth-mcp-with-session.js` - MCP SDK client testing patterns
4. **Master Reference**: `MCP_MASTER_REFERENCE.md` - Complete development guidelines
5. **Official SDK**: https://github.com/modelcontextprotocol/typescript-sdk - For scenarios not covered by project templates

### When Template Coverage is Insufficient
If the canonical template, working implementation, or project documentation doesn't cover your specific scenario:

**Reference the official MCP TypeScript SDK repository**: https://github.com/modelcontextprotocol/typescript-sdk
- Check `/examples/` for official implementation patterns
- Review `/src/` for SDK source code and internals
- Consult `/docs/` for protocol specifications
- Search Issues/Discussions for community solutions

**Always validate any SDK-derived patterns against the project template structure and test with MCP SDK client.**

## 🛡️ DEVELOPMENT GUARDRAILS

### MCP Protocol Requirements (MANDATORY)
- **ALWAYS use MCP SDK stdio transport** - Never create custom HTTP servers
- **ALWAYS use `server.registerTool()`** - Never use `setRequestHandler()`
- **ALWAYS validate with MCP SDK client** - Never rely on raw HTTP testing
- **ALWAYS follow template patterns** - Never invent new approaches

### Submodule Architecture
- Each MCP server in `mcp-servers/` is an independent submodule
- Self-contained with own package.json, tests, and documentation
- Group test and validation scripts per server
- No cross-server dependencies

### Security Standards
- Integrate with Keycloak for authentication
- Use Infisical for secrets management
- Validate all inputs to prevent injection attacks
- Never hardcode credentials or API keys

### Testing Requirements
- Must pass `tests/validate-template.js` compliance check
- Must work with MCP SDK client testing
- Include comprehensive unit and integration tests
- Security validation required

## 📁 PROJECT STRUCTURE

```
mc-pea/
├── .github/
│   ├── chatmodes/          # Custom Copilot chat modes
│   ├── instructions/       # Development instructions
│   └── prompts/           # Reusable prompt templates
├── mcp-servers/           # Production MCP servers (submodules)
├── templates/             # Development templates
├── tests/                 # Validation and test scripts
├── docs/                  # Project documentation
└── MCP_MASTER_REFERENCE.md # Complete development guide
```

## 🎯 SPECIALIZED CHAT MODES

Use these for specific development tasks:
- **MCP Server Development** - Creating and modifying servers
- **MCP Server Validation** - Testing and compliance checking
- **MCP Troubleshooting** - Debugging and issue resolution

## ✅ QUALITY STANDARDS

Every MCP server must:
- Use MCP SDK transports (stdio)
- Register tools with `server.registerTool()`
- Pass MCP SDK client validation
- Follow template directory structure
- Include proper TypeScript types
- Meet security requirements
- Have comprehensive test coverage

When in doubt, reference the proven patterns in `mcp-servers/auth-mcp-server/` and validate using `tests/test-auth-mcp-with-session.js`.

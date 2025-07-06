---
applyTo: 'mcp-servers/**'
description: 'Architectural guidelines for MCP server submodules and project organization'
---

# MCP Server Submodule Architecture

## 🏗️ Submodule Philosophy

Each MCP server in `mcp-servers/` is treated as an **independent submodule** that should be capable of:
- Standalone development and testing
- Independent versioning and releases
- Separate dependency management
- Individual deployment pipelines

## 📁 Required Directory Structure

Every MCP server must follow this exact structure:

```
mcp-servers/<server-name>/
├── src/                        # TypeScript source code
│   ├── index.ts               # Main server entry point
│   ├── tools/                 # Tool implementations
│   ├── resources/             # Resource implementations
│   └── types/                 # TypeScript type definitions
├── tests/                      # Server-specific test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   ├── validation/            # MCP compliance tests
│   └── mcp-client-test.js     # MCP SDK client validation
├── docs/                       # Server documentation
│   ├── README.md              # Setup and usage guide
│   ├── API.md                 # Tool and resource documentation
│   └── SECURITY.md            # Security considerations
├── config/                     # Configuration templates
│   ├── .env.example          # Environment variables
│   └── docker/                # Docker configuration
├── package.json               # Dependencies and scripts
├── tsconfig.json              # TypeScript configuration
├── .gitignore                 # Git ignore rules
└── README.md                  # Main server documentation
```

## 🔗 Submodule Independence

### Dependency Management
- Each server maintains its own `package.json`
- No shared dependencies between servers
- Use exact version pinning for stability
- Regular dependency updates per server

### Testing Isolation
- Each server has complete test suite
- No cross-server test dependencies
- Independent CI/CD pipelines
- Isolated test environments

### Documentation Separation
- Self-contained documentation per server
- No references to other servers
- Complete setup guides for each server
- Independent API documentation

## 🧪 Test Organization Per Server

### Test Structure Requirements
```
<server-name>/tests/
├── unit/
│   ├── tools/                 # Unit tests for each tool
│   ├── resources/             # Unit tests for each resource
│   └── utils/                 # Utility function tests
├── integration/
│   ├── external-services/     # External API integration tests
│   ├── auth-flows/           # Authentication workflow tests
│   └── end-to-end/           # Complete workflow tests
├── validation/
│   ├── mcp-compliance/       # MCP protocol validation
│   ├── template-adherence/   # Template structure validation
│   └── security/             # Security validation tests
└── performance/
    ├── load-tests/           # Load and stress tests
    └── benchmarks/           # Performance benchmarks
```

### Test Requirements
1. **MCP SDK Client Test** - Must validate server using MCP SDK
2. **Protocol Compliance** - JSON-RPC 2.0 validation
3. **Tool Coverage** - Test all registered tools
4. **Resource Coverage** - Test all registered resources
5. **Error Handling** - Test error scenarios
6. **Security Testing** - Authentication and input validation

## 📦 Package Management

### Required Scripts in package.json
```json
{
  "scripts": {
    "build": "tsc",
    "test": "npm run test:unit && npm run test:integration",
    "test:unit": "jest tests/unit",
    "test:integration": "jest tests/integration", 
    "test:validation": "jest tests/validation",
    "test:mcp": "node tests/mcp-client-test.js",
    "validate": "node ../../tests/validate-template.js .",
    "dev": "tsx src/index.ts",
    "start": "node dist/index.js"
  }
}
```

### Required Dependencies
- `@modelcontextprotocol/sdk` - MCP protocol implementation
- `typescript` - TypeScript compiler
- `tsx` - Development execution
- `jest` - Testing framework
- Server-specific dependencies as needed

## 🚀 Development Workflow

### Creating New Server
1. Copy template: `cp -r templates/mcp-server-template/ mcp-servers/<new-server>/`
2. Update package.json with server-specific details
3. Implement tools and resources following template patterns
4. Create comprehensive test suite
5. Validate with template compliance checker
6. Test with MCP SDK client

**For advanced implementation scenarios**: Reference the [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk) repository for official patterns and protocol specifications not covered by the template.

### Modifying Existing Server
1. Create feature branch in server directory
2. Implement changes following template patterns
3. Update tests to cover new functionality
4. Run full test suite including validation
5. Update documentation
6. Merge when all tests pass

### Server Release Process
1. Version bump in server's package.json
2. Complete test suite execution
3. Security scan and validation
4. Documentation review and update
5. Tag release for the specific server
6. Deploy to appropriate environments

## 🔒 Security Considerations

### Submodule Security
- Each server has independent security assessment
- Isolated secret management per server
- Separate authentication configurations
- Independent vulnerability scanning

### Shared Security Standards
- All servers must integrate with Keycloak
- All servers must use Infisical for secrets
- Consistent input validation patterns
- Unified audit logging format

## 📊 Quality Gates

Each server must independently meet:
- 100% MCP protocol compliance
- Template structure adherence > 95%
- Test coverage > 90%
- Zero critical security vulnerabilities
- Performance benchmarks within SLA
- Complete documentation

This architecture ensures each MCP server can be developed, tested, and deployed independently while maintaining consistency across the MC-PEA project.

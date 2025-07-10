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

## 🤖 AI Agent Development Standards

### Multi-Agent Architecture
- **Framework**: CrewAI for multi-agent orchestration and collaboration
- **Core AI Model**: Claude Sonnet 4 via Anthropic SDK for primary reasoning
- **UI Framework**: Streamlit for rapid prototyping and testing interfaces
- **Workflow Visualization**: Plotly for interactive workflow diagrams and process monitoring

### Architecture Separation of Concerns
- **Python Components**: AI agents, MCP server generation, publishing workflows, UI interfaces
- **TypeScript Components**: Runtime MCP servers following MCP protocol standards
- **No Runtime Interaction**: Python and TypeScript programs operate independently
- **Validation Only**: Python may invoke TypeScript for validation/testing but no runtime dependencies
- **Clear Boundaries**: Python handles generation/publishing, TypeScript handles MCP protocol execution

### Agent System Requirements
1. **Modular Design**: Each agent type in separate modules for future microservice extraction
2. **Clear Responsibilities**: Well-defined roles and boundaries for each agent
3. **Inter-Agent Communication**: Standardized message passing and coordination protocols
4. **State Management**: Persistent state handling across agent interactions
5. **Error Handling**: Graceful degradation and recovery mechanisms

### Python Development Standards
```python
# Agent class pattern
from crewai import Agent, Task, Crew
from anthropic import Anthropic

class MCPServerGeneratorAgent(Agent):
    """Agent responsible for generating MCP server code"""
    
    def __init__(self, anthropic_client: Anthropic):
        super().__init__(
            role='MCP Server Generator',
            goal='Generate production-ready MCP servers from specifications',
            backstory='Expert TypeScript developer specializing in MCP protocol',
            llm=anthropic_client,
            tools=[self.generate_server_code, self.validate_mcp_compliance]
        )
    
    def generate_server_code(self, specification: dict) -> str:
        """Generate MCP server code following MC-PEA standards"""
        # Implementation with proper error handling
        pass
```

### Terminal Command Guidelines
**CRITICAL**: When using terminal commands, follow these strict guidelines:

1. **NEVER use long commands with `-c` flag** - This causes terminal issues and hangs
   ```bash
   # ❌ WRONG - Will cause terminal to hang
   python -c "import sys; print(sys.version)"
   
   # ✅ CORRECT - Use separate script files
   echo "import sys; print(sys.version)" > temp_script.py
   python temp_script.py
   rm temp_script.py
   ```

2. **Create temporary script files for complex Python operations**
   ```bash
   # ✅ CORRECT approach for testing imports
   echo "from agents.github_agent import GitHubAgent; print('Import successful')" > test_import.py
   python test_import.py
   rm test_import.py
   ```

3. **Break down complex commands into simple steps**
   ```bash
   # ❌ WRONG - Complex chained command
   python -c "import module; result = module.function(); print(result)"
   
   # ✅ CORRECT - Simple commands
   python --version
   python -m pip list
   ```

4. **Use proper file-based testing for validation**
   ```bash
   # ✅ CORRECT - Create test file first
   cat > validate_agent.py << 'EOF'
   try:
       from agents.github_agent import GitHubAgent
       print("✅ GitHub agent import successful")
   except Exception as e:
       print(f"❌ Import failed: {e}")
   EOF
   
   python validate_agent.py
   rm validate_agent.py
   ```

5. **Avoid inline Python execution in terminal**
   - Never use `python -c` with complex code
   - Always prefer script files for multi-line operations
   - Use `echo` or `cat` to create temporary scripts
   - Clean up temporary files after use

6. **Preferred patterns for testing**
   ```bash
   # ✅ Testing imports
   echo "import module_name" > test.py && python test.py && rm test.py
   
   # ✅ Testing functionality
   cat > test_function.py << 'EOF'
   from module import function
   result = function()
   print(f"Result: {result}")
   EOF
   python test_function.py
   rm test_function.py
   ```

These guidelines prevent terminal hangs and ensure reliable command execution across different environments.

## 📚 External Documentation References

### Current Tool Versions and Documentation
> **Note**: These links should be updated regularly as the tools evolve beyond the training cutoff date.

#### Anthropic SDK
- **Latest Documentation**: https://docs.anthropic.com/en/api/getting-started
- **Python SDK**: https://github.com/anthropics/anthropic-sdk-python
- **TypeScript SDK**: https://github.com/anthropics/anthropic-sdk-typescript
- **Model Information**: https://docs.anthropic.com/en/docs/models-overview
- **Function Calling**: https://docs.anthropic.com/en/docs/tool-use

#### CrewAI
- **Official Documentation**: https://docs.crewai.com/
- **GitHub Repository**: https://github.com/joaomdmoura/crewAI
- **Getting Started**: https://docs.crewai.com/getting-started/
- **Agent Configuration**: https://docs.crewai.com/core-concepts/agents/
- **Workflow Examples**: https://docs.crewai.com/examples/

#### Streamlit
- **Official Documentation**: https://docs.streamlit.io/
- **API Reference**: https://docs.streamlit.io/library/api-reference
- **GitHub Repository**: https://github.com/streamlit/streamlit
- **Deployment Guide**: https://docs.streamlit.io/streamlit-community-cloud
- **Component Library**: https://streamlit.io/components

#### Workflow Visualization Options
- **Streamlit Flow Components**: https://github.com/streamlit/streamlit/wiki/Components
- **Plotly for Interactive Diagrams**: https://plotly.com/python/

#### Development Tools
- **Python Project Standards**: https://packaging.python.org/en/latest/
- **Poetry for Dependency Management**: https://python-poetry.org/docs/
- **pytest Documentation**: https://docs.pytest.org/
- **Black Code Formatter**: https://black.readthedocs.io/
- **mypy Type Checker**: https://mypy.readthedocs.io/

### Documentation Update Schedule
- **Monthly Review**: Check for major version updates
- **Before Implementation**: Verify API compatibility for new features
- **Version Pinning**: Use specific versions in requirements.txt/pyproject.toml
- **Breaking Changes**: Monitor changelogs for deprecations

### Integration Notes
1. **Version Compatibility**: Test agent integration with latest MCP SDK versions
2. **API Changes**: Monitor Anthropic API for new features (function calling, streaming)
3. **CrewAI Updates**: Check for new agent collaboration patterns
4. **Streamlit Features**: Leverage new UI components for better visualization
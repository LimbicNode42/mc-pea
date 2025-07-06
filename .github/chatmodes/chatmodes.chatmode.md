---
description: 'MC-PEA Project general assistance mode with access to all project documentation and standards'
tools: ['*']
---

# MC-PEA Project General Mode

You are working within the MC-PEA (Model Context Protocol - Production Enterprise Applications) project. This mode provides general assistance with project navigation, documentation, and understanding.

## 📚 Project Overview

MC-PEA is a comprehensive framework for developing, testing, and deploying production-ready MCP (Model Context Protocol) servers with enterprise-grade authentication and database integrations.

### Key Project Components
- **Templates**: `templates/mcp-server-template/` - Canonical template for new MCP servers
- **Reference Implementation**: `mcp-servers/auth-mcp-server/` - Proven working MCP server
- **Testing Framework**: `tests/` - Comprehensive validation and testing tools
- **Documentation**: `docs/` and `MCP_MASTER_REFERENCE.md` - Complete project guidance

## 🎯 Available Specialized Modes

For specific tasks, switch to these specialized chat modes:

### [MCP Server Development](./mcp-server-development.chatmode.md)
- Creating new MCP servers
- Implementing tools and resources  
- Following template patterns and guardrails

### [MCP Server Validation](./mcp-server-validation.chatmode.md)
- Testing MCP server implementations
- Protocol compliance validation
- Security and performance assessment

### [MCP Troubleshooting](./mcp-troubleshooting.chatmode.md)
- Debugging MCP server issues
- Systematic problem diagnosis
- Resolution guidance and fixes

### [MCP Repository Management](./mcp-repository-management.chatmode.md)
- Managing MCP server repositories and submodules
- Creating and organizing GitHub repositories
- Setting up CI/CD pipelines and automation
- Repository security and compliance management

## 🛡️ Critical Context

**The Model Context Protocol (MCP) is NOT in AI training data.** This project provides:
- Working reference implementations
- Canonical templates and patterns
- Comprehensive validation tools
- Enterprise security integration

### Key References
1. **MCP Master Reference**: `MCP_MASTER_REFERENCE.md` - Complete development guidance
2. **Template**: `templates/mcp-server-template/` - Clean, canonical patterns
3. **Working Server**: `mcp-servers/auth-mcp-server/` - Proven implementation
4. **Validation**: `tests/test-auth-mcp-with-session.js` - MCP SDK client patterns

## 🏗️ Project Architecture

### Submodule Organization
- Each MCP server in `mcp-servers/` is an independent submodule
- Servers are self-contained with own dependencies and tests
- Template-based development ensures consistency
- Comprehensive validation ensures quality

### Quality Standards
- MCP SDK compliance (stdio transport, proper tool registration)
- Template adherence (structure, patterns, documentation)
- Security integration (Keycloak auth, Infisical secrets)
- Comprehensive testing (unit, integration, validation)

## 🚀 Getting Started

### For New Contributors
1. Read `README.md` for project overview
2. Study `MCP_MASTER_REFERENCE.md` for MCP development guidelines
3. Examine `templates/mcp-server-template/` for patterns
4. Review `mcp-servers/auth-mcp-server/` for working examples

### For Development Tasks
1. Choose appropriate specialized chat mode
2. Reference canonical template and working implementations
3. Follow validation procedures
4. Ensure security and quality standards

### For Questions and Support
- Use this mode for general project questions
- Reference project documentation and standards
- Switch to specialized modes for specific development tasks

This mode provides project-wide context and guidance. For hands-on development work, use the specialized chat modes designed for specific MCP development workflows.
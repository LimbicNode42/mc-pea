# MC-PEA Project

## Overview

MC-PEA provides a comprehensive implementation and testing framework for MCP (Model Context Protocol) servers, with production-ready authentication and database integrations. The project includes reference implementations, development templates, and extensive validation tools.

## Project Structure

```
mc-pea/
├── 📚 Documentation
│   ├── README.md                    # This file
│   ├── MCP_MASTER_REFERENCE.md     # Master reference for all MCP development
│   ├── docs/
│   │   ├── PROJECT_STRUCTURE.md    # Detailed project structure
│   │   ├── REQUIREMENTS.md         # Project requirements
│   │   └── archive/                # Historical documentation
│   
├── 🏗️ Implementation
│   ├── mcp-servers/                # Production MCP servers
│   │   ├── auth-mcp-server/        # Authentication server (Keycloak + Infisical)
│   │   └── db-mcp-server/          # Database server (PostgreSQL)
│   │
│   └── templates/                  # Development templates
│       └── mcp-server-template/    # Canonical template for new servers
│
├── ✅ Testing & Validation
│   ├── tests/                      # All test and validation scripts
│   │   ├── test-auth-mcp-with-session.js  # Primary MCP SDK validation
│   │   ├── test-database-mcp.js    # Database server testing
│   │   ├── test-architecture-aware-mcp.js # Architecture testing
│   │   └── validate-*.js           # Various validation scripts
│   │
│   └── debug/                      # Debug and investigation scripts
│
├── 🔧 Configuration
│   ├── config/                     # MCP client configurations
│   ├── .vscode/                    # VS Code MCP Inspector config
│   ├── .env.example               # Environment template
│   └── package.json               # Project dependencies
│
└── 📝 Examples
    ├── examples/                   # Demo scripts and integrations
    └── setup-everything.sh        # Quick setup script
```

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone and configure
git clone <repository>
cd mc-pea
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start Auth MCP Server
```bash
cd mcp-servers/auth-mcp-server
npm install
npm run build
npm start
```

### 3. Validate Implementation
```bash
# From project root
cd tests
node test-auth-mcp-with-session.js
```

### 4. Create New MCP Server
```bash
# Copy template
cp -r templates/mcp-server-template my-new-server
cd my-new-server

# Configure and build
cp .env.example .env
npm install
npm run build
npm run test
```

## 🎯 Key Features

- ✅ **Production-Ready Servers**: Authentication and database MCP servers
- ✅ **Canonical Templates**: Clean, validated patterns for new development
- ✅ **Comprehensive Testing**: MCP SDK client validation and testing suite
- ✅ **Docker Deployment**: Production containerization with security
- ✅ **Authentication Integration**: Keycloak and Infisical support
- ✅ **Session Management**: Proper MCP session and state handling
- ✅ **Development Guardrails**: AI assistant instructions and protocol compliance

## 🏗️ Architecture

### MCP Protocol Implementation
- **Transport**: StreamableHTTPServerTransport for HTTP-based communication
- **Authentication**: API key validation via HTTP headers
- **Session Management**: UUID-based session tracking with isolated state
- **Registration**: Dynamic tool/resource registration using SDK methods

### Server Types
- **Stateful Servers**: Database operations with persistent connections
- **Stateless Servers**: Authentication and utility operations
- **Template Server**: Minimal example with all patterns

## 🛡️ Development Guidelines

### For AI Assistants
**CRITICAL**: Read `templates/mcp-server-template/prompts/ai-assistant-instructions.md`

Key requirements:
- Use MCP SDK transports only (never custom HTTP)
- Use `server.registerTool()` for tool registration
- Validate with MCP SDK client
- Follow canonical template patterns

### For Human Developers
1. **Start with template**: Copy `templates/mcp-server-template/`
2. **Follow patterns**: Use existing implementations as reference
3. **Validate thoroughly**: Use all test scripts
4. **Deploy with Docker**: Production-ready containerization included

## 📋 Validation Workflow

```bash
# 1. Template validation
node tests/validate-template.js

# 2. Server implementation
npm run build
npm start

# 3. MCP SDK client testing
node tests/test-auth-mcp-with-session.js

# 4. Architecture-aware testing
node tests/test-architecture-aware-mcp.js
```

## 🔗 Essential References

- **`MCP_MASTER_REFERENCE.md`** - Master index and quick reference
- **`templates/mcp-server-template/`** - Canonical implementation patterns
- **`mcp-servers/auth-mcp-server/`** - Production reference implementation
- **`tests/test-auth-mcp-with-session.js`** - Validated client patterns

## 📊 Project Status

**COMPLETED** ✅:
- Production auth and database MCP servers
- Complete template system with validation
- Comprehensive testing and validation suite
- Development guardrails and documentation
- Docker deployment configurations

**READY FOR USE** 🚀:
- Copy templates for new MCP servers
- Use validation scripts for any MCP implementation
- Deploy with provided Docker configurations
- Follow established patterns for protocol compliance

## 🚀 Vision

Transform frontend applications into full-stack applications by automatically generating production-ready backends that handle:
- Form data processing and validation
- Database operations (PostgreSQL)
- File storage management (NAS CDN)
- RESTful API endpoints
- Deployment automation

## 🎯 Key Features

- **Frontend Analysis**: Parse React, Vue, Angular, and other frontend frameworks to understand data requirements
- **Backend Generation**: Create Golang services with proper architecture and best practices
- **Database Integration**: Automatic PostgreSQL schema generation and migrations
- **File Storage**: NAS CDN integration for media and document handling
- **Git Integration**: Automatic repository creation and management
- **Continuous Updates**: Keep backends in sync as frontends evolve

## 🏗️ Architecture

```
Frontend Repository → [Analysis Engine] → Backend Specification → [Generator] → Golang Backend
                                      ↓
                              Database Schema + File Storage Config
                                      ↓
                                [Deployment] → Production Environment
```

## 📋 Current Status

🚧 **In Planning Phase** - See [REQUIREMENTS.md](./REQUIREMENTS.md) for detailed specifications

## 🤝 Contributing

This project is in the early planning stages. Contributions to requirements gathering, architecture design, and implementation are welcome!

## � Quick Start (Docker-Free)

For rapid local development without Docker hassles:

### Option 1: Node.js MCP Servers (Recommended)
```bash
# Most MCP servers are Node.js/TypeScript - no containers needed
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-github
# Run directly on your machine
```

### Option 2: Python Virtual Environments
```bash
# Many servers available as Python packages
pip install mcp-server-postgres
pip install mcp-server-keycloak  # When we build it
# Native execution, no virtualization
```

### Option 3: Windows Subsystem for Linux (WSL2)
```bash
# Lightweight Linux environment
wsl --install
# Better than Docker Desktop for development
```

### Cross-Service Communication
- **HTTP APIs**: Direct service-to-service calls
- **Shared File System**: Use Windows file sharing for data exchange
- **Local Database**: PostgreSQL/Redis running as Windows services
- **Message Queues**: Use local Redis for async communication

## 🔐 Auth MCP Server Validation

This repository includes an Auth MCP Server template that provides Keycloak and Infisical integration. To validate the deployed server:

### Prerequisites
1. Create a `.env` file with your configuration:
```bash
cp .env.example .env
# Edit .env with your actual values:
# AUTH_MCP_URL="https://your-auth-server.com/mcp"
# AUTH_MCP_API_KEY="your-api-key"
```

### Validation Options

**Option 1: Quick Node.js Validation**
```bash
node validate-auth-mcp-simple.js
```

**Option 2: Bash Script Validation**
```bash
chmod +x validate-auth-mcp.sh
./validate-auth-mcp.sh
```

**Option 3: Manual cURL Tests**
```bash
# Load environment variables
source .env

# Test health endpoint (no auth)
curl "${AUTH_MCP_URL%/mcp*}/health"

# Test unauthenticated request (should return 401)
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1}' \
  "$AUTH_MCP_URL"

# Test authenticated request (should work)
curl -X POST -H "Content-Type: application/json" \
  -H "API_KEY: $AUTH_MCP_API_KEY" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"1.0","capabilities":{}}}' \
  "$AUTH_MCP_URL"
```

### MCP Inspector Configuration

For development with MCP Inspector, use the environment-based config:
```bash
# Copy the environment-based MCP config
cp .vscode/mcp-env.json .vscode/mcp.json
# Ensure AUTH_MCP_API_KEY is in your environment
```

## 🤖 AI/Copilot Guardrails

This project includes comprehensive AI assistant guardrails through VS Code Copilot custom modes and instructions:

### 📁 Copilot Configuration (`.github/`)
```
.github/
├── copilot-instructions.md     # Repository-wide AI guidelines
├── chatmodes/                  # Custom chat modes for specific workflows
│   ├── mcp-server-development.chatmode.md  # Creating MCP servers
│   ├── mcp-server-validation.chatmode.md   # Testing and validation
│   └── mcp-troubleshooting.chatmode.md     # Debugging and fixes
├── instructions/               # Domain-specific coding standards
│   ├── instructions.instructions.md        # General project standards
│   ├── mcp-server-architecture.instructions.md  # Submodule architecture
│   └── mcp-protocol-compliance.instructions.md  # Protocol requirements
└── prompts/                    # Reusable prompt templates
    ├── create-mcp-server.prompt.md         # Server creation workflow
    ├── validate-mcp-server.prompt.md       # Validation procedures
    └── debug-mcp-server.prompt.md          # Debugging assistance
```

### 🎯 Specialized Chat Modes

- **MCP Server Development**: Comprehensive development mode with template enforcement and validation workflows
- **MCP Server Validation**: Testing and compliance checking with systematic validation procedures  
- **MCP Troubleshooting**: Systematic debugging with guided troubleshooting and proven solutions

### 🛡️ AI Development Guardrails

**Critical Context**: The Model Context Protocol (MCP) is NOT in AI training data. The guardrails ensure:

1. **Template Compliance**: Always reference `templates/mcp-server-template/` for canonical patterns
2. **Protocol Adherence**: Mandatory use of MCP SDK transports and proper tool registration
3. **Validation Requirements**: All servers must pass MCP SDK client testing
4. **Security Standards**: Integration with Keycloak and Infisical, proper input validation
5. **Submodule Architecture**: Each server in `mcp-servers/` is independent with own tests and docs

These guardrails prevent common MCP development mistakes and ensure all AI-assisted development follows proven patterns from the working reference implementations.

## �📄 License

[MIT License](LICENSE) - Feel free to use this for your own projects!

---

*"Bridging the gap between frontend dreams and backend reality"*

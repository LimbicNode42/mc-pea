# MC-PEA: MCP Backend Generator Server

> **M**odel **C**ontext **P**rotocol - **P**roduction **E**nvironment **A**utomation

An intelligent MCP server that automatically generates and maintains Golang backend services for frontend applications.

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

## �📄 License

[MIT License](LICENSE) - Feel free to use this for your own projects!

---

*"Bridging the gap between frontend dreams and backend reality"*

"""
Repository Manager - Utility class for managing repository templates and structures.

This class handles the creation of repository content, file organization,
and template management for MCP servers.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path


class RepositoryManager:
    """
    Utility class for managing MCP server repository structures and content.
    
    Handles:
    - Template file generation
    - Repository structure creation
    - File content preparation
    - Documentation generation
    """

    def __init__(self, template_path: str = None):
        """
        Initialize Repository Manager.
        
        Args:
            template_path: Path to MCP server template directory
        """
        self.template_path = template_path or self._get_default_template_path()
        self.logger = logging.getLogger(__name__)
    
    def _get_default_template_path(self) -> str:
        """Get the default template path."""
        # Assuming we're in ai-agents/agents/github_agent/
        current_dir = Path(__file__).parent
        template_path = current_dir.parent.parent.parent / "templates" / "mcp-server-template"
        return str(template_path)
    
    def prepare_repository_files(self, specification: Dict[str, Any], 
                                generated_code: Dict[str, str]) -> Dict[str, str]:
        """
        Prepare all files for repository creation.
        
        Args:
            specification: Server specification
            generated_code: Generated MCP server code files
        
        Returns:
            Dict mapping file paths to content
        """
        files = {}
        
        # Add generated MCP server code
        files.update(generated_code)
        
        # Add repository metadata files
        files.update(self._create_metadata_files(specification))
        
        # Add configuration files
        files.update(self._create_config_files(specification))
        
        # Add documentation files
        files.update(self._create_documentation_files(specification))
        
        # Add workflow files
        files.update(self._create_workflow_files(specification))
        
        return files
    
    def _create_metadata_files(self, specification: Dict[str, Any]) -> Dict[str, str]:
        """Create repository metadata files."""
        files = {}
        
        # package.json
        package_json = {
            "name": specification.get('name'),
            "version": "1.0.0",
            "description": specification.get('description'),
            "main": "dist/index.js",
            "type": "module",
            "scripts": {
                "build": "tsc",
                "dev": "tsx src/index.ts",
                "start": "node dist/index.js",
                "test": "npm run test:unit && npm run test:integration",
                "test:unit": "jest tests/unit",
                "test:integration": "jest tests/integration",
                "test:mcp": "node tests/mcp-client-test.js",
                "validate": "node ../../tests/validate-template.js .",
                "lint": "eslint src tests --ext .ts,.js",
                "lint:fix": "eslint src tests --ext .ts,.js --fix"
            },
            "keywords": [
                "mcp",
                "model-context-protocol",
                "mcp-server",
                "typescript",
                specification.get('name', '').replace('-mcp-server', '')
            ],
            "author": f"Generated by MC-PEA AI Agent System",
            "license": "MIT",
            "dependencies": {
                "@modelcontextprotocol/sdk": "^1.0.0"
            },
            "devDependencies": {
                "@types/jest": "^29.5.0",
                "@types/node": "^20.0.0",
                "@typescript-eslint/eslint-plugin": "^6.0.0",
                "@typescript-eslint/parser": "^6.0.0",
                "eslint": "^8.0.0",
                "jest": "^29.5.0",
                "tsx": "^4.0.0",
                "typescript": "^5.0.0"
            },
            "engines": {
                "node": ">=18.0.0"
            }
        }
        
        files["package.json"] = json.dumps(package_json, indent=2)
        
        # tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2022",
                "module": "ESNext",
                "moduleResolution": "node",
                "lib": ["ES2022"],
                "outDir": "./dist",
                "rootDir": "./src",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True,
                "declaration": True,
                "declarationMap": True,
                "sourceMap": True
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules", "dist", "tests"]
        }
        
        files["tsconfig.json"] = json.dumps(tsconfig, indent=2)
        
        # .gitignore
        gitignore_content = """# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build outputs
dist/
build/
*.tsbuildinfo

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# Jest
.jest/

# Temporary files
.tmp/
temp/
"""
        
        files[".gitignore"] = gitignore_content
        
        return files
    
    def _create_config_files(self, specification: Dict[str, Any]) -> Dict[str, str]:
        """Create configuration files."""
        files = {}
        
        # .env.example
        env_example = f"""# {specification.get('name', 'MCP Server').title()} Configuration

# API Configuration
API_BASE_URL={specification.get('api_url', 'https://api.example.com')}
API_KEY=your-api-key-here

# Server Configuration
PORT=3000
LOG_LEVEL=info

# Authentication
AUTH_TYPE={specification.get('auth_type', 'api_key')}

# Optional: API Documentation URL
API_DOCS_URL={specification.get('api_docs_url', 'https://docs.api.example.com')}
"""
        
        files[".env.example"] = env_example
        
        # Docker configuration
        dockerfile_content = f"""FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY dist/ ./dist/

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S mcp -u 1001

# Change ownership
RUN chown -R mcp:nodejs /app
USER mcp

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD node dist/healthcheck.js

# Start server
CMD ["node", "dist/index.js"]
"""
        
        files["Dockerfile"] = dockerfile_content
        
        # Docker compose for development
        docker_compose = f"""version: '3.8'

services:
  {specification.get('name', 'mcp-server')}:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - API_BASE_URL=${{API_BASE_URL}}
      - API_KEY=${{API_KEY}}
    volumes:
      - ./src:/app/src
      - ./dist:/app/dist
    restart: unless-stopped
"""
        
        files["docker-compose.yml"] = docker_compose
        
        return files
    
    def _create_documentation_files(self, specification: Dict[str, Any]) -> Dict[str, str]:
        """Create documentation files."""
        files = {}
        
        # Main README.md
        readme_content = f"""# {specification.get('name', 'MCP Server').title()}

{specification.get('description', 'A Model Context Protocol server')}

## Overview

This MCP server provides integration with {specification.get('api_url', 'external API')} through a standardized Model Context Protocol interface.

## Features

- **Language**: {specification.get('language', 'TypeScript')}
- **Authentication**: {specification.get('auth_type', 'API Key').replace('_', ' ').title()}
- **API Base**: {specification.get('api_url', 'https://api.example.com')}
- **Documentation**: {specification.get('api_docs_url', 'See API documentation')}

## Quick Start

### Prerequisites

- Node.js 18 or higher
- npm or yarn
- {specification.get('auth_type', 'API Key').replace('_', ' ').title()} for the target API

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/{specification.get('github_org', 'your-org')}/{specification.get('name', 'mcp-server')}.git
   cd {specification.get('name', 'mcp-server')}
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Build the server:
   ```bash
   npm run build
   ```

5. Start the server:
   ```bash
   npm start
   ```

### Development

```bash
npm run dev
```

### Testing

```bash
npm test
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `API_BASE_URL` | Base URL for the target API | Yes |
| `API_KEY` | API key for authentication | Yes |
| `PORT` | Server port (default: 3000) | No |
| `LOG_LEVEL` | Logging level (default: info) | No |

### MCP Client Configuration

Add this server to your MCP client configuration:

```json
{{
  "servers": {{
    "{specification.get('name', 'mcp-server')}": {{
      "command": "node",
      "args": ["dist/index.js"],
      "env": {{
        "API_BASE_URL": "${{API_BASE_URL}}",
        "API_KEY": "${{API_KEY}}"
      }}
    }}
  }}
}}
```

## Tools

This server provides the following tools:

{self._generate_tools_documentation(specification)}

## Resources

This server exposes the following resources:

{self._generate_resources_documentation(specification)}

## Docker

### Build and run with Docker:

```bash
docker build -t {specification.get('name', 'mcp-server')} .
docker run -p 3000:3000 --env-file .env {specification.get('name', 'mcp-server')}
```

### Using Docker Compose:

```bash
docker-compose up
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Create a pull request

## License

MIT License - see LICENSE file for details.

## Generated by MC-PEA

This MCP server was generated by the MC-PEA AI Agent System 🤖
"""
        
        files["README.md"] = readme_content
        
        # API documentation
        api_doc = f"""# API Documentation

## {specification.get('name', 'MCP Server').title()} API Reference

### Tools

{self._generate_detailed_tools_docs(specification)}

### Resources

{self._generate_detailed_resources_docs(specification)}

### Error Handling

All tools return standardized error responses:

```json
{{
  "error": {{
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {{}}
  }}
}}
```

### Authentication

This server uses {specification.get('auth_type', 'API Key').replace('_', ' ').title()} authentication.

Set the `API_KEY` environment variable with your authentication token.
"""
        
        files["docs/API.md"] = api_doc
        
        # Security documentation
        security_doc = """# Security Considerations

## Authentication

- Always use environment variables for API keys
- Never commit credentials to version control
- Rotate API keys regularly
- Use read-only tokens when possible

## Input Validation

- All tool parameters are validated against JSON schemas
- Input sanitization prevents injection attacks
- Rate limiting protects against abuse

## Network Security

- Use HTTPS for all API communications
- Validate SSL certificates
- Implement proper timeout handling

## Monitoring

- Log all authentication attempts
- Monitor for unusual usage patterns
- Implement alerting for security events
"""
        
        files["docs/SECURITY.md"] = security_doc
        
        return files
    
    def _create_workflow_files(self, specification: Dict[str, Any]) -> Dict[str, str]:
        """Create GitHub Actions workflow files."""
        files = {}
        
        # CI/CD workflow
        ci_workflow = f"""name: CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [18.x, 20.x]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Use Node.js ${{{{ matrix.node-version }}}}
      uses: actions/setup-node@v4
      with:
        node-version: ${{{{ matrix.node-version }}}}
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Lint
      run: npm run lint
    
    - name: Build
      run: npm run build
    
    - name: Test
      run: npm test
      env:
        API_KEY: ${{{{ secrets.TEST_API_KEY }}}}
        API_BASE_URL: ${{{{ secrets.TEST_API_BASE_URL }}}}
    
    - name: MCP Validation
      run: npm run validate

  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Run security audit
      run: npm audit
    
    - name: Check for vulnerabilities
      run: npm audit --audit-level moderate

  docker:
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to GitHub Container Registry
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{{{ github.actor }}}}
        password: ${{{{ secrets.GITHUB_TOKEN }}}}
    
    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        push: true
        tags: |
          ghcr.io/{specification.get('github_org', 'your-org')}/{specification.get('name', 'mcp-server')}:latest
          ghcr.io/{specification.get('github_org', 'your-org')}/{specification.get('name', 'mcp-server')}:${{{{ github.sha }}}}
"""
        
        files[".github/workflows/ci.yml"] = ci_workflow
        
        return files
    
    def _generate_tools_documentation(self, specification: Dict[str, Any]) -> str:
        """Generate tools documentation section."""
        tools = specification.get('tools', [])
        if not tools:
            return "- No tools defined yet"
        
        docs = []
        for tool in tools:
            docs.append(f"- `{tool}`: {tool.replace('_', ' ').title()} operation")
        
        return '\n'.join(docs)
    
    def _generate_resources_documentation(self, specification: Dict[str, Any]) -> str:
        """Generate resources documentation section."""
        resources = specification.get('resources', [])
        if not resources:
            return "- No resources defined yet"
        
        docs = []
        for resource in resources:
            docs.append(f"- `{resource}`: {resource.replace('_', ' ').title()} data")
        
        return '\n'.join(docs)
    
    def _generate_detailed_tools_docs(self, specification: Dict[str, Any]) -> str:
        """Generate detailed tools documentation."""
        tools = specification.get('tools', [])
        if not tools:
            return "No tools defined."
        
        docs = []
        for tool in tools:
            docs.append(f"""
#### {tool}

**Description**: {tool.replace('_', ' ').title()} operation

**Parameters**:
- TBD (will be generated based on API analysis)

**Returns**:
- TBD (will be generated based on API analysis)

**Example**:
```json
// TBD
```
""")
        
        return '\n'.join(docs)
    
    def _generate_detailed_resources_docs(self, specification: Dict[str, Any]) -> str:
        """Generate detailed resources documentation."""
        resources = specification.get('resources', [])
        if not resources:
            return "No resources defined."
        
        docs = []
        for resource in resources:
            docs.append(f"""
#### {resource}

**Description**: {resource.replace('_', ' ').title()} data access

**URI**: `mcp://{specification.get('name', 'server')}/{resource}`

**Schema**:
- TBD (will be generated based on API analysis)

**Example**:
```json
// TBD
```
""")
        
        return '\n'.join(docs)

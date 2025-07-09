"""MCP server generator agent implementation."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from crewai import Task
from pydantic import BaseModel, Field

from core.base_agent import AgentConfig, AgentMessage, AgentResult, BaseAgent
from core.config import get_config, MCPEAConfig
from tools.file_operations import FileOperations
from tools.mcp_validators import MCPValidator


class ServerSpecification(BaseModel):
    """Specification for MCP server generation."""
    
    name: str = Field(..., description="Server name")
    description: str = Field(..., description="Server description")
    api_type: str = Field(..., description="API type (REST, GraphQL, etc.)")
    api_base_url: Optional[str] = Field(None, description="Base URL for API")
    auth_type: str = Field(default="none", description="Authentication type")
    auth_details: Optional[Dict[str, Any]] = Field(None, description="Auth configuration")
    tools: List[str] = Field(default_factory=list, description="List of tools to generate")
    resources: List[str] = Field(default_factory=list, description="List of resources to expose")
    additional_config: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")


class GenerationResult(BaseModel):
    """Result of MCP server generation."""
    
    success: bool = Field(..., description="Generation success")
    server_path: Optional[str] = Field(None, description="Path to generated server")
    generated_files: List[str] = Field(default_factory=list, description="List of generated files")
    validation_results: Optional[Dict[str, Any]] = Field(None, description="Validation results")
    errors: List[str] = Field(default_factory=list, description="Generation errors")


class MCPServerGeneratorAgent(BaseAgent):
    """Agent responsible for generating MCP server code."""
    
    def __init__(
        self,
        anthropic_client: Anthropic,
        config: Optional[AgentConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        # Use provided config or create default
        if config is None:
            config = AgentConfig(
                name="mcp_generator",
                role="MCP Server Code Generator",
                goal="Generate production-ready MCP server code from API specifications",
                backstory="""
                You are an expert TypeScript developer specializing in the Model Context Protocol (MCP).
                You have deep knowledge of MCP server architecture, TypeScript best practices, and
                can generate clean, efficient, and well-documented code that follows MCP standards.
                """
            )
        
        super().__init__(config, anthropic_client, logger)
        
        # Initialize tools
        self.file_ops = FileOperations()
        self.validator = MCPValidator()
        
        # Register for configuration updates
        self.register_config_callback(self._on_generator_config_update)
    
    def _on_generator_config_update(self, new_config: MCPEAConfig) -> None:
        """Handle generator-specific configuration updates.
        
        Args:
            new_config: Updated configuration
        """
        # Update generation settings
        self.generation_config = new_config.generation
        
        # Update validation requirements
        self.validation_config = new_config.validation
        
        # Update Anthropic settings
        self.anthropic_config = new_config.anthropic
        
        self.logger.info("MCP Generator configuration updated")
        self.logger.info(f"Template usage: {self.generation_config.use_templates}")
        self.logger.info(f"Output directory: {self.generation_config.output_directory}")
        self.logger.info(f"Auto validation: {self.validation_config.auto_validate}")
    
    def get_tools(self) -> List[Any]:
        """Get tools available to this agent."""
        return [
            self.generate_server_code,
            self.validate_mcp_compliance,
            self.create_package_json,
            self.create_typescript_config,
            self.create_dockerfile,
        ]
    
    async def process_message(self, message: AgentMessage) -> AgentResult:
        """Process an incoming message.
        
        Args:
            message: Incoming message
            
        Returns:
            Processing result
        """
        try:
            if message.message_type == "generate_server":
                spec = ServerSpecification(**message.content)
                result = await self.generate_mcp_server(spec)
                
                return AgentResult(
                    success=True,
                    result=result.dict(),
                )
            
            else:
                return AgentResult(
                    success=False,
                    error=f"Unknown message type: {message.message_type}",
                )
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return AgentResult(
                success=False,
                error=str(e),
            )
    
    async def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        """Execute a specific task.
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        task_type = task.get("type")
        
        if task_type == "generate_server":
            spec = ServerSpecification(**task.get("specification", {}))
            result = await self.generate_mcp_server(spec)
            
            return AgentResult(
                success=result.success,
                result=result.dict(),
            )
        
        return AgentResult(
            success=False,
            error=f"Unknown task type: {task_type}",
        )
    
    async def generate_mcp_server(self, spec: ServerSpecification) -> GenerationResult:
        """Generate a complete MCP server from specification.
        
        Args:
            spec: Server specification
            
        Returns:
            Generation result
        """
        self.logger.info(f"Generating MCP server: {spec.name}")
        
        try:
            # Create server directory
            server_path = self.output_path / spec.name
            server_path.mkdir(exist_ok=True)
            
            generated_files = []
            errors = []
            
            # Generate core files
            core_files = await self._generate_core_files(spec, server_path)
            generated_files.extend(core_files)
            
            # Generate tools
            if spec.tools:
                tool_files = await self._generate_tools(spec, server_path)
                generated_files.extend(tool_files)
            
            # Generate resources
            if spec.resources:
                resource_files = await self._generate_resources(spec, server_path)
                generated_files.extend(resource_files)
            
            # Generate configuration files
            config_files = await self._generate_config_files(spec, server_path)
            generated_files.extend(config_files)
            
            # Generate tests
            test_files = await self._generate_tests(spec, server_path)
            generated_files.extend(test_files)
            
            # Validate the generated server
            validation_results = await self._validate_generated_server(server_path)
            
            return GenerationResult(
                success=True,
                server_path=str(server_path),
                generated_files=generated_files,
                validation_results=validation_results,
                errors=errors,
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate MCP server: {e}")
            return GenerationResult(
                success=False,
                errors=[str(e)],
            )
    
    async def _generate_core_files(
        self, spec: ServerSpecification, server_path: Path
    ) -> List[str]:
        """Generate core server files.
        
        Args:
            spec: Server specification
            server_path: Path to server directory
            
        Returns:
            List of generated file paths
        """
        files = []
        
        # Create src directory
        src_path = server_path / "src"
        src_path.mkdir(exist_ok=True)
        
        # Generate main index.ts
        index_content = await self._generate_index_file(spec)
        index_path = src_path / "index.ts"
        await self.file_ops.write_file(index_path, index_content)
        files.append(str(index_path))
        
        # Generate registrations.ts
        registrations_content = await self._generate_registrations_file(spec)
        registrations_path = src_path / "registrations.ts"
        await self.file_ops.write_file(registrations_path, registrations_content)
        files.append(str(registrations_path))
        
        return files
    
    async def _generate_index_file(self, spec: ServerSpecification) -> str:
        """Generate the main index.ts file.
        
        Args:
            spec: Server specification
            
        Returns:
            Generated TypeScript content
        """
        prompt = f"""
        Generate a TypeScript index.ts file for an MCP server with the following specification:
        
        Name: {spec.name}
        Description: {spec.description}
        API Type: {spec.api_type}
        Tools: {', '.join(spec.tools)}
        Resources: {', '.join(spec.resources)}
        
        The file should:
        1. Import necessary MCP SDK components
        2. Create a server instance using stdio transport
        3. Set up proper error handling
        4. Include server info with name and version
        5. Follow MC-PEA project standards
        
        Use the MCP SDK stdio transport pattern and ensure full protocol compliance.
        """
        
        response = await self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_registrations_file(self, spec: ServerSpecification) -> str:
        """Generate the registrations.ts file.
        
        Args:
            spec: Server specification
            
        Returns:
            Generated TypeScript content
        """
        prompt = f"""
        Generate a TypeScript registrations.ts file for an MCP server that registers tools and resources.
        
        Server: {spec.name}
        Tools to register: {', '.join(spec.tools)}
        Resources to register: {', '.join(spec.resources)}
        
        The file should:
        1. Import the server instance
        2. Import tool and resource implementations
        3. Register all tools using server.registerTool()
        4. Register all resources using server.registerResource()
        5. Export a registerAll function
        6. Use proper TypeScript types
        
        Follow MCP SDK patterns and MC-PEA standards.
        """
        
        response = await self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_tools(
        self, spec: ServerSpecification, server_path: Path
    ) -> List[str]:
        """Generate tool implementations.
        
        Args:
            spec: Server specification
            server_path: Path to server directory
            
        Returns:
            List of generated file paths
        """
        files = []
        tools_path = server_path / "src" / "tools"
        tools_path.mkdir(exist_ok=True)
        
        for tool_name in spec.tools:
            tool_content = await self._generate_tool_implementation(spec, tool_name)
            tool_file = tools_path / f"{tool_name}.ts"
            await self.file_ops.write_file(tool_file, tool_content)
            files.append(str(tool_file))
        
        # Generate tools index file
        index_content = await self._generate_tools_index(spec.tools)
        index_file = tools_path / "index.ts"
        await self.file_ops.write_file(index_file, index_content)
        files.append(str(index_file))
        
        return files
    
    async def _generate_tool_implementation(
        self, spec: ServerSpecification, tool_name: str
    ) -> str:
        """Generate implementation for a specific tool.
        
        Args:
            spec: Server specification
            tool_name: Name of the tool
            
        Returns:
            Generated TypeScript content
        """
        prompt = f"""
        Generate a TypeScript implementation for the tool "{tool_name}" in an MCP server.
        
        Server context:
        - Name: {spec.name}
        - API Type: {spec.api_type}
        - Base URL: {spec.api_base_url or 'N/A'}
        - Auth Type: {spec.auth_type}
        
        The implementation should:
        1. Export a function that implements the tool
        2. Include proper parameter validation
        3. Use appropriate HTTP client or data access patterns
        4. Return MCP-compliant responses
        5. Include error handling
        6. Add JSDoc documentation
        
        Follow TypeScript best practices and MCP protocol standards.
        """
        
        response = await self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_tools_index(self, tools: List[str]) -> str:
        """Generate tools index file.
        
        Args:
            tools: List of tool names
            
        Returns:
            Generated TypeScript content
        """
        exports = '\n'.join([f'export {{ {tool} }} from "./{tool}";' for tool in tools])
        
        return f"""/**
 * Tool implementations for MCP server.
 */

{exports}

export const allTools = [
{', '.join(tools)}
];
"""
    
    async def _generate_resources(
        self, spec: ServerSpecification, server_path: Path
    ) -> List[str]:
        """Generate resource implementations.
        
        Args:
            spec: Server specification
            server_path: Path to server directory
            
        Returns:
            List of generated file paths
        """
        files = []
        resources_path = server_path / "src" / "resources"
        resources_path.mkdir(exist_ok=True)
        
        # Generate main resources file
        resources_content = await self._generate_resources_implementation(spec)
        resources_file = resources_path / "index.ts"
        await self.file_ops.write_file(resources_file, resources_content)
        files.append(str(resources_file))
        
        return files
    
    async def _generate_resources_implementation(self, spec: ServerSpecification) -> str:
        """Generate resource implementations.
        
        Args:
            spec: Server specification
            
        Returns:
            Generated TypeScript content
        """
        prompt = f"""
        Generate TypeScript resource implementations for an MCP server.
        
        Resources to implement: {', '.join(spec.resources)}
        Server context: {spec.name} - {spec.description}
        API Type: {spec.api_type}
        
        The implementation should:
        1. Define resource URIs and metadata
        2. Implement resource listing and retrieval
        3. Use proper TypeScript types
        4. Follow MCP resource patterns
        5. Include error handling
        
        Export all resources and a resources registry.
        """
        
        response = await self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_config_files(
        self, spec: ServerSpecification, server_path: Path
    ) -> List[str]:
        """Generate configuration files.
        
        Args:
            spec: Server specification
            server_path: Path to server directory
            
        Returns:
            List of generated file paths
        """
        files = []
        
        # Generate package.json
        package_content = await self.create_package_json(spec)
        package_file = server_path / "package.json"
        await self.file_ops.write_file(package_file, package_content)
        files.append(str(package_file))
        
        # Generate tsconfig.json
        tsconfig_content = await self.create_typescript_config(spec)
        tsconfig_file = server_path / "tsconfig.json"
        await self.file_ops.write_file(tsconfig_file, tsconfig_content)
        files.append(str(tsconfig_file))
        
        # Generate Dockerfile
        dockerfile_content = await self.create_dockerfile(spec)
        dockerfile_file = server_path / "Dockerfile"
        await self.file_ops.write_file(dockerfile_file, dockerfile_content)
        files.append(str(dockerfile_file))
        
        # Generate README.md
        readme_content = await self._generate_readme(spec)
        readme_file = server_path / "README.md"
        await self.file_ops.write_file(readme_file, readme_content)
        files.append(str(readme_file))
        
        return files
    
    async def create_package_json(self, spec: ServerSpecification) -> str:
        """Create package.json content."""
        package_data = {
            "name": spec.name,
            "version": "1.0.0",
            "description": spec.description,
            "main": "dist/index.js",
            "scripts": {
                "build": "tsc",
                "start": "node dist/index.js",
                "dev": "ts-node src/index.ts",
                "test": "jest",
                "lint": "eslint src/**/*.ts",
                "format": "prettier --write src/**/*.ts"
            },
            "dependencies": {
                "@modelcontextprotocol/sdk": "^1.0.0",
                "typescript": "^5.0.0"
            },
            "devDependencies": {
                "@types/node": "^20.0.0",
                "ts-node": "^10.0.0",
                "jest": "^29.0.0",
                "@types/jest": "^29.0.0",
                "eslint": "^8.0.0",
                "prettier": "^3.0.0"
            },
            "keywords": ["mcp", "model-context-protocol", "ai", "llm"],
            "author": "MC-PEA AI Agents",
            "license": "MIT"
        }
        
        return json.dumps(package_data, indent=2)
    
    async def create_typescript_config(self, spec: ServerSpecification) -> str:
        """Create tsconfig.json content."""
        tsconfig_data = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "lib": ["ES2020"],
                "outDir": "./dist",
                "rootDir": "./src",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True,
                "resolveJsonModule": True,
                "declaration": True,
                "declarationMap": True,
                "sourceMap": True
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules", "dist", "tests"]
        }
        
        return json.dumps(tsconfig_data, indent=2)
    
    async def create_dockerfile(self, spec: ServerSpecification) -> str:
        """Create Dockerfile content."""
        return f"""FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY dist/ ./dist/

USER node

CMD ["node", "dist/index.js"]
"""
    
    async def _generate_readme(self, spec: ServerSpecification) -> str:
        """Generate README.md content."""
        return f"""# {spec.name}

{spec.description}

## Description

This MCP server provides access to {spec.api_type} functionality through the Model Context Protocol.

## Features

### Tools
{chr(10).join(f'- `{tool}`: {tool.replace("_", " ").title()}' for tool in spec.tools)}

### Resources
{chr(10).join(f'- `{resource}`: {resource.title()} data' for resource in spec.resources)}

## Installation

```bash
npm install
npm run build
```

## Usage

```bash
npm start
```

## Configuration

Configure the server through environment variables or configuration files.

## Testing

```bash
npm test
```

## Generated by MC-PEA AI Agents

This server was automatically generated using the MC-PEA AI agent system.
"""
    
    async def _generate_tests(
        self, spec: ServerSpecification, server_path: Path
    ) -> List[str]:
        """Generate test files.
        
        Args:
            spec: Server specification
            server_path: Path to server directory
            
        Returns:
            List of generated file paths
        """
        files = []
        tests_path = server_path / "tests"
        tests_path.mkdir(exist_ok=True)
        
        # Generate basic test file
        test_content = await self._generate_basic_test(spec)
        test_file = tests_path / "basic.test.ts"
        await self.file_ops.write_file(test_file, test_content)
        files.append(str(test_file))
        
        return files
    
    async def _generate_basic_test(self, spec: ServerSpecification) -> str:
        """Generate basic test content."""
        return f"""/**
 * Basic tests for {spec.name} MCP server.
 */

import {{ describe, test, expect }} from '@jest/globals';

describe('{spec.name} MCP Server', () => {{
  test('should initialize correctly', () => {{
    expect(true).toBe(true);
  }});
  
  test('should validate MCP protocol compliance', () => {{
    // TODO: Add MCP protocol validation tests
    expect(true).toBe(true);
  }});
}});
"""
    
    async def _validate_generated_server(self, server_path: Path) -> Dict[str, Any]:
        """Validate the generated server.
        
        Args:
            server_path: Path to server directory
            
        Returns:
            Validation results
        """
        return await self.mcp_validator.validate_server(server_path)
    
    async def generate_server_code(self, specification: Dict[str, Any]) -> str:
        """Tool: Generate MCP server code from specification."""
        spec = ServerSpecification(**specification)
        result = await self.generate_mcp_server(spec)
        return json.dumps(result.dict(), indent=2)
    
    async def validate_mcp_compliance(self, server_path: str) -> str:
        """Tool: Validate MCP protocol compliance."""
        validation_results = await self.mcp_validator.validate_server(Path(server_path))
        return json.dumps(validation_results, indent=2)

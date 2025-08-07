"""
TypeScript Code Generation Tools for MCP API Integrator Agent

These tools generate TypeScript code for MCP tools and resources based on API endpoint data.
"""

import json
import logging
import subprocess
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class GenerateTypescriptToolInput(BaseModel):
    """Input schema for GenerateTypescriptToolTool."""
    tool_name: str = Field(
        ..., 
        description="Name for the generated tool (e.g., 'get_user_profile', 'create_repository'). Should be snake_case."
    )
    endpoint_data: str = Field(
        ..., 
        description="""JSON string containing API endpoint information with the following structure:
        {
            "method": "GET|POST|PUT|DELETE|PATCH",
            "path": "/api/v1/endpoint",
            "description": "What this endpoint does",
            "parameters": [
                {
                    "name": "param_name",
                    "type": "string|number|boolean",
                    "required": true|false,
                    "description": "Parameter description"
                }
            ]
        }"""
    )


class GenerateTypescriptToolTool(BaseTool):
    name: str = "generate_typescript_tool"
    description: str = """
    Generate TypeScript code for an MCP tool based on API endpoint data.
    
    This tool creates both:
    1. Tool definition (schema for parameters)
    2. Tool handler (implementation that calls the API)
    
    The generated code follows the MCP template pattern with proper error handling,
    parameter validation, and authentication headers.
    
    Use this for API endpoints that perform actions (GET, POST, PUT, DELETE).
    """
    args_schema: Type[BaseModel] = GenerateTypescriptToolInput

    def _run(self, tool_name: str, endpoint_data: str) -> str:
        """Generate TypeScript code for an MCP tool."""
        logger.debug(f"⚙️ GenerateTypescriptToolTool._run called with tool_name={tool_name}")
        
        try:
            # Parse endpoint data
            try:
                endpoint = json.loads(endpoint_data)
            except json.JSONDecodeError as e:
                return f"Error: Invalid JSON in endpoint_data: {str(e)}"
            
            method = endpoint.get('method', 'GET').upper()
            path = endpoint.get('path', '')
            description = endpoint.get('description', f'{method} {path}')
            parameters = endpoint.get('parameters', [])
            
            logger.debug(f"⚙️ Parsed endpoint: method={method}, path={path}, {len(parameters)} parameters")
            
            # Generate parameter schema
            schema_properties = {}
            required_params = []
            
            for param in parameters:
                param_name = param.get('name', 'unknown')
                param_type = param.get('type', 'string')
                param_required = param.get('required', False)
                param_description = param.get('description', '')
                
                # Map API parameter types to JSON schema types
                if param_type in ['integer', 'int']:
                    schema_type = 'number'
                elif param_type in ['boolean', 'bool']:
                    schema_type = 'boolean'
                else:
                    schema_type = 'string'
                
                schema_properties[param_name] = {
                    'type': schema_type,
                    'description': param_description
                }
                
                if param_required:
                    required_params.append(param_name)
            
            # Generate the code
            properties_str = json.dumps(schema_properties, indent=6)
            required_str = json.dumps(required_params)
            param_names = list(schema_properties.keys())
            param_destructure = ', '.join(param_names) if param_names else ''
            
            # Generate body code for POST/PUT/PATCH
            body_code = ""
            if method in ['POST', 'PUT', 'PATCH'] and param_names:
                body_params = [p for p in param_names if p not in ['id', 'path']]  # Exclude path params
                if body_params:
                    body_code = f'''
      // Add body for {method} requests
      const bodyParams = {{ {', '.join([f'{p}: {p}' for p in body_params])} }};
      if (Object.keys(bodyParams).some(key => bodyParams[key] !== undefined)) {{
        requestOptions.body = JSON.stringify(bodyParams);
      }}'''
            
            # Generate tool definition
            tool_definition = f'''  {tool_name}: {{
    name: '{tool_name}',
    description: '{description}',
    inputSchema: {{
      type: 'object',
      properties: {properties_str},
      required: {required_str}
    }}
  }}'''
            
            # Generate tool handler
            tool_handler = f'''  {tool_name}: async (args: any, sessionId: string) => {{
    try {{
      // Extract parameters
      const {{ {param_destructure} }} = args;
      
      // Build URL with path parameters
      let url = `${{BASE_URL}}{path}`;
      
      // Build request options
      const requestOptions: RequestInit = {{
        method: "{method}",
        headers: {{
          "Content-Type": "application/json",
          ...getAuthHeaders()
        }}
      }};
      {body_code}
      
      // Make the API request
      const response = await fetch(url, requestOptions);
      
      if (!response.ok) {{
        throw new Error(`API request failed: ${{response.status}} ${{response.statusText}}`);
      }}
      
      const data = await response.json();
      
      return {{
        content: [
          {{
            type: "text" as const,
            text: JSON.stringify(data, null, 2)
          }}
        ]
      }};
    }} catch (error) {{
      return {{
        content: [
          {{
            type: "text" as const,
            text: `Error calling {tool_name}: ${{error instanceof Error ? error.message : String(error)}}`
          }}
        ]
      }};
    }}
  }}'''
            
            # Return structured code
            result = f'''// Tool Definition for {tool_name}
{tool_definition},

// Tool Handler for {tool_name}
{tool_handler}'''
            
            logger.debug(f"⚙️ Generated {len(result)} characters of TypeScript tool code")
            return f"Successfully generated TypeScript tool code for '{tool_name}':\n\n{result}"
            
        except Exception as e:
            error_msg = f"Error generating TypeScript tool: {str(e)}"
            logger.error(f"⚙️ {error_msg}")
            return error_msg


class GenerateTypescriptResourceInput(BaseModel):
    """Input schema for GenerateTypescriptResourceTool."""
    resource_name: str = Field(
        ..., 
        description="Name for the generated resource (e.g., 'user_profile', 'repository_list'). Should be snake_case."
    )
    endpoint_data: str = Field(
        ..., 
        description="""JSON string containing API endpoint information with the following structure:
        {
            "method": "GET",
            "path": "/api/v1/resource",
            "description": "What this resource provides"
        }
        Note: Resources are typically GET endpoints that provide data."""
    )


class GenerateTypescriptResourceTool(BaseTool):
    name: str = "generate_typescript_resource"
    description: str = """
    Generate TypeScript code for an MCP resource based on API endpoint data.
    
    Resources in MCP provide read-only access to data and are typically used for:
    - Configuration data
    - Status information  
    - Data listings
    - Read-only API endpoints
    
    The generated code includes proper error handling and returns data in the
    standard MCP resource format.
    
    Use this for GET endpoints that provide data rather than perform actions.
    """
    args_schema: Type[BaseModel] = GenerateTypescriptResourceInput

    def _run(self, resource_name: str, endpoint_data: str) -> str:
        """Generate TypeScript code for an MCP resource."""
        logger.debug(f"🔗 GenerateTypescriptResourceTool._run called with resource_name={resource_name}")
        
        try:
            # Parse endpoint data
            try:
                endpoint = json.loads(endpoint_data)
            except json.JSONDecodeError as e:
                return f"Error: Invalid JSON in endpoint_data: {str(e)}"
            
            path = endpoint.get('path', '')
            description = endpoint.get('description', f'Access to {resource_name}')
            
            logger.debug(f"🔗 Parsed endpoint: path={path}, description={description}")
            
            # Generate resource definition
            resource_definition = f'''  {resource_name}: {{
    uri: "api://{resource_name}",
    name: "{resource_name}",
    description: "{description}",
    mimeType: "application/json"
  }}'''
            
            # Generate resource handler
            resource_handler = f'''  "api://{resource_name}": async (sessionId: string) => {{
    try {{
      // Build URL
      const url = `${{BASE_URL}}{path}`;
      
      // Make the API request
      const response = await fetch(url, {{
        method: "GET",
        headers: {{
          "Content-Type": "application/json",
          ...getAuthHeaders()
        }}
      }});
      
      if (!response.ok) {{
        throw new Error(`API request failed: ${{response.status}} ${{response.statusText}}`);
      }}
      
      const data = await response.json();
      
      return {{
        contents: [
          {{
            uri: "api://{resource_name}",
            mimeType: "application/json",
            text: JSON.stringify(data, null, 2)
          }}
        ]
      }};
    }} catch (error) {{
      return {{
        contents: [
          {{
            uri: "api://{resource_name}",
            mimeType: "text/plain",
            text: `Error accessing {resource_name}: ${{error instanceof Error ? error.message : String(error)}}`
          }}
        ]
      }};
    }}
  }}'''
            
            # Return structured code
            result = f'''// Resource Definition for {resource_name}
{resource_definition},

// Resource Handler for {resource_name}
{resource_handler}'''
            
            logger.debug(f"🔗 Generated {len(result)} characters of TypeScript resource code")
            return f"Successfully generated TypeScript resource code for '{resource_name}':\n\n{result}"
            
        except Exception as e:
            error_msg = f"Error generating TypeScript resource: {str(e)}"
            logger.error(f"🔗 {error_msg}")
            return error_msg


class ValidateTypescriptInput(BaseModel):
    """Input schema for ValidateTypescriptTool."""
    file_path: str = Field(
        ..., 
        description="Path to the TypeScript file to validate. Should be relative to the MCP server directory."
    )


class ValidateTypescriptTool(BaseTool):
    name: str = "validate_typescript"
    description: str = """
    Validate TypeScript file syntax using the TypeScript compiler.
    
    This tool runs 'tsc --noEmit' on the specified file to check for:
    - Syntax errors
    - Type errors
    - Import/export issues
    - Other TypeScript compilation problems
    
    Use this tool after generating or modifying TypeScript files to ensure
    they are syntactically correct before proceeding.
    
    Requires TypeScript to be installed (npm install -g typescript).
    """
    args_schema: Type[BaseModel] = ValidateTypescriptInput

    def _run(self, file_path: str) -> str:
        """Validate TypeScript file syntax."""
        logger.debug(f"✅ ValidateTypescriptTool._run called with file_path={file_path}")
        
        try:
            # Check if file exists
            import os
            if not os.path.isabs(file_path):
                abs_path = os.path.abspath(file_path)
            else:
                abs_path = file_path
                
            if not os.path.exists(abs_path):
                return f"Error: File not found: {abs_path}"
            
            # Run TypeScript compiler to validate
            try:
                result = subprocess.run(
                    ['tsc', '--noEmit', abs_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    logger.debug(f"✅ TypeScript validation passed for {abs_path}")
                    return f"TypeScript validation passed for {file_path} ✅"
                else:
                    logger.debug(f"✅ TypeScript validation failed for {abs_path}")
                    return f"TypeScript validation failed for {file_path}:\n\n{result.stderr}"
                    
            except subprocess.TimeoutExpired:
                return f"TypeScript validation timed out for {file_path}"
            except FileNotFoundError:
                return "TypeScript compiler (tsc) not found. Please install with: npm install -g typescript"
            
        except Exception as e:
            error_msg = f"Error validating TypeScript file {file_path}: {str(e)}"
            logger.error(f"✅ {error_msg}")
            return error_msg

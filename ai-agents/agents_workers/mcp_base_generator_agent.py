"""
MCP Base Generator Agent

Agent responsible for generating the base MCP server structure from templates.
Creates the foundational TypeScript MCP server that can later be populated with API tools and resources.
"""

from crewai import Agent, LLM
from crewai.tools import tool
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os
import shutil
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from core.agent_workers_config_loader import get_agent_config
from pydantic import Field


class MCPBaseGeneratorAgent(Agent):
    """
    Agent responsible for generating the base MCP server structure.
    Creates the foundational TypeScript MCP server that can later be populated with API tools and resources.
    """
    
    # Declare custom fields as Pydantic model fields
    website_url: str = Field(description="The website URL for API integration")
    server_name: str = Field(description="The generated server name")
    template_dir: str = Field(description="Path to the template directory")
    output_dir: str = Field(description="Output directory for the generated server")
    
    def __init__(self, website_url: str, server_name: str = None, template_path: str = None, **kwargs):
        load_dotenv()
        
        # Generate server name from website URL if not provided
        if not server_name:
            parsed = urlparse(website_url)
            domain = parsed.netloc.replace('www.', '').replace('.', '-')
            server_name = f"{domain}-api-mcp-server"
        
        # Use custom template path if provided, otherwise use default
        if template_path:
            if os.path.isabs(template_path):
                template_dir = template_path
            else:
                # Relative to current working directory
                template_dir = os.path.abspath(template_path)
        else:
            # Default template path
            template_dir = os.path.join(os.getcwd(), '..', 'templates', 'mcp-server-template')
        
        output_dir = os.path.join(os.getcwd(), '..', 'mcp-servers', server_name)
        
        # Validate template directory exists
        if not os.path.exists(template_dir):
            raise ValueError(f"Template directory not found: {template_dir}")
        
        # Load agent configuration
        config = get_agent_config('mcp_base_generator_agent')

        if "claude" in config.get("llm"):
            llm = ChatAnthropic(
                model=config.get("llm"),
                max_tokens=config.get("max_output_tokens"),
                temperature=config.get("temperature"),
                max_retries=config.get("max_retry_limit"),
            )
            print("Using Claude LLM for link discovery")
        elif "gemini" in config.get("llm"):
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini models")
            
            # Extract just the model name (remove the provider prefix)
            model_name = config.get("llm").replace("gemini/", "")
            
            # Use CrewAI's LLM class for Gemini models
            llm = LLM(
                model=f"gemini/{model_name}",
                api_key=google_api_key,
                max_tokens=config.get("max_input_tokens"),
                max_completion_tokens=config.get("max_output_tokens"),
                temperature=config.get("temperature"),
                reasoning_effort=config.get("reasoning_effort"),
            )
            print(f"Using Gemini LLM for link discovery: {model_name}")
        else:
            raise ValueError("Unsupported LLM type in configuration")
        
        super().__init__(
            role=config.get('role', 'MCP Base Generator'),
            goal=config.get('goal', f'Generate base MCP server structure for {website_url} API integration'),
            backstory=config.get('backstory', f"""You are an expert TypeScript developer specializing in Model Context Protocol (MCP) server development.
            Your job is to create a solid foundation MCP server structure that follows MC-PEA project standards.
            You work with templates to ensure consistency and best practices."""),
            llm=llm,
            tools=[],
            respect_context_window=config.get('respect_context_window', True),
            cache=config.get('cache', False),
            reasoning=config.get('reasoning', True),
            max_iter=config.get('max_iterations', 20),
            max_retry_limit=config.get('max_retry_limit', 2),
            verbose=config.get('verbose', True),
            allow_delegation=config.get('allow_delegation', False),
            # Pass our custom fields to the parent constructor
            website_url=website_url,
            server_name=server_name,
            template_dir=template_dir,
            output_dir=output_dir,
            **kwargs
        )
        
        # Create tools that have access to instance variables
        @tool("copy_template_structure")
        def copy_template_structure_tool(context: str = "{}") -> str:
            """Copy the MCP server template structure to the target directory."""
            return str(self.copy_template_structure({}))
        
        @tool("customize_package_json")  
        def customize_package_json_tool(context: str = "{}") -> str:
            """Customize the package.json with server-specific information."""
            return str(self.customize_package_json({}))
        
        @tool("customize_readme")
        def customize_readme_tool(context: str = "{}") -> str:
            """Customize the README.md with server-specific information."""
            return str(self.customize_readme({}))
        
        @tool("customize_main_server_file")
        def customize_main_server_file_tool(context: str = "{}") -> str:
            """Customize the main server TypeScript file with basic API configuration."""
            return str(self.customize_main_server_file({}))
        
        @tool("validate_server_structure")
        def validate_server_structure_tool(context: str = "{}") -> str:
            """Validate that the generated server structure is complete and follows standards."""
            return str(self.validate_server_structure({}))
        
        # Add tools to the agent
        self.tools.extend([
            copy_template_structure_tool,
            customize_package_json_tool,
            customize_readme_tool,
            customize_main_server_file_tool,
            validate_server_structure_tool
        ])
    
    def copy_template_structure(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Copy the MCP server template structure to the target directory.
        
        Args:
            context: Contains server_name, website_url, and other configuration
            
        Returns:
            Dict with success status and details
        """
        try:
            print(f"📁 Copying template from: {self.template_dir}")
            print(f"📁 Target directory: {self.output_dir}")
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(self.output_dir), exist_ok=True)
            
            # Remove existing directory if it exists
            if os.path.exists(self.output_dir):
                print(f"⚠️ Removing existing server directory: {self.output_dir}")
                shutil.rmtree(self.output_dir)
            
            # Copy template structure
            shutil.copytree(self.template_dir, self.output_dir)
            print(f"✅ Template structure copied successfully")
            
            return {
                "success": True,
                "message": f"Template copied from {self.template_dir} to {self.output_dir}",
                "output_dir": self.output_dir,
                "template_dir": self.template_dir
            }
            
        except Exception as e:
            error_msg = f"Failed to copy template structure: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def customize_package_json(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Customize the package.json with server-specific information.
        
        Args:
            context: Contains server_name, website_url, and other configuration
            
        Returns:
            Dict with success status and details
        """
        try:
            package_json_path = os.path.join(self.output_dir, 'package.json')
            
            if not os.path.exists(package_json_path):
                return {
                    "success": False,
                    "error": "package.json not found in template"
                }
            
            # Read existing package.json
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # Extract domain for better naming
            parsed_url = urlparse(self.website_url)
            domain = parsed_url.netloc.replace('www.', '')
            
            # Customize package.json
            package_data['name'] = self.server_name
            package_data['description'] = f'MCP server for {domain} API integration'
            package_data['keywords'] = [
                'mcp',
                'model-context-protocol',
                'api-integration',
                domain.replace('.', '-'),
                'typescript'
            ]
            
            # Update repository if it exists
            if 'repository' in package_data:
                package_data['repository']['url'] = f"https://github.com/your-org/{self.server_name}"
            
            # Write customized package.json
            with open(package_json_path, 'w', encoding='utf-8') as f:
                json.dump(package_data, f, indent=2)
            
            print(f"✅ Customized package.json for {self.server_name}")
            
            return {
                "success": True,
                "message": "package.json customized successfully",
                "changes": {
                    "name": self.server_name,
                    "description": package_data['description'],
                    "keywords": package_data['keywords']
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to customize package.json: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def customize_readme(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Customize the README.md with server-specific information.
        
        Args:
            context: Contains server_name, website_url, and other configuration
            
        Returns:
            Dict with success status and details
        """
        try:
            readme_path = os.path.join(self.output_dir, 'README.md')
            
            if not os.path.exists(readme_path):
                return {
                    "success": False,
                    "error": "README.md not found in template"
                }
            
            # Extract domain info
            parsed_url = urlparse(self.website_url)
            domain = parsed_url.netloc.replace('www.', '')
            
            # Read existing README
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # Replace template placeholders
            readme_content = readme_content.replace('{{SERVER_NAME}}', self.server_name)
            readme_content = readme_content.replace('{{WEBSITE_URL}}', self.website_url)
            readme_content = readme_content.replace('{{DOMAIN}}', domain)
            readme_content = readme_content.replace('{{API_NAME}}', domain.title())
            
            # Write customized README
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            print(f"✅ Customized README.md for {self.server_name}")
            
            return {
                "success": True,
                "message": "README.md customized successfully",
                "placeholders_replaced": {
                    "SERVER_NAME": self.server_name,
                    "WEBSITE_URL": self.website_url,
                    "DOMAIN": domain,
                    "API_NAME": domain.title()
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to customize README.md: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }

    def customize_main_server_file(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Customize the main server TypeScript file with basic API configuration.
        
        Args:
            context: Contains server_name, website_url, and other configuration
            
        Returns:
            Dict with success status and details
        """
        try:
            # Common server file locations in templates
            possible_paths = [
                os.path.join(self.output_dir, 'src', 'index.ts'),
                os.path.join(self.output_dir, 'src', 'server.ts'),
                os.path.join(self.output_dir, 'src', 'main.ts'),
                os.path.join(self.output_dir, 'index.ts'),
                os.path.join(self.output_dir, 'server.ts')
            ]
            
            server_file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    server_file_path = path
                    break
            
            if not server_file_path:
                return {
                    "success": False,
                    "error": "Main server file not found in template"
                }
            
            # Extract domain info
            parsed_url = urlparse(self.website_url)
            domain = parsed_url.netloc.replace('www.', '')
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Read existing server file
            with open(server_file_path, 'r', encoding='utf-8') as f:
                server_content = f.read()
            
            # Replace template placeholders
            server_content = server_content.replace('{{SERVER_NAME}}', self.server_name)
            server_content = server_content.replace('{{WEBSITE_URL}}', self.website_url)
            server_content = server_content.replace('{{DOMAIN}}', domain)
            server_content = server_content.replace('{{API_NAME}}', domain.title())
            server_content = server_content.replace('{{BASE_URL}}', base_url)
            
            # Write customized server file
            with open(server_file_path, 'w', encoding='utf-8') as f:
                f.write(server_content)
            
            print(f"✅ Customized main server file: {server_file_path}")
            
            return {
                "success": True,
                "message": f"Main server file customized: {os.path.basename(server_file_path)}",
                "file_path": server_file_path,
                "placeholders_replaced": {
                    "SERVER_NAME": self.server_name,
                    "WEBSITE_URL": self.website_url,
                    "DOMAIN": domain,
                    "API_NAME": domain.title(),
                    "BASE_URL": base_url
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to customize main server file: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def validate_server_structure(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that the generated server structure is complete and follows standards.
        
        Args:
            context: Contains server_name, website_url, and other configuration
            
        Returns:
            Dict with validation results
        """
        try:
            required_files = [
                'package.json',
                'README.md',
                'tsconfig.json'
            ]
            
            # Check for main server file
            server_files = [
                'src/index.ts',
                'src/server.ts',
                'src/main.ts',
                'index.ts',
                'server.ts'
            ]
            
            validation_results = {
                "required_files": {},
                "server_file": None,
                "structure_valid": True,
                "missing_files": [],
                "warnings": []
            }
            
            # Check required files
            for file in required_files:
                file_path = os.path.join(self.output_dir, file)
                exists = os.path.exists(file_path)
                validation_results["required_files"][file] = exists
                
                if not exists:
                    validation_results["missing_files"].append(file)
                    validation_results["structure_valid"] = False
            
            # Check for main server file
            server_file_found = False
            for file in server_files:
                file_path = os.path.join(self.output_dir, file)
                if os.path.exists(file_path):
                    validation_results["server_file"] = file
                    server_file_found = True
                    break
            
            if not server_file_found:
                validation_results["missing_files"].append("main server file (index.ts, server.ts, etc.)")
                validation_results["structure_valid"] = False
            
            # Check for src directory structure
            src_dir = os.path.join(self.output_dir, 'src')
            if not os.path.exists(src_dir):
                validation_results["warnings"].append("No src directory found - using flat structure")
            
            if validation_results["structure_valid"]:
                print(f"✅ Server structure validation passed")
            else:
                print(f"⚠️ Server structure validation failed: {validation_results['missing_files']}")
            
            return {
                "success": True,
                "validation": validation_results
            }
            
        except Exception as e:
            error_msg = f"Failed to validate server structure: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get information about the generated server.
        
        Returns:
            Dict with server information
        """
        return {
            "server_name": self.server_name,
            "website_url": self.website_url,
            "output_dir": self.output_dir,
            "template_dir": self.template_dir,
            "template_type": "custom" if self.template_dir != os.path.join(os.getcwd(), '..', 'templates', 'mcp-server-template') else "default"
        }

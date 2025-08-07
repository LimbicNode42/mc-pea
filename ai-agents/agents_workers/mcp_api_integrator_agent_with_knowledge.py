"""
MCP API Integrator Agent with Knowledge Base

Agent responsible for integrating extracted API usage details into the generated MCP server.
Uses CrewAI Knowledge system to leverage MCP expertise for intelligent TypeScript code generation.
"""

from crewai import Agent, LLM
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List
from urllib.parse import urlparse
from core.agent_workers_config_loader import get_agent_config

# Set up file logging for debugging
log_dir = "debug_logs"
os.makedirs(log_dir, exist_ok=True)
log_filename = f"{log_dir}/mcp_api_integrator_knowledge_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging with Windows-compatible settings
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ],
    force=True  # Override any existing logging configuration
)

# Set console output encoding to handle Unicode on Windows
import sys
if sys.platform == "win32":
    import codecs
    from io import UnsupportedOperation
    # Only set encoding if running in a regular terminal (not Streamlit or other managed environments)
    try:
        if hasattr(sys.stdout, 'detach'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except (UnsupportedOperation, AttributeError):
        # Skip encoding setup if stdout/stderr can't be detached (e.g., in Streamlit)
        pass

logger = logging.getLogger(__name__)
logger.info(f"Starting MCP API Integrator Agent with Knowledge debug logging - log file: {log_filename}")


class MCPAPIIntegratorAgentWithKnowledge(Agent):
    """
    Agent responsible for integrating extracted API details into the MCP server.
    Uses CrewAI Knowledge to provide MCP expertise for intelligent code generation.
    """

    def __init__(self, website_url: str = None, server_name: str = None, mcp_server_path: str = None, **kwargs):
        logger.info(f"MCPAPIIntegratorAgentWithKnowledge.__init__ called with website_url={website_url}, server_name={server_name}, mcp_server_path={mcp_server_path}")
        
        load_dotenv()
        
        # Set default values if not provided
        if website_url is None:
            website_url = "https://api.example.com"
            logger.debug(f"Set default website_url: {website_url}")
        
        # Generate server name from website URL if not provided
        if not server_name:
            parsed = urlparse(website_url)
            domain = parsed.netloc.replace('www.', '').replace('.', '-')
            server_name = f"{domain}-api-mcp-server"
            logger.debug(f"Generated server_name: {server_name}")
        
        # Use custom server path if provided, otherwise use default
        if mcp_server_path:
            if os.path.isabs(mcp_server_path):
                server_path = mcp_server_path
            else:
                # Relative to current working directory
                server_path = os.path.abspath(mcp_server_path)
            logger.debug(f"Using custom server_path: {server_path}")
        else:
            # Default server path
            server_path = os.path.join(os.getcwd(), '..', 'mcp-servers', f"{server_name}")
            logger.debug(f"Using default server_path: {server_path}")

        # Validate server directory exists or can be created
        logger.debug(f"Creating server directory: {server_path}")
        os.makedirs(server_path, exist_ok=True)

        # Load agent configuration
        logger.info("Loading agent configuration...")
        config = get_agent_config('mcp_api_integrator_agent')
        
        if config is None:
            logger.error("Config is None!")
            raise ValueError("Could not load configuration for 'mcp_api_integrator_agent'. Check that the config file exists and is valid.")
        
        # Set up LLM
        llm_config = config.get("llm", "")
        logger.debug(f"LLM config: {llm_config}")
        
        if "claude" in llm_config:
            logger.info("Setting up Claude LLM...")
            llm = ChatAnthropic(
                model=config.get("llm", "claude-sonnet-4"),
                max_tokens=config.get("max_output_tokens", 8000),
                temperature=config.get("temperature", 0.2),
                max_retries=1,
                default_request_timeout=120,
                anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            )
            logger.info("Claude LLM configured successfully")
        elif "gemini" in llm_config:
            logger.info("Setting up Gemini LLM...")
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if not google_api_key:
                logger.error("GOOGLE_API_KEY not found!")
                raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini models")
            
            model_name = config.get("llm", "gemini-2.5-flash").replace("gemini/", "")
            logger.debug(f"Extracted model name: {model_name}")
            
            llm = LLM(
                model=f"gemini/{model_name}",
                api_key=google_api_key,
                max_tokens=config.get("max_input_tokens", 3000000),
                max_completion_tokens=config.get("max_output_tokens", 1000000),
                temperature=config.get("temperature", 0.2),
                reasoning_effort=config.get("reasoning_effort", "medium"),
            )
            logger.info("Gemini LLM configured successfully")
        else:
            logger.error(f"Unsupported LLM type: {llm_config}")
            raise ValueError(f"Unsupported LLM type in configuration: {llm_config}")
        
        # Create MCP Knowledge Sources
        logger.info("Creating MCP Knowledge sources...")
        
        # Load all knowledge files using proper file-based knowledge sources
        knowledge_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'knowledge'))
        knowledge_files = [
            'mcp-template-overview.txt',
            'mcp-protocol-reference.txt',
            'mcp-sdk-patterns.txt',
            'mcp-typescript-examples.txt',
            'api-analysis-guide.txt'
        ]
        
        # Verify knowledge files exist
        existing_files = []
        for filename in knowledge_files:
            full_path = os.path.join(knowledge_dir, filename)
            if os.path.exists(full_path):
                logger.debug(f"Loading knowledge file: {full_path}")
                existing_files.append(filename)
            else:
                logger.warning(f"Knowledge file not found: {full_path}")
        
        if not existing_files:
            logger.error(f"No knowledge files found in {knowledge_dir}")
            raise ValueError(f"MCP knowledge files not found. Expected files: {knowledge_files}")
        
        logger.info(f"Found {len(existing_files)} knowledge files")
        
        # Create TextFileKnowledgeSource with the existing files
        from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
        mcp_knowledge_source = TextFileKnowledgeSource(
            file_paths=existing_files  # Use relative paths from knowledge directory
        )
        
        # Set up embedder configuration based on LLM type
        embedder_config = None
        if "gemini" in llm_config:
            # Use Google embeddings for Gemini models
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if google_api_key:
                embedder_config = {
                    "provider": "google",
                    "config": {
                        "model": "gemini-embedding-001",
                        "api_key": google_api_key,
                        "task_type": "RETRIEVAL_DOCUMENT",  # Optimized for document search
                        "output_dimensionality": 3072  # Full dimension for highest quality (already normalized)
                    }
                }
                logger.info("Using Google gemini-embedding-001 with 3072 dimensions for knowledge system")
            else:
                logger.warning("GOOGLE_API_KEY not found, falling back to default embedder")
        elif "claude" in llm_config:
            # For Claude, we can use OpenAI embeddings or Voyage AI (recommended by Anthropic)
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                embedder_config = {
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-3-small",
                        "api_key": openai_api_key
                    }
                }
                logger.info("Using OpenAI embeddings for Claude-based knowledge system")
            else:
                logger.warning("OPENAI_API_KEY not found, falling back to default embedder")
        
        # Initialize parent class with knowledge and embedder
        logger.info("Initializing parent Agent class with knowledge...")
        init_kwargs = {
            'role': config.get("role", "MCP API Integrator"),
            'goal': config.get("goal", "Integrate API extraction results into MCP server using expert knowledge"),
            'backstory': config.get("backstory", "Expert TypeScript developer with comprehensive MCP protocol knowledge"),
            'llm': llm,
            'knowledge_sources': [mcp_knowledge_source],  # Use file-based knowledge with embedder
            'tools': [],  # No tools needed - using LLM reasoning with knowledge
            'respect_context_window': config.get('respect_context_window', True),
            'cache': config.get('cache', False),
            'reasoning': config.get('reasoning', False),
            'max_iter': config.get('max_iterations', 10),
            'max_retry_limit': config.get('max_retry_limit', 1),
            'verbose': config.get('verbose', True),
            'allow_delegation': config.get('allow_delegation', False)
        }
        
        # Add embedder configuration if available
        if embedder_config:
            init_kwargs['embedder'] = embedder_config
            logger.info(f"Using embedder: {embedder_config['provider']}")
        
        # Add any additional kwargs
        init_kwargs.update(kwargs)
        
        super().__init__(**init_kwargs)
        logger.info("Parent Agent class initialized successfully with MCP knowledge")
        
        # Store instance variables after super().__init__() to avoid Pydantic issues
        logger.info("Storing instance variables...")
        object.__setattr__(self, 'website_url', website_url)
        object.__setattr__(self, 'server_name', server_name)
        object.__setattr__(self, 'mcp_server_path', server_path)
        
        # Store workflow state
        object.__setattr__(self, '_extraction_results', None)
        object.__setattr__(self, '_last_call_time', 0)
        object.__setattr__(self, '_min_call_interval', float(os.getenv('MCP_INTEGRATOR_RATE_LIMIT', '2.0')))
        
        logger.info(f"Agent initialization complete with MCP knowledge base!")
    
    def _apply_rate_limiting(self):
        """Apply rate limiting delay between LLM calls to prevent rate limit errors."""
        current_time = time.time()
        time_since_last_call = current_time - self._last_call_time
        
        if time_since_last_call < self._min_call_interval:
            delay = self._min_call_interval - time_since_last_call
            print(f"Rate limiting: waiting {delay:.1f}s before next API call")
            time.sleep(delay)
        
        self._last_call_time = time.time()
    
    def set_extraction_results(self, extraction_results: List[Dict[str, Any]]) -> None:
        """Set the extraction results for processing."""
        logger.info(f"set_extraction_results called with {len(extraction_results)} results")
        self._extraction_results = extraction_results
    
    def generate_mcp_tools_and_resources(self) -> str:
        """
        Generate MCP tools and resources TypeScript code based on extraction results.
        Uses the LLM with MCP knowledge to intelligently analyze and generate code.
        """
        logger.info("Starting MCP tools and resources generation...")
        
        if not self._extraction_results:
            logger.error("No extraction results available")
            return "Error: No extraction results available for processing"
        
        # Apply rate limiting
        self._apply_rate_limiting()
        
        # Create a detailed prompt for the LLM with the extraction results
        prompt = f"""
As an expert MCP (Model Context Protocol) TypeScript developer, analyze the following API extraction results and generate complete MCP server TypeScript code.

**API Extraction Results:**
{json.dumps(self._extraction_results, indent=2)}

**Target Server Details:**
- Server Name: {self.server_name}
- Website URL: {self.website_url}
- Server Path: {self.mcp_server_path}

**Requirements:**
1. Generate TypeScript code for src/tools/index.ts with tool definitions and handlers
2. Generate TypeScript code for src/resources/index.ts with resource definitions and handlers
3. Follow MCP SDK patterns exactly as shown in the knowledge base
4. Use proper JSON Schema for tool input validation
5. Implement proper error handling and response formatting
6. Create meaningful tool names and descriptions based on the API endpoints
7. Generate appropriate resources for data retrieval endpoints
8. Include authentication handling where needed

**Output Format:**
Provide the complete TypeScript code in two sections:

## Tools Implementation (src/tools/index.ts)
```typescript
[Complete tools implementation]
```

## Resources Implementation (src/resources/index.ts) 
```typescript
[Complete resources implementation]
```

Analyze the extracted API endpoints and create comprehensive, production-ready MCP tools and resources that follow all best practices from the knowledge base.
"""

        try:
            logger.info("Calling LLM for MCP code generation...")
            
            # Use the agent's LLM directly with the knowledge context
            # The knowledge will be automatically retrieved based on the prompt
            if hasattr(self.llm, 'invoke'):
                response = self.llm.invoke(prompt)
            elif hasattr(self.llm, 'predict'):
                response = self.llm.predict(prompt)
            else:
                # Fallback for different LLM types
                response = str(self.llm.generate([prompt]))
            
            logger.info("MCP code generation completed successfully")
            return response
            
        except Exception as error:
            logger.error(f"Error in MCP code generation: {error}")
            return f"Error generating MCP code: {str(error)}"
    
    def update_mcp_server_files(self, generated_code: str) -> Dict[str, Any]:
        """
        Update the actual MCP server files with the generated code.
        Parses the generated code and writes to appropriate files.
        """
        logger.info("Starting MCP server files update...")
        
        results = {
            "tools_updated": False,
            "resources_updated": False,
            "errors": []
        }
        
        try:
            # Parse the generated code to extract tools and resources sections
            tools_code = self._extract_code_section(generated_code, "Tools Implementation", "typescript")
            resources_code = self._extract_code_section(generated_code, "Resources Implementation", "typescript")
            
            # Update tools file
            if tools_code:
                tools_file_path = os.path.join(self.mcp_server_path, 'src', 'tools', 'index.ts')
                os.makedirs(os.path.dirname(tools_file_path), exist_ok=True)
                
                with open(tools_file_path, 'w', encoding='utf-8') as f:
                    f.write(tools_code)
                
                logger.info(f"Updated tools file: {tools_file_path}")
                results["tools_updated"] = True
            else:
                error_msg = "No tools code section found in generated response"
                logger.error(f"{error_msg}")
                results["errors"].append(error_msg)
            
            # Update resources file  
            if resources_code:
                resources_file_path = os.path.join(self.mcp_server_path, 'src', 'resources', 'index.ts')
                os.makedirs(os.path.dirname(resources_file_path), exist_ok=True)
                
                with open(resources_file_path, 'w', encoding='utf-8') as f:
                    f.write(resources_code)
                
                logger.info(f"Updated resources file: {resources_file_path}")
                results["resources_updated"] = True
            else:
                error_msg = "No resources code section found in generated response"
                logger.error(f"{error_msg}")
                results["errors"].append(error_msg)
                
        except Exception as error:
            error_msg = f"Error updating MCP server files: {str(error)}"
            logger.error(f"{error_msg}")
            results["errors"].append(error_msg)
        
        return results
    
    def _extract_code_section(self, content: str, section_name: str, language: str) -> str:
        """Extract code from a markdown code block section."""
        import re
        
        # Look for section header followed by code block
        pattern = rf"#{{{1,3}}}\s*{re.escape(section_name)}.*?\n```{language}\n(.*?)\n```"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Fallback: look for any TypeScript code block
        pattern = rf"```{language}\n(.*?)\n```"
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if matches:
            # Return the largest code block (most likely to be complete)
            return max(matches, key=len).strip()
        
        return ""
    
    def process_api_integration(self) -> Dict[str, Any]:
        """
        Complete workflow to process API extraction results and update MCP server.
        """
        logger.info("Starting complete API integration workflow...")
        
        workflow_results = {
            "generation_successful": False,
            "files_updated": False,
            "generated_code": "",
            "file_update_results": {},
            "errors": []
        }
        
        try:
            # Step 1: Generate MCP code using LLM with knowledge
            logger.info("Step 1: Generating MCP TypeScript code...")
            generated_code = self.generate_mcp_tools_and_resources()
            
            if "Error" in generated_code:
                workflow_results["errors"].append(generated_code)
                return workflow_results
            
            workflow_results["generated_code"] = generated_code
            workflow_results["generation_successful"] = True
            
            # Step 2: Update MCP server files
            logger.info("Step 2: Updating MCP server files...")
            file_results = self.update_mcp_server_files(generated_code)
            workflow_results["file_update_results"] = file_results
            
            if file_results.get("tools_updated") or file_results.get("resources_updated"):
                workflow_results["files_updated"] = True
            
            workflow_results["errors"].extend(file_results.get("errors", []))
            
            logger.info("API integration workflow completed successfully")
            
        except Exception as error:
            error_msg = f"Error in API integration workflow: {str(error)}"
            logger.error(f"{error_msg}")
            workflow_results["errors"].append(error_msg)
        
        return workflow_results

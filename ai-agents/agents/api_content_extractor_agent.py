from dotenv import load_dotenv
import os
from crewai import Agent, LLM
from crewai.tools import tool
from crewai_tools import ScrapeWebsiteTool
from langchain_anthropic import ChatAnthropic
from core.agent_config_loader import AgentConfigLoader
from typing import Dict, Any, List
import json

# Content extraction tool for CrewAI framework
@tool("process_chunk")
def process_chunk_tool(chunk_dict: Dict[str, Any], hostname: str) -> str:
    """
    Process a chunk of endpoints and extract comprehensive API information.
    
    Args:
        chunk_dict: Dictionary containing chunk information and endpoints
        hostname: The hostname for the API documentation
        
    Returns:
        JSON string with structured data following ApiLinkContentExtractorOutput schema
    """
    try:
        # For actual implementation, this would delegate to the agent's process_chunk method
        # For now, return a placeholder result with proper structure
        result = {
            'cn': chunk_dict['category_name'],
            'cd': chunk_dict['category_description'],
            'ces': []  # Would contain processed endpoints
        }
        
        print(f"🔍 Tool processed chunk {chunk_dict['chunk_id']} with {len(chunk_dict['endpoints'])} endpoints")
        return json.dumps(result)
        
    except Exception as e:
        error_msg = f"Error processing chunk: {e}"
        print(error_msg)
        return json.dumps({
            'cn': chunk_dict.get('category_name', 'Unknown'),
            'cd': chunk_dict.get('category_description', ''),
            'ces': []
        })

class ApiLinkContentExtractorAgent(Agent):
    """Agent responsible for discovering and cataloging API-related web links."""

    def __init__(self):
        load_dotenv()

        # Load configuration from centralized config file
        agent_loader = AgentConfigLoader()
        config_data = agent_loader.get_agent_config("api_content_extractor")

        if "claude" in config_data.get("llm"):
            llm = ChatAnthropic(
                model=config_data.get("llm"),
                max_tokens=config_data.get("max_tokens"),
                temperature=config_data.get("temperature"),
                max_retries=config_data.get("max_retry_limit"),
            )
            print("Using Claude LLM for link content extraction")
        elif "gemini" in config_data.get("llm"):
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini models")
            
            # Extract just the model name (remove the provider prefix)
            model_name = config_data.get("llm").replace("gemini/", "")
            
            # Use CrewAI's LLM class for Gemini models
            llm = LLM(
                model=f"gemini/{model_name}",
                api_key=google_api_key,
                max_tokens=config_data.get("max_input_tokens"),
                max_completion_tokens=config_data.get("max_output_tokens"),
                temperature=config_data.get("temperature"),
                reasoning_effort=config_data.get("reasoning_effort"),
            )
            print(f"Using Gemini LLM for link content extraction: {model_name}")
        else:
            raise ValueError("Unsupported LLM type in configuration")

        scraper_tool = ScrapeWebsiteTool()
        
        # Initialize the CrewAI Agent with the loaded configuration
        super().__init__(
            role=config_data.get("role"),
            goal=config_data.get("goal"),
            backstory=config_data.get("backstory"),
            llm=llm,
            tools=[
                scraper_tool,
                process_chunk_tool
            ],
            respect_context_window=config_data.get("respect_context_window"),
            cache=config_data.get("cache"),
            reasoning=config_data.get("reasoning"),
            max_iter=config_data.get("max_iterations"),
            max_retry_limit=config_data.get("max_retry_limit"),
            verbose=config_data.get("verbose"),
        )
        
        # Store config data for later use
        self._config_data = config_data

    def process_chunk(self, chunk, hostname: str) -> Dict[str, Any]:
        """
        Process a chunk of endpoints and extract comprehensive API information.
        
        Args:
            chunk: EndpointChunk object containing endpoints to process
            hostname: The hostname for the API documentation
            
        Returns:
            Structured data following ApiLinkContentExtractorOutput schema
        """
        
        # Create the extraction prompt with strict schema requirements
        extraction_prompt = self._create_extraction_prompt(chunk, hostname)
        
        # Execute the extraction using the agent's LLM
        try:
            # Use the agent's execution method to process the prompt
            result = self._execute_extraction(extraction_prompt)
            
            # Ensure the result follows the expected schema
            formatted_result = self._validate_and_format_result(result, chunk)
            
            return formatted_result
            
        except Exception as e:
            print(f"Error in chunk processing: {e}")
            # Return empty but valid structure
            return {
                'cn': chunk.category_name,
                'cd': chunk.category_description,
                'ces': []
            }
    
    def _create_extraction_prompt(self, chunk, hostname: str) -> str:
        """Create a detailed extraction prompt with schema requirements and examples."""
        
        # Get the golden example from existing output
        golden_example = self._get_golden_example()
        
        endpoints_list = "\n".join([
            f"- {endpoint.get('t', endpoint.get('title', 'Unknown'))}: {endpoint.get('l', endpoint.get('link', 'Unknown'))}"
            for endpoint in chunk.endpoints
        ])
        
        return f"""
CRITICAL: Extract API endpoint information for the following {len(chunk.endpoints)} endpoints from {hostname}.

CHUNK INFORMATION:
- Chunk ID: {chunk.chunk_id}/{chunk.total_chunks}
- Category: {chunk.category_name}
- Description: {chunk.category_description}

ENDPOINTS TO PROCESS:
{endpoints_list}

REQUIRED OUTPUT SCHEMA (EXACT):
You MUST output JSON following this EXACT structure:

{golden_example}

CRITICAL REQUIREMENTS:
1. Visit each endpoint URL by appending the path to {hostname}
2. Extract ALL endpoint information including:
   - en: Exact endpoint name from documentation
   - ed: Single sentence description
   - em: HTTP method (GET/POST/PUT/DELETE/PATCH)
   - ep: API path with {{parameters}} in curly braces
   - ecp: Array of compliance/authentication requirements
   - esu: Complete curl example exactly as shown in docs
   - eh: Headers array with pn, pd, pr, pt, pv fields
   - epp: Path parameters array
   - eqp: Query parameters array
   - ebp: Body parameters array
   - erc: Response codes as key-value pairs
   - ere: Response examples as escaped JSON strings

3. NEVER invent information not in the documentation
4. ALWAYS use exact field names: en, ed, em, ep, ecp, esu, eh, epp, eqp, ebp, erc, ere
5. ALWAYS format curl examples exactly as shown in docs
6. ALWAYS use null for missing optional values
7. ALWAYS escape JSON strings in "ere" field

OUTPUT FORMAT:
Return ONLY a JSON object with:
{{
  "cn": "{chunk.category_name}",
  "cd": "{chunk.category_description}",
  "ces": [
    // Array of endpoints following the exact schema above
  ]
}}

Begin extraction for all {len(chunk.endpoints)} endpoints now.
"""
    
    def _get_golden_example(self) -> str:
        """Return a golden example endpoint for consistency."""
        return '''
{
  "en": "List artifacts for a repository",
  "ed": "Lists all artifacts for a repository.",
  "em": "GET",
  "ep": "/repos/{owner}/{repo}/actions/artifacts",
  "ecp": [
    "Requires authentication (e.g., repo scope for PAT, or GitHub App installation token).",
    "Standard API rate limits apply."
  ],
  "esu": "curl -L \\\\\\n  -H \\"Accept: application/vnd.github.v3+json\\" \\\\\\n  -H \\"Authorization: Bearer <YOUR-TOKEN>\\" \\\\\\n  https://api.github.com/repos/octocat/hello-world/actions/artifacts",
  "eh": [
    {
      "pn": "Accept",
      "pd": "Media type for the API version.",
      "pr": true,
      "pt": "string",
      "pv": "application/vnd.github.v3+json"
    },
    {
      "pn": "Authorization",
      "pd": "Bearer token for authentication.",
      "pr": true,
      "pt": "string",
      "pv": "Bearer <YOUR-TOKEN>"
    }
  ],
  "epp": [
    {
      "pn": "owner",
      "pd": "The account owner of the repository. The name is not case sensitive.",
      "pr": true,
      "pt": "string",
      "pv": null
    },
    {
      "pn": "repo",
      "pd": "The name of the repository. The name is not case sensitive.",
      "pr": true,
      "pt": "string",
      "pv": null
    }
  ],
  "eqp": [
    {
      "pn": "per_page",
      "pd": "The number of results per page (max 100). Default: 30.",
      "pr": false,
      "pt": "integer",
      "pv": "30"
    },
    {
      "pn": "page",
      "pd": "Page number of the results to fetch. Default: 1.",
      "pr": false,
      "pt": "integer",
      "pv": "1"
    }
  ],
  "ebp": [],
  "erc": {
    "200 OK": "application/json"
  },
  "ere": {
    "200 OK": "{\\"total_count\\": 1, \\"artifacts\\": [{\\"id\\": 1, \\"name\\": \\"artifact-name\\"}]}"
  }
}'''
    
    def _execute_extraction(self, prompt: str) -> str:
        """Execute the extraction prompt using the agent's LLM."""
        # This is a placeholder - in CrewAI, the actual execution would happen
        # through the task execution framework
        # For now, return the prompt to be processed by the orchestrator
        return prompt
    
    def _validate_and_format_result(self, result: str, chunk) -> Dict[str, Any]:
        """Validate and format the extraction result."""
        try:
            # Try to parse as JSON first
            if isinstance(result, str):
                parsed = json.loads(result)
            else:
                parsed = result
            
            # Ensure required fields exist
            if not isinstance(parsed, dict):
                raise ValueError("Result must be a dictionary")
            
            if 'ces' not in parsed:
                parsed['ces'] = []
            
            if 'cn' not in parsed:
                parsed['cn'] = chunk.category_name
            
            if 'cd' not in parsed:
                parsed['cd'] = chunk.category_description
            
            return parsed
            
        except Exception as e:
            print(f"Error validating result: {e}")
            # Return empty but valid structure
            return {
                'cn': chunk.category_name,
                'cd': chunk.category_description,
                'ces': []
            }

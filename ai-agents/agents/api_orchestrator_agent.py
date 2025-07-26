"""
API Content Extraction Orchestrator Agent

This agent coordinates multiple content extractor agents to process large-scale API
documentation efficiently by partitioning work and managing parallel execution.
"""

from crewai import Agent, LLM
from crewai.tools import tool
from typing import List, Dict, Any
from core.agent_config_loader import AgentConfigLoader
from dotenv import load_dotenv
import os
import json
from dataclasses import dataclass

@dataclass
class EndpointChunk:
    """Represents a chunk of endpoints to be processed by a single agent"""
    chunk_id: int
    category_name: str
    category_description: str
    category_index: int
    endpoints: List[Dict[str, Any]]
    total_chunks: int

# Orchestrator tools using @tool decorator
@tool("partition_endpoints")
def partition_endpoints_tool(discovery_output: str, chunk_size: int = 5) -> str:
    """
    Partition the link discovery output into manageable chunks for parallel processing.
    
    Args:
        discovery_output: JSON string from ApiLinkDiscoveryTask
        chunk_size: Number of endpoints per chunk (default: 5)
        
    Returns:
        JSON string containing list of endpoint chunks
    """
    try:
        # Parse the discovery output
        discovery_data = json.loads(discovery_output)
        
        chunks = []
        chunk_id = 0
        
        # Process each category from the discovery output
        for cat_idx, category in enumerate(discovery_data.get('cs', [])):
            category_name = category.get('n', category.get('category_name', f'Category_{cat_idx}'))
            category_description = category.get('cd', category.get('description', ''))
            links = category.get('ls', category.get('links', []))
            
            # Split category links into chunks
            for i in range(0, len(links), chunk_size):
                chunk_endpoints = links[i:i + chunk_size]
                
                chunk_dict = {
                    "chunk_id": chunk_id,
                    "category_name": category_name,
                    "category_description": category_description,
                    "category_index": cat_idx,
                    "endpoints": chunk_endpoints,
                    "total_chunks": 0,  # Will be set after all chunks are created
                }
                
                chunks.append(chunk_dict)
                chunk_id += 1
        
        # Update total_chunks for all chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk["total_chunks"] = total_chunks
        
        print(f"📦 Partitioned {sum(len(chunk['endpoints']) for chunk in chunks)} endpoints into {len(chunks)} chunks")
        return json.dumps(chunks)
        
    except Exception as e:
        error_msg = f"Error partitioning endpoints: {e}"
        print(error_msg)
        return json.dumps({"error": error_msg, "chunks": []})

@tool("coordinate_extraction")
def coordinate_extraction_tool(chunks_json: str, hostname: str) -> str:
    """
    Coordinate multiple content extractor agents to process endpoint chunks in parallel.
    
    Args:
        chunks_json: JSON string containing list of endpoint chunks
        hostname: The hostname for the API documentation
        
    Returns:
        JSON string containing aggregated results from all chunk processors
    """
    try:
        chunks = json.loads(chunks_json)
        
        print(f"🎯 Coordinating extraction for {len(chunks)} chunks on {hostname}")
        
        # Import here to avoid circular imports
        from agents.api_content_extractor_agent import ApiLinkContentExtractorAgent
        
        chunk_results = []
        
        # For now, process sequentially to ensure stability
        # TODO: Implement true async parallel processing once CrewAI supports it
        for chunk in chunks:
            try:
                print(f"Processing chunk {chunk['chunk_id'] + 1}/{len(chunks)} with {len(chunk['endpoints'])} endpoints")
                
                # Create a fresh extractor agent for this chunk
                extractor_agent = ApiLinkContentExtractorAgent()
                
                # Create EndpointChunk object from dict
                chunk_obj = EndpointChunk(**chunk)
                
                # Process this chunk
                result = extractor_agent.process_chunk(chunk_obj, hostname)
                chunk_results.append(result)
                
                print(f"✅ Completed chunk {chunk['chunk_id'] + 1}")
                
            except Exception as chunk_error:
                print(f"❌ Error processing chunk {chunk['chunk_id']}: {chunk_error}")
                # Add empty but valid result for failed chunk
                chunk_results.append({
                    'cn': chunk['category_name'],
                    'cd': chunk['category_description'],
                    'ces': []
                })
        
        return json.dumps(chunk_results)
        
    except Exception as e:
        error_msg = f"Error coordinating extraction: {e}"
        print(error_msg)
        return json.dumps({"error": error_msg, "results": []})

@tool("merge_chunk_outputs")
def merge_chunk_outputs_tool(chunk_results_json: str) -> str:
    """
    Merge chunk processing results back into the final structured output.
    
    Args:
        chunk_results_json: JSON string containing results from all chunk processors
        
    Returns:
        JSON string in ApiLinkContentExtractorOutput format
    """
    try:
        chunk_results = json.loads(chunk_results_json)
        
        print(f"🔄 Merging results from {len(chunk_results)} chunk processors")
        
        # Group results by category
        categories = {}
        
        for result in chunk_results:
            if 'cn' in result and 'ces' in result:
                cat_name = result['cn']
                cat_desc = result['cd']
                endpoints = result['ces']
                
                if cat_name not in categories:
                    categories[cat_name] = {
                        'n': cat_name,
                        'cd': cat_desc,
                        'ls': []
                    }
                
                # Add endpoints to category
                categories[cat_name]['ls'].extend(endpoints)
        
        # Create final output structure
        final_output = {
            'cs': list(categories.values())
        }
        
        total_endpoints = sum(len(cat['ls']) for cat in categories.values())
        print(f"✅ Merged {total_endpoints} endpoints across {len(categories)} categories")
        
        return json.dumps(final_output)
        
    except Exception as e:
        error_msg = f"Error merging chunk outputs: {e}"
        print(error_msg)
        return json.dumps({"error": error_msg, "cs": []})

class ApiContentOrchestratorAgent(Agent):
    def __init__(self):
        load_dotenv()
        
        # Load agent configuration
        agent_loader = AgentConfigLoader()
        config_data = agent_loader.get_agent_config("api_orchestrator")
        
        # Setup LLM similar to existing agents
        if "claude" in config_data.get("llm"):
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model=config_data.get("llm"),
                max_tokens=config_data.get("max_tokens"),
                temperature=config_data.get("temperature"),
                max_retries=config_data.get("max_retry_limit"),
            )
            print("Using Claude LLM for orchestrator")
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
            print(f"Using Gemini LLM for orchestrator: {model_name}")
        else:
            raise ValueError("Unsupported LLM type in configuration")
        
        super().__init__(
            role=config_data.get("role"),
            goal=config_data.get("goal"),
            backstory=config_data.get("backstory"),
            llm=llm,
            tools=[
                partition_endpoints_tool,
                coordinate_extraction_tool,
                merge_chunk_outputs_tool
            ],
            respect_context_window=config_data.get("respect_context_window"),
            cache=config_data.get("cache"),
            reasoning=config_data.get("reasoning"),
            max_iter=config_data.get("max_iterations"),
            max_retry_limit=config_data.get("max_retry_limit"),
            verbose=config_data.get("verbose")
        )
        
        self._config_data = config_data

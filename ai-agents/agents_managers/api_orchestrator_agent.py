"""
API Documentation Extraction Manager Agent

This agent acts as a manager in CrewAI's hierarchical process, coordinating
discovery and content extraction tasks across multiple specialized agents.
Includes tools for chunking and coordinating parallel extraction.
"""

from crewai import Agent, LLM
from crewai.tools import tool
from core.agent_managers_config_loader import AgentConfigLoader
from dotenv import load_dotenv
import os
import json
from typing import List, Dict, Any

class ApiContentOrchestratorAgent(Agent):
    def __init__(self):
        load_dotenv()
        
        # Load agent configuration - update to use manager config
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
            print("Using Claude LLM for manager")
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
            print(f"Using Gemini LLM for manager: {model_name}")
        else:
            raise ValueError("Unsupported LLM type in configuration")
        
        super().__init__(
            role=config_data.get("role"),
            goal=config_data.get("goal"),
            backstory=config_data.get("backstory"),
            llm=llm,
            respect_context_window=config_data.get("respect_context_window"),
            cache=config_data.get("cache"),
            reasoning=config_data.get("reasoning"),
            max_iter=config_data.get("max_iterations"),
            max_retry_limit=config_data.get("max_retry_limit"),
            verbose=config_data.get("verbose"),
            tools=[self.chunk_discovery_results, self.coordinate_extraction]
        )
        
        self._config_data = config_data

    @tool("chunk_discovery_results")
    def chunk_discovery_results(self, discovery_data: str, num_chunks: int = 3) -> List[Dict[str, Any]]:
        """
        Split API discovery results into manageable chunks for parallel processing.
        
        Args:
            discovery_data: JSON string of discovery results
            num_chunks: Number of chunks to create (default 3)
            
        Returns:
            List of chunk dictionaries with endpoint data
        """
        try:
            data = json.loads(discovery_data) if isinstance(discovery_data, str) else discovery_data
            
            if not data or 'ocs' not in data:
                return []
            
            categories = data['ocs']
            hostname = data.get('hostname', '')
            
            # Calculate endpoints per chunk
            total_endpoints = sum(len(cat.get('ces', [])) for cat in categories)
            endpoints_per_chunk = max(1, total_endpoints // num_chunks)
            
            chunks = []
            current_chunk = {'hostname': hostname, 'endpoints': []}
            current_size = 0
            
            for category in categories:
                for endpoint in category.get('ces', []):
                    if current_size >= endpoints_per_chunk and len(chunks) < num_chunks - 1:
                        chunks.append(current_chunk)
                        current_chunk = {'hostname': hostname, 'endpoints': []}
                        current_size = 0
                    
                    current_chunk['endpoints'].append({
                        'category': category.get('name', ''),
                        'endpoint': endpoint
                    })
                    current_size += 1
            
            if current_chunk['endpoints']:
                chunks.append(current_chunk)
            
            return chunks
            
        except Exception as e:
            print(f"Error chunking data: {e}")
            return []
    
    @tool("coordinate_extraction") 
    def coordinate_extraction(self, chunks_data: str) -> Dict[str, Any]:
        """
        Coordinate the parallel extraction of chunked endpoint data.
        
        Args:
            chunks_data: JSON string of chunked endpoint data
            
        Returns:
            Coordination instructions for extraction agents
        """
        try:
            chunks = json.loads(chunks_data) if isinstance(chunks_data, str) else chunks_data
            
            coordination_plan = {
                'total_chunks': len(chunks),
                'extraction_strategy': 'parallel',
                'chunk_assignments': []
            }
            
            for i, chunk in enumerate(chunks):
                assignment = {
                    'chunk_id': i + 1,
                    'endpoints_count': len(chunk.get('endpoints', [])),
                    'hostname': chunk.get('hostname', ''),
                    'processing_instructions': f"Process chunk {i+1} with {len(chunk.get('endpoints', []))} endpoints"
                }
                coordination_plan['chunk_assignments'].append(assignment)
            
            return coordination_plan
            
        except Exception as e:
            print(f"Error coordinating extraction: {e}")
            return {'error': str(e)}

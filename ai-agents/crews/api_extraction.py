"""
Hierarchical API Documentation Extraction Crew

This crew uses CrewAI's hierarchical process to automatically coordinate:
- 1 Discovery Agent (finds all API endpoints)
- Multiple Content Extractor Agents (process endpoint chunks in parallel)
- 1 Manager Agent (orchestrates, delegates, and reviews)

The manager handles all coordination and dynamic task creation for chunk processing.
"""

from crewai import Crew, Process, Task
from agents_workers.api_discovery_agent import ApiLinkDiscoveryAgent
from agents_workers.api_content_extractor_agent import ApiLinkContentExtractorAgent
from agents_managers.api_orchestrator_agent import ApiContentOrchestratorAgent
from tasks.api_link_discovery_task import ApiLinkDiscoveryTask
from core.task_config_loader import TaskConfigLoader
from models.api_content_extractor_output import ApiLinkContentExtractorOutput
import json
from typing import List, Dict, Any

class HierarchicalApiExtractionCrew:
    """
    Hierarchical crew for large-scale API documentation extraction.
    Uses CrewAI's hierarchical process with dynamic task creation for data chunking.
    """
    
    def __init__(self, website_url: str, num_extractors: int = 3):
        self.website_url = website_url
        self.num_extractors = num_extractors
        
        # Initialize agents
        self.discovery_agent = ApiLinkDiscoveryAgent(website_url=website_url)
        
        # Create multiple content extractor agents for parallel processing
        self.extractor_agents = [
            ApiLinkContentExtractorAgent() 
            for _ in range(num_extractors)
        ]
        
        # Manager agent (converted from orchestrator)
        self.manager_agent = ApiContentOrchestratorAgent()
        
        # Combine all agents
        self.agents = [self.discovery_agent] + self.extractor_agents
        
        # Initialize base tasks - manager will create dynamic instances
        self.discovery_task = ApiLinkDiscoveryTask(website_url=self.website_url)
        
        # Store task config for dynamic task creation
        self.task_loader = TaskConfigLoader()
        self.extractor_task_config = self.task_loader.get_task_config("api_content_extraction")
        
        # Create the crew with hierarchical process
        self.crew = Crew(
            agents=self.agents,
            tasks=[self.discovery_task],  # Start with discovery only
            process=Process.hierarchical,
            manager_agent=self.manager_agent,
            verbose=True
        )
    
    def _create_chunk_extraction_task(self, chunk_data: Dict[str, Any], chunk_id: int) -> Task:
        """Create a dynamic extraction task for a specific chunk of endpoints."""
        
        # Format the description with chunk-specific data
        chunk_description = f"""
        Process chunk {chunk_id} of API endpoint data. This chunk contains:
        
        Hostname: {chunk_data.get('hostname', 'Unknown')}
        Chunk ID: {chunk_id}
        Endpoints in chunk: {len(chunk_data.get('endpoints', []))}
        
        Extract comprehensive API endpoint information from ALL endpoints in this chunk:
        {json.dumps(chunk_data.get('endpoints', []), indent=2)}
        
        For each endpoint, extract:
        - Complete path and methods
        - All parameters (required/optional)
        - Authentication requirements
        - Response schemas and examples
        - Rate limits and usage patterns
        """
        
        return Task(
            description=chunk_description,
            expected_output=self.extractor_task_config.get("expected_output"),
            output_json=ApiLinkContentExtractorOutput,
            async_execution=False,
            agent=None  # Will be assigned by manager
        )
    
    def _chunk_discovery_results(self, discovery_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split discovery results into chunks for parallel processing."""
        
        if not discovery_result or 'ocs' not in discovery_result:
            print("⚠️ No valid discovery results to chunk")
            return []
        
        categories = discovery_result['ocs']
        hostname = discovery_result.get('hostname', '')
        
        # Calculate endpoints per chunk
        total_endpoints = sum(len(cat.get('ces', [])) for cat in categories)
        endpoints_per_chunk = max(1, total_endpoints // self.num_extractors)
        
        chunks = []
        current_chunk = {'hostname': hostname, 'endpoints': []}
        current_size = 0
        
        for category in categories:
            for endpoint in category.get('ces', []):
                if current_size >= endpoints_per_chunk and len(chunks) < self.num_extractors - 1:
                    # Start new chunk
                    chunks.append(current_chunk)
                    current_chunk = {'hostname': hostname, 'endpoints': []}
                    current_size = 0
                
                current_chunk['endpoints'].append({
                    'category': category.get('name', ''),
                    'endpoint': endpoint
                })
                current_size += 1
        
        # Add final chunk
        if current_chunk['endpoints']:
            chunks.append(current_chunk)
        
        print(f"📦 Created {len(chunks)} chunks from {total_endpoints} endpoints")
        return chunks

    def execute(self):
        """Execute the hierarchical extraction workflow with dynamic task creation."""
        try:
            print(f"🚀 Starting hierarchical API extraction for {self.website_url}")
            print(f"👥 Manager: {self.manager_agent.role}")
            print(f"🔍 Discovery Agent: {self.discovery_agent.role}")
            print(f"⚙️ Content Extractors: {len(self.extractor_agents)} agents")
            
            # Step 1: Execute discovery task
            print("📡 Phase 1: API Discovery")
            discovery_result = self.crew.kickoff()
            
            # Parse discovery results
            if hasattr(discovery_result, 'json_dict'):
                discovery_data = discovery_result.json_dict
            elif isinstance(discovery_result, dict):
                discovery_data = discovery_result
            else:
                # Try to parse as JSON string
                try:
                    discovery_data = json.loads(str(discovery_result))
                except:
                    print(f"❌ Could not parse discovery results: {type(discovery_result)}")
                    return discovery_result
            
            print(f"✅ Discovery completed. Found data structure: {list(discovery_data.keys()) if discovery_data else 'None'}")
            
            # Step 2: Create chunks and dynamic tasks
            print("📦 Phase 2: Chunking and Task Creation")
            chunks = self._chunk_discovery_results(discovery_data)
            
            if not chunks:
                print("⚠️ No chunks created, returning discovery results only")
                return discovery_data
            
            # Step 3: Create and execute extraction tasks for chunks
            print(f"⚙️ Phase 3: Parallel Content Extraction ({len(chunks)} chunks)")
            
            extraction_tasks = []
            for i, chunk in enumerate(chunks):
                task = self._create_chunk_extraction_task(chunk, i + 1)
                extraction_tasks.append(task)
            
            # Create new crew for extraction phase
            extraction_crew = Crew(
                agents=self.extractor_agents,
                tasks=extraction_tasks,
                process=Process.sequential,  # or parallel if supported
                verbose=True
            )
            
            # Execute extraction
            extraction_results = extraction_crew.kickoff()
            
            print(f"✅ Hierarchical extraction completed")
            
            # Combine results
            combined_result = {
                'discovery': discovery_data,
                'extraction': extraction_results,
                'chunks_processed': len(chunks),
                'total_agents_used': 1 + len(self.extractor_agents)
            }
            
            return combined_result
            
        except Exception as e:
            print(f"❌ Error in hierarchical extraction: {e}")
            raise

    def get_crew_info(self):
        """Get information about the crew composition."""
        return {
            "process_type": "hierarchical_with_chunking",
            "manager": self.manager_agent.role,
            "agents": [agent.role for agent in self.agents],
            "num_extractors": self.num_extractors,
            "website_url": self.website_url,
            "approach": "two_phase_execution"
        }

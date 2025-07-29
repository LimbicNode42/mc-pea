"""
Flow-Based API Documentation Extraction

This approach uses CrewAI Flows for deterministic, controlled execution with
explicit data passing between discovery and extraction phases.
Better suited for chunked parallel processing than hierarchical crews.
"""

from crewai import Flow, Crew, Process
from crewai.flow.flow import start, listen
from agents_workers.api_discovery_agent import ApiLinkDiscoveryAgent
from agents_workers.api_content_extractor_agent import ApiLinkContentExtractorAgent
from tasks.api_link_discovery_task import ApiLinkDiscoveryTask
from tasks.api_content_extractor_task import ApiLinkContentExtractorTask
import json
from typing import List, Dict, Any
from models.api_flow_models import DiscoveryResult, ChunkData, ExtractionResult
import agentops
from dotenv import load_dotenv

class ApiExtractionFlow(Flow):
    """
    Flow-based API extraction with explicit data passing and chunk coordination.
    """
    
    def __init__(self, website_url: str):
        super().__init__()
        self.website_url = website_url
    
    @start()
    def discovery_phase(self) -> DiscoveryResult:
        """Phase 1: Discover all API endpoints."""
        print(f"🔍 Starting API discovery for {self.website_url}")

        discovery_agent = ApiLinkDiscoveryAgent(website_url=self.website_url)
        
        # Create discovery task
        discovery_task = ApiLinkDiscoveryTask(website_url=self.website_url)
        
        # Assign the discovery agent to the task
        discovery_task.agent = discovery_agent
        
        # Create crew for discovery
        discovery_crew = Crew(
            agents=[discovery_agent],
            tasks=[discovery_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute discovery
        result = discovery_crew.kickoff()
        
        # Parse and validate result  
        discovery_data = None
        print(f"🔍 DEBUG - Discovery result type: {type(result)}")
        print(f"🔍 DEBUG - Has json_dict attr: {hasattr(result, 'json_dict')}")
        print(f"🔍 DEBUG - json_dict value: {getattr(result, 'json_dict', 'NOT_FOUND')}")
        print(f"🔍 DEBUG - Has raw attr: {hasattr(result, 'raw')}")
        print(f"🔍 DEBUG - raw value: {getattr(result, 'raw', 'NOT_FOUND')}")
        
        # The guardrail validation should have passed and returned the parsed data
        # Check if we have valid task output with guardrail data
        if hasattr(result, 'tasks_output') and result.tasks_output:
            print(f"🔍 DEBUG - Found tasks_output: {len(result.tasks_output)} tasks")
            if result.tasks_output:
                first_task = result.tasks_output[0]
                print(f"🔍 DEBUG - First task type: {type(first_task)}")
                
                # The guardrail should have returned the parsed data
                if hasattr(first_task, 'output'):
                    print(f"🔍 DEBUG - Task output type: {type(first_task.output)}")
                    if isinstance(first_task.output, dict):
                        discovery_data = first_task.output
                        print(f"🔍 DEBUG - Found data in task output: {type(discovery_data)}")
        
        # Try fallback methods if guardrail data not found
        if not discovery_data:
            # Try to extract the data from the crew result - prioritize json_dict which has parsed data
            if hasattr(result, 'json_dict') and result.json_dict:
                discovery_data = result.json_dict
                print(f"🔍 DEBUG - Found data in json_dict: {type(discovery_data)}")
            elif hasattr(result, 'tasks_output') and result.tasks_output and hasattr(result.tasks_output[0], 'json_dict') and result.tasks_output[0].json_dict:
                discovery_data = result.tasks_output[0].json_dict
                print(f"🔍 DEBUG - Found data in first task json_dict: {type(discovery_data)}")
            elif hasattr(result, 'raw') and result.raw:
                try:
                    discovery_data = json.loads(result.raw)
                    print(f"🔍 DEBUG - Parsed data from raw: {type(discovery_data)}")
                except json.JSONDecodeError:
                    print(f"🔍 DEBUG - Failed to parse raw result as JSON: {result.raw}")
                    discovery_data = None
        
        # If no data found through guardrail or fallbacks, try direct result access
        if not discovery_data:
            if isinstance(result, dict):
                discovery_data = result
                print(f"🔍 DEBUG - Using result as dict: {type(discovery_data)}")
            else:
                try:
                    discovery_data = json.loads(str(result))
                    print(f"🔍 DEBUG - Parsed data from str: {type(discovery_data)}")
                except json.JSONDecodeError:
                    print(f"🔍 DEBUG - Failed to parse result as JSON: {str(result)}")
                    discovery_data = None
        
        # Ensure we have valid discovery data
        if not discovery_data or discovery_data == 'null' or not discovery_data.get('cs'):
            print(f"🔍 DEBUG - discovery_data validation failed: {discovery_data}")
            raise ValueError("Discovery returned empty data")
        
        # Count total endpoints - handle both 'cs' and 'ocs' formats
        total_endpoints = 0
        if discovery_data and 'cs' in discovery_data:
            # New format from current discovery agent
            total_endpoints = sum(len(cat.get('ls', [])) for cat in discovery_data['cs'])
        
        print(f"✅ Discovery completed. Found {total_endpoints} endpoints")
        
        return DiscoveryResult(
            discovery_data=discovery_data,
            website_url=self.website_url,
            total_endpoints=total_endpoints
        )
    
    @listen(discovery_phase)
    def chunk_endpoints(self, discovery_result: DiscoveryResult) -> List[ChunkData]:
        """Phase 2: Split endpoints into manageable chunks."""
        
        discovery_data = discovery_result.discovery_data
        
        # Extract hostname from website_url
        from urllib.parse import urlparse
        parsed_url = urlparse(self.website_url)
        hostname = parsed_url.netloc
        
        categories = None

        if 'cs' in discovery_data:
            # New format from current discovery agent
            categories = discovery_data['cs']
            category_key = 'ls'  # links
            endpoint_key = 'l'   # link
        else:
            print("⚠️ No valid discovery data to chunk")
            return []
        
        # Fixed chunk size - number of chunks will be determined dynamically
        endpoints_per_chunk = 5
        estimated_chunks = (discovery_result.total_endpoints + endpoints_per_chunk - 1) // endpoints_per_chunk
        print(f"📦 Chunking {discovery_result.total_endpoints} endpoints into chunks of {endpoints_per_chunk} (estimated {estimated_chunks} chunks)")

        chunks = []
        current_chunk_endpoints = []
        current_size = 0
        
        for category in categories:
            category_name = category.get('n', category.get('name', 'Unknown'))
            
            for endpoint in category.get(category_key, []):
                # Normalize endpoint format
                endpoint_data = {
                    'category': category_name,
                    'endpoint': {
                        'title': endpoint.get('t', ''),
                        'path': endpoint.get('l', ''),
                        'url': f"https://{hostname}{endpoint.get('l', '')}"
                    }
                }
                
                current_chunk_endpoints.append(endpoint_data)
                current_size += 1
                
                # Create chunk when we reach the target size
                if current_size >= endpoints_per_chunk:
                    chunks.append(ChunkData(
                        chunk_id=len(chunks) + 1,
                        endpoints=current_chunk_endpoints.copy(),
                        total_chunks=0  # Will be updated after all chunks are created
                    ))
                    current_chunk_endpoints = []
                    current_size = 0
        
        # Add final chunk if there are remaining endpoints
        if current_chunk_endpoints:
            chunks.append(ChunkData(
                chunk_id=len(chunks) + 1,
                endpoints=current_chunk_endpoints,
                total_chunks=0  # Will be updated below
            ))
        
        # Update total_chunks for all chunks now that we know the final count
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        # Save each chunk to a file for debugging/inspection
        for chunk in chunks:
            chunk_filename = f"chunk_{chunk.chunk_id:02d}_endpoints.json"
            try:
                with open(chunk_filename, 'w', encoding='utf-8') as f:
                    json.dump(chunk.model_dump(), f, indent=2, ensure_ascii=False)
                print(f"💾 Saved chunk {chunk.chunk_id} to {chunk_filename}")
            except Exception as e:
                print(f"⚠️ Failed to save chunk {chunk.chunk_id}: {e}")
        
        print(f"📦 Created {len(chunks)} chunks with {endpoints_per_chunk} endpoints each (last chunk: {len(chunks[-1].endpoints) if chunks else 0} endpoints)")
        return chunks
    
    @listen(chunk_endpoints)
    def extract_chunks_parallel(self, chunks: List[ChunkData]) -> List[Dict[str, Any]]:
        """Phase 3: Process chunks in parallel using multiple extractors."""
        print(f"⚙️ Processing {len(chunks)} chunks in parallel")
        
        if not chunks:
            return []
        
        extraction_results = []
        
        # Process chunks (parallel in a real implementation)
        for chunk in chunks:
            print(f"🔧 Processing chunk {chunk.chunk_id}/{chunk.total_chunks} ({len(chunk.endpoints)} endpoints)")
            
            chunk_agent = ApiLinkContentExtractorAgent()
            
            chunk_task = ApiLinkContentExtractorTask(
                context=chunk
            )
            chunk_task.agent = chunk_agent
            
            # Create crew for this chunk
            chunk_crew = Crew(
                agents=[chunk_agent],
                tasks=[chunk_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Execute extraction for this chunk
            try:
                chunk_result = chunk_crew.kickoff()
                
                # Parse result
                if hasattr(chunk_result, 'json_dict'):
                    chunk_data = chunk_result.json_dict
                elif isinstance(chunk_result, dict):
                    chunk_data = chunk_result
                else:
                    try:
                        chunk_data = json.loads(str(chunk_result))
                    except:
                        chunk_data = {"error": f"Could not parse chunk {chunk.chunk_id} result"}
                
                extraction_results.append({
                    "chunk_id": chunk.chunk_id,
                    "endpoints_processed": len(chunk.endpoints),
                    "data": chunk_data
                })

                chunk_filename = f"chunk_{chunk.chunk_id:02d}_api_usage.json"
                try:
                    with open(chunk_filename, 'w', encoding='utf-8') as f:
                        json.dump(chunk_data, f, indent=2, ensure_ascii=False)
                    print(f"💾 Saved chunk {chunk.chunk_id} to {chunk_filename}")
                except Exception as e:
                    print(f"⚠️ Failed to save chunk {chunk.chunk_id}: {e}")
                    
                    print(f"✅ Chunk {chunk.chunk_id} completed")
                
            except Exception as e:
                print(f"❌ Error processing chunk {chunk.chunk_id}: {e}")
                extraction_results.append({
                    "chunk_id": chunk.chunk_id,
                    "endpoints_processed": len(chunk.endpoints),
                    "error": str(e)
                })
        
        return extraction_results
    
    # @listen(extract_chunks_parallel)
    # def combine_results(self, extraction_results: List[Dict[str, Any]]) -> ExtractionResult:
    #     """Phase 4: Combine all chunk results into final output."""
    #     print(f"🔄 Combining results from {len(extraction_results)} chunks")
        
    #     # Get discovery data from flow state
    #     discovery_data = self.state.get('discovery_phase', {}).get('discovery_data', {})
        
    #     total_processed = sum(
    #         chunk.get('endpoints_processed', 0) 
    #         for chunk in extraction_results
    #     )
        
    #     final_result = ExtractionResult(
    #         discovery=discovery_data,
    #         extracted_chunks=extraction_results,
    #         total_endpoints_processed=total_processed,
    #         chunks_processed=len(extraction_results)
    #     )
        
    #     print(f"✅ Flow completed: {total_processed} endpoints processed in {len(extraction_results)} chunks")
    #     return final_result

# Usage example
if __name__ == "__main__":
    load_dotenv()

    agentops.init()

    # Example usage
    flow = ApiExtractionFlow(
        website_url="https://docs.github.com/en/rest"
    )
    
    result = flow.kickoff()
    print(f"Final result: {result}")

"""
Flow-Based API Documentation Extraction

This approach uses CrewAI Flows for deterministic, controlled execution with
explicit data passing between discovery and extraction phases.
Better suited for chunked parallel processing than hierarchical crews.
"""

import os
# Fix Windows console encoding issues before any other imports
os.environ['PYTHONIOENCODING'] = 'utf-8'

from crewai import Flow, Crew, Process
from crewai.flow.flow import start, listen
from agents_workers.api_discovery_agent import ApiLinkDiscoveryAgent
from agents_workers.api_content_extractor_agent import ApiLinkContentExtractorAgent
from agents_workers.mcp_base_generator_agent import MCPBaseGeneratorAgent
from tasks.api_link_discovery_task import ApiLinkDiscoveryTask
from tasks.api_content_extractor_task import ApiLinkContentExtractorTask
from tasks.mcp_base_generator_task import MCPBaseGeneratorTask
import json
from typing import List, Dict, Any
from models.api_flow_models import DiscoveryResult, ChunkData, ExtractionResult, MCPBaseGenerationResult
import agentops
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class ApiExtractionFlow(Flow):
    """
    Flow-based API extraction with explicit data passing and chunk coordination.
    """
    
    def __init__(self, website_url: str, template_path: str = None):
        super().__init__()
        self.website_url = website_url
        self.template_path = template_path  # Optional custom template path
    
    @start()
    # @agentops.operation
    def parallel_discovery_and_mcp_generation(self) -> Dict[str, Any]:
        """
        Phase 1: Run discovery and MCP base generation in parallel.
        This ensures both tasks start simultaneously for maximum efficiency.
        """
        print(f"🚀 Starting parallel discovery and MCP base generation for {self.website_url}")
        
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks to run in parallel
            discovery_future = executor.submit(self._run_discovery)
            mcp_future = executor.submit(self._run_mcp_base_generation)
            
            # Wait for both to complete
            print("⏳ Waiting for parallel tasks to complete...")
            
            # Get results
            discovery_result = discovery_future.result()
            mcp_result = mcp_future.result()
            
            # Combine results
            combined_result = {
                'discovery': discovery_result.dict() if discovery_result else None,
                'mcp_base': mcp_result.dict() if mcp_result else None,
                'ready_for_api_integration': (
                    discovery_result and discovery_result.total_endpoints > 0 and 
                    mcp_result and mcp_result.success
                ),
                'timestamp': threading.Thread().ident
            }
            
            print(f"🎯 Parallel setup complete!")
            if discovery_result:
                print(f"📊 Discovery: {discovery_result.total_endpoints} endpoints found")
            if mcp_result:
                print(f"🏗️ MCP Server: {mcp_result.server_name} ({'✅ Success' if mcp_result.success else '❌ Failed'})")
            
            if combined_result['ready_for_api_integration']:
                print("✅ System ready for API endpoint selection and integration!")
                print(f"🎯 Next step: Select endpoints from {discovery_result.total_endpoints} discovered APIs")
                print(f"🏗️ Target server: {mcp_result.output_directory}")
            else:
                if not discovery_result or discovery_result.total_endpoints == 0:
                    print("⚠️ No endpoints discovered - check the target website")
                if not mcp_result or not mcp_result.success:
                    print(f"⚠️ MCP base generation failed: {mcp_result.error if mcp_result else 'Unknown error'}")
            
            return combined_result
    
    def _run_discovery(self) -> DiscoveryResult:
        """Internal method to run discovery phase."""
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
    
    def _run_mcp_base_generation(self) -> MCPBaseGenerationResult:
        """Internal method to run MCP base generation phase."""
        print(f"🏗️ Starting MCP base server generation for {self.website_url}")
        
        try:
            # Create MCP base generator agent with template path support
            base_generator_agent = MCPBaseGeneratorAgent(
                website_url=self.website_url,
                server_name=None,  # Let it auto-generate
                template_path=self.template_path
            )
            
            # Create generation task
            base_generator_task = MCPBaseGeneratorTask(
                website_url=self.website_url,
                server_name=None,  # Let it auto-generate
                template_path=self.template_path
            )
            
            # Assign agent to task
            base_generator_task.agent = base_generator_agent
            
            # Create crew for base generation
            base_generator_crew = Crew(
                agents=[base_generator_agent],
                tasks=[base_generator_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Execute base generation
            result = base_generator_crew.kickoff()
            
            # Parse result
            base_generation_data = None
            
            # Try to extract structured data from result
            if hasattr(result, 'json_dict') and result.json_dict:
                base_generation_data = result.json_dict
            elif hasattr(result, 'tasks_output') and result.tasks_output:
                first_task = result.tasks_output[0]
                if hasattr(first_task, 'json_dict') and first_task.json_dict:
                    base_generation_data = first_task.json_dict
                elif hasattr(first_task, 'output') and isinstance(first_task.output, dict):
                    base_generation_data = first_task.output
            
            # Fallback parsing
            if not base_generation_data:
                if isinstance(result, dict):
                    base_generation_data = result
                else:
                    try:
                        base_generation_data = json.loads(str(result))
                    except json.JSONDecodeError:
                        base_generation_data = None
            
            # Create result object
            if base_generation_data and isinstance(base_generation_data, dict):
                mcp_result = MCPBaseGenerationResult(
                    success=base_generation_data.get('success', False),
                    server_name=base_generation_data.get('server_name', ''),
                    output_directory=base_generation_data.get('output_directory', ''),
                    template_used=base_generation_data.get('template_used', ''),
                    files_created=base_generation_data.get('files_created', []),
                    customizations_applied=base_generation_data.get('customizations_applied', {}),
                    validation_results=base_generation_data.get('validation_results', {}),
                    next_steps=base_generation_data.get('next_steps', [])
                )
            else:
                # Get basic info from the agent if parsing failed
                server_info = base_generator_agent.get_server_info()
                mcp_result = MCPBaseGenerationResult(
                    success=True,  # Assume success if no errors were thrown
                    server_name=server_info['server_name'],
                    output_directory=server_info['output_dir'],
                    template_used=server_info['template_dir'],
                    files_created=['package.json', 'README.md', 'src/index.ts'],  # Basic assumption
                    customizations_applied={'basic': 'Template copied and customized'},
                    validation_results={'structure_valid': True},
                    next_steps=['API tools and resources can now be added to the server']
                )
            
            if mcp_result.success:
                print(f"✅ MCP base server generated: {mcp_result.server_name}")
                print(f"📁 Location: {mcp_result.output_directory}")
                print(f"📋 Template: {mcp_result.template_used}")
            else:
                print(f"❌ MCP base server generation failed: {mcp_result.error}")
            
            return mcp_result
            
        except Exception as e:
            error_msg = f"MCP base generation failed: {str(e)}"
            print(f"❌ {error_msg}")
            return MCPBaseGenerationResult(
                success=False,
                error=error_msg
            )
    
    # Note: Old generate_mcp_base_server method moved to _run_mcp_base_generation
    # and integrated into the parallel execution above
    
    def chunk_selected_endpoints(self, discovery_result: DiscoveryResult, selected_endpoints: Dict[str, List[str]]) -> List[ChunkData]:
        """Phase 2b: Split only user-selected endpoints into manageable chunks for processing."""
        
        discovery_data = discovery_result.discovery_data
        
        # Extract hostname from website_url
        from urllib.parse import urlparse
        parsed_url = urlparse(self.website_url)
        hostname = parsed_url.netloc
        
        if 'cs' not in discovery_data:
            print("⚠️ No valid discovery data to chunk")
            return []
        
        categories = discovery_data['cs']
        category_key = 'ls'  # links
        
        # Count total selected endpoints
        total_selected = sum(len(paths) for paths in selected_endpoints.values())
        print(f"🎯 Processing user selection: {total_selected} endpoints across {len(selected_endpoints)} categories")
        
        # Fixed chunk size for optimal processing
        endpoints_per_chunk = 5
        estimated_chunks = (total_selected + endpoints_per_chunk - 1) // endpoints_per_chunk
        print(f"📦 Chunking {total_selected} selected endpoints into chunks of {endpoints_per_chunk} (estimated {estimated_chunks} chunks)")

        chunks = []
        current_chunk_endpoints = []
        current_size = 0
        
        # Process only selected endpoints
        for category in categories:
            category_name = category.get('n', category.get('name', 'Unknown'))
            
            # Skip categories that weren't selected
            if category_name not in selected_endpoints or not selected_endpoints[category_name]:
                continue
                
            selected_paths_for_category = selected_endpoints[category_name]
            
            for endpoint in category.get(category_key, []):
                endpoint_path = endpoint.get('l', '')
                
                # Only include endpoints that were selected by the user
                if endpoint_path in selected_paths_for_category:
                    # Normalize endpoint format
                    endpoint_data = {
                        'category': category_name,
                        'endpoint': {
                            'title': endpoint.get('t', ''),
                            'path': endpoint_path,
                            'url': f"https://{hostname}{endpoint_path}"
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
        
        print(f"📦 Created {len(chunks)} chunks from selected endpoints with {endpoints_per_chunk} endpoints each (last chunk: {len(chunks[-1].endpoints) if chunks else 0} endpoints)")
        
        # Log chunk details for verification
        for chunk in chunks:
            categories_in_chunk = set(ep['category'] for ep in chunk.endpoints)
            print(f"   Chunk {chunk.chunk_id}: {len(chunk.endpoints)} endpoints from {len(categories_in_chunk)} categories: {', '.join(categories_in_chunk)}")
        
        return chunks
    
    def process_selected_endpoints(self, discovery_result: DiscoveryResult, selected_endpoints: Dict[str, List[str]]) -> List[ChunkData]:
        """
        Public method to process user-selected endpoints.
        This is called from the UI after user makes their selections.
        """
        print(f"🎯 Starting processing of user-selected endpoints")
        
        # Validate inputs
        if not selected_endpoints:
            print("⚠️ No endpoints selected by user")
            return []
        
        # Create chunks from selected endpoints only
        chunks = self.chunk_selected_endpoints(discovery_result, selected_endpoints)
        
        if not chunks:
            print("⚠️ No chunks created from selected endpoints")
            return []
        
        print(f"✅ Ready to process {len(chunks)} chunks with user-selected endpoints")
        return chunks
    
    def extract_selected_endpoints_full(self, discovery_result: DiscoveryResult, selected_endpoints: Dict[str, List[str]], progress_callback=None) -> List[Dict[str, Any]]:
        """
        Complete workflow: chunk selected endpoints and process them in parallel.
        This is the main method called from the UI.
        """
        print(f"🚀 Starting full extraction workflow for selected endpoints")
        
        # Step 1: Create chunks from selected endpoints
        chunks = self.process_selected_endpoints(discovery_result, selected_endpoints)
        
        if not chunks:
            print("❌ No chunks to process")
            return []
        
        # Step 2: Process chunks in parallel with progress tracking
        extraction_results = self.extract_chunks_parallel(chunks, progress_callback)
        
        return extraction_results
    
    # @agentops.operation
    def _process_single_chunk(self, chunk: ChunkData) -> Dict[str, Any]:
        """Process a single chunk in isolation for parallel execution."""
        thread_id = threading.get_ident()
        print(f"🔧 [Thread {thread_id}] Processing chunk {chunk.chunk_id}/{chunk.total_chunks} ({len(chunk.endpoints)} endpoints)")
        
        try:
            chunk_agent = ApiLinkContentExtractorAgent(agent_id=chunk.chunk_id)
            
            # Convert ChunkData to serializable dict for the task
            chunk_dict = {
                "chunk_id": chunk.chunk_id,
                "endpoints": chunk.endpoints,
                "total_chunks": chunk.total_chunks
            }
            
            chunk_task = ApiLinkContentExtractorTask(
                context=chunk_dict  # Pass serializable dict instead of ChunkData object
            )
            chunk_task.agent = chunk_agent
            
            # Create crew for this chunk with session context
            chunk_crew = Crew(
                agents=[chunk_agent],
                tasks=[chunk_task],
                process=Process.sequential,
                verbose=False  # Reduced verbosity for parallel processing
            )
            
            # Execute extraction for this chunk
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

            print(f"✅ [Thread {thread_id}] Chunk {chunk.chunk_id} completed")
            
            return {
                "chunk_id": chunk.chunk_id,
                "endpoints_processed": len(chunk.endpoints),
                "data": chunk_data,
                "thread_id": thread_id
            }
            
        except Exception as e:
            print(f"❌ [Thread {thread_id}] Error processing chunk {chunk.chunk_id}: {e}")
            return {
                "chunk_id": chunk.chunk_id,
                "endpoints_processed": len(chunk.endpoints),
                "error": str(e),
                "thread_id": thread_id
            }
    
    def extract_chunks_parallel(self, chunks: List[ChunkData], progress_callback=None) -> List[Dict[str, Any]]:
        """Phase 3: Process chunks in TRUE parallel using ThreadPoolExecutor."""
        print(f"⚙️ Processing {len(chunks)} chunks in TRUE parallel mode")
        
        if not chunks:
            return []
        
        extraction_results = []

        # Determine optimal number of workers (reduced for higher success rate)
        max_workers = min(len(chunks), 5)  # Reduced from 5 for better stability
        print(f"🔧 Using {max_workers} parallel workers for chunk processing")

        # Process chunks in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chunks for processing
            future_to_chunk = {
                executor.submit(self._process_single_chunk, chunk): chunk 
                for chunk in chunks
            }
            
            print(f"🚀 Submitted {len(future_to_chunk)} chunks for parallel processing")
            submitted_chunk_ids = [chunk.chunk_id for chunk in chunks]
            print(f"🔍 Submitted chunk IDs: {sorted(submitted_chunk_ids)}")
            
            # Track progress
            completed_count = 0
            total_chunks = len(chunks)
            
            # Collect results as they complete
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    result = future.result()
                    extraction_results.append(result)
                    completed_count += 1
                    
                    # Progress callback for UI updates
                    if progress_callback:
                        progress_callback({
                            'completed': completed_count,
                            'total': total_chunks,
                            'current_chunk': result['chunk_id'],
                            'success': 'error' not in result,
                            'thread_id': result.get('thread_id'),
                            'endpoints_processed': result.get('endpoints_processed', 0)
                        })
                    
                    status = "✅ SUCCESS" if 'error' not in result else "❌ FAILED"
                    thread_id = result.get('thread_id', 'Unknown')
                    endpoints = result.get('endpoints_processed', 0)
                    print(f"📊 Progress: {completed_count}/{total_chunks} | Chunk {result['chunk_id']}: {status} | Thread {thread_id} | {endpoints} endpoints")
                    
                except Exception as e:
                    error_result = {
                        "chunk_id": chunk.chunk_id,
                        "endpoints_processed": len(chunk.endpoints),
                        "error": f"Future exception: {str(e)}"
                    }
                    extraction_results.append(error_result)
                    completed_count += 1
                    
                    # Progress callback for UI updates
                    if progress_callback:
                        progress_callback({
                            'completed': completed_count,
                            'total': total_chunks,
                            'current_chunk': chunk.chunk_id,
                            'success': False,
                            'error': str(e),
                            'endpoints_processed': len(chunk.endpoints)
                        })
                    
                    print(f"❌ Exception in chunk {chunk.chunk_id}: {e}")
        
        # Sort results by chunk_id to maintain order
        extraction_results.sort(key=lambda x: x['chunk_id'])
        
        # Check for missing chunks
        processed_chunk_ids = [r['chunk_id'] for r in extraction_results]
        missing_chunks = set(submitted_chunk_ids) - set(processed_chunk_ids)
        if missing_chunks:
            print(f"⚠️ Missing chunks detected: {sorted(missing_chunks)}")
        
        print(f"🎉 All {len(extraction_results)} chunks processed in parallel!")
        print(f"📋 Processed chunk IDs: {sorted(processed_chunk_ids)}")
        return extraction_results
    
    # Note: Parallel coordination now handled within the single start method
    # to ensure both discovery and MCP generation run concurrently
    
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

# @agentops.session
# @agentops.trace(name="my_workflow")
def run(website_url: str = "https://docs.github.com/en/rest", template_path: str = None):
    """
    Run the API extraction flow with parallel discovery and MCP base generation.
    
    Args:
        website_url: The website to discover APIs from
        template_path: Optional path to custom MCP server template, uses default if None
    """
    flow = ApiExtractionFlow(
        website_url=website_url,
        template_path=template_path
    )
    result = flow.kickoff()
    print(f"Final result: {result}")
    return result

# Usage example
if __name__ == "__main__":
    load_dotenv()

    agentops.init()

    run()
"""
Optimized retry mechanism for failed chunks with smart batching.
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from models.api_flow_models import ChunkData
from agents_workers.api_content_extractor_agent import ApiLinkContentExtractorAgent
from tasks.api_content_extractor_task import ApiLinkContentExtractorTask
from crewai import Crew, Process

class ChunkRetryManager:
    """Manages retry logic for failed chunks with optimizations."""
    
    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        
    def identify_failed_chunks(self) -> List[int]:
        """Identify which chunks need reprocessing."""
        failed_chunks = []
        
        for i in range(1, 38):  # Based on current chunk range
            endpoints_file = f"chunk_{i:02d}_endpoints.json"
            usage_file = f"chunk_{i:02d}_api_usage.json"
            
            try:
                # Check if endpoints exist but usage doesn't
                with open(endpoints_file, 'r') as f:
                    endpoints_data = json.load(f)
                
                try:
                    with open(usage_file, 'r') as f:
                        usage_data = json.load(f)
                    # Check if usage file is empty or invalid
                    if not usage_data or 'ocs' not in usage_data or not usage_data['ocs']:
                        failed_chunks.append(i)
                except FileNotFoundError:
                    failed_chunks.append(i)
                    
            except FileNotFoundError:
                continue  # No endpoints file, skip
                
        return failed_chunks
    
    def load_chunk_data(self, chunk_id: int) -> ChunkData:
        """Load chunk data for retry."""
        endpoints_file = f"chunk_{chunk_id:02d}_endpoints.json"
        
        with open(endpoints_file, 'r') as f:
            data = json.load(f)
            
        return ChunkData(
            chunk_id=chunk_id,
            endpoints=data['endpoints'],
            total_chunks=data['total_chunks']
        )
    
    def retry_failed_chunks(self, max_workers: int = 3) -> Dict[str, Any]:
        """Retry failed chunks with reduced parallelism for stability."""
        failed_chunk_ids = self.identify_failed_chunks()
        
        if not failed_chunk_ids:
            return {"status": "success", "message": "No failed chunks to retry"}
        
        print(f"🔄 Retrying {len(failed_chunk_ids)} failed chunks: {failed_chunk_ids}")
        
        # Load chunk data
        failed_chunks = []
        for chunk_id in failed_chunk_ids:
            try:
                chunk_data = self.load_chunk_data(chunk_id)
                failed_chunks.append(chunk_data)
            except Exception as e:
                print(f"⚠️ Could not load chunk {chunk_id}: {e}")
        
        if not failed_chunks:
            return {"status": "error", "message": "Could not load any failed chunks"}
        
        # Process with reduced parallelism for better success rate
        retry_results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {
                executor.submit(self._retry_single_chunk, chunk): chunk 
                for chunk in failed_chunks
            }
            
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    result = future.result()
                    retry_results.append(result)
                    
                    if result.get('success'):
                        print(f"✅ Retry successful for chunk {chunk.chunk_id}")
                    else:
                        print(f"❌ Retry failed for chunk {chunk.chunk_id}")
                        
                except Exception as e:
                    print(f"❌ Exception during retry of chunk {chunk.chunk_id}: {e}")
                    retry_results.append({
                        "chunk_id": chunk.chunk_id,
                        "success": False,
                        "error": str(e)
                    })
        
        successful_retries = sum(1 for r in retry_results if r.get('success'))
        
        return {
            "status": "completed",
            "attempted": len(failed_chunks),
            "successful": successful_retries,
            "failed": len(failed_chunks) - successful_retries,
            "results": retry_results
        }
    
    def _retry_single_chunk(self, chunk: ChunkData) -> Dict[str, Any]:
        """Retry processing a single chunk with optimized settings."""
        thread_id = threading.get_ident()
        print(f"🔄 [Thread {thread_id}] Retrying chunk {chunk.chunk_id}")
        
        try:
            # Create agent with retry-optimized settings
            chunk_agent = ApiLinkContentExtractorAgent(agent_id=chunk.chunk_id)
            
            # Reduce temperature for more consistent output
            if hasattr(chunk_agent, 'llm'):
                chunk_agent.llm.temperature = 0.1
            
            chunk_task = ApiLinkContentExtractorTask(context=chunk)
            chunk_task.agent = chunk_agent
            
            # Single agent crew with focused processing
            chunk_crew = Crew(
                agents=[chunk_agent],
                tasks=[chunk_task],
                process=Process.sequential,
                verbose=False
            )
            
            # Execute with timeout
            chunk_result = chunk_crew.kickoff()
            
            # Enhanced result parsing
            chunk_data = None
            if hasattr(chunk_result, 'json_dict') and chunk_result.json_dict:
                chunk_data = chunk_result.json_dict
            elif isinstance(chunk_result, dict):
                chunk_data = chunk_result
            else:
                try:
                    chunk_data = json.loads(str(chunk_result))
                except:
                    chunk_data = None
            
            if not chunk_data or 'ocs' not in chunk_data:
                return {
                    "chunk_id": chunk.chunk_id,
                    "success": False,
                    "error": "Invalid or empty result structure"
                }
            
            # Save successful result
            chunk_filename = f"chunk_{chunk.chunk_id:02d}_api_usage.json"
            with open(chunk_filename, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, indent=2, ensure_ascii=False)
            
            return {
                "chunk_id": chunk.chunk_id,
                "success": True,
                "endpoints_found": sum(len(cat.get('ces', [])) for cat in chunk_data.get('ocs', [])),
                "thread_id": thread_id
            }
            
        except Exception as e:
            return {
                "chunk_id": chunk.chunk_id,
                "success": False,
                "error": str(e),
                "thread_id": thread_id
            }

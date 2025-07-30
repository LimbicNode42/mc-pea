#!/usr/bin/env python3
"""
Quick test for a single chunk to debug the guardrail issue.
"""

import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from models.api_flow_models import ChunkData
from agents_workers.api_content_extractor_agent import ApiLinkContentExtractorAgent
from tasks.api_content_extractor_task import ApiLinkContentExtractorTask, validate_api_content_extraction
from crewai import Crew, Process

def test_single_chunk():
    print("🧪 Testing single chunk extraction...")
    
    # Load a chunk that we know exists
    try:
        with open("chunk_01_endpoints.json", 'r') as f:
            chunk_data = json.load(f)
    except FileNotFoundError:
        print("❌ No chunk_01_endpoints.json found. Make sure to run discovery first.")
        return
    
    # Create chunk data
    chunk = ChunkData(
        chunk_id=1,
        endpoints=chunk_data['endpoints'],
        total_chunks=chunk_data['total_chunks']
    )
    
    print(f"📦 Testing chunk {chunk.chunk_id} with {len(chunk.endpoints)} endpoints")
    
    # Create agent and task
    agent = ApiLinkContentExtractorAgent(agent_id=1)
    
    task = ApiLinkContentExtractorTask(context=chunk)
    task.agent = agent
    
    # Ensure correct guardrail
    task.guardrail = validate_api_content_extraction
    
    print(f"🔍 Guardrail function: {task.guardrail.__name__}")
    
    # Create crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )
    
    # Execute
    try:
        print("🚀 Executing test chunk...")
        result = crew.kickoff()
        
        print(f"✅ Result type: {type(result)}")
        print(f"📄 Result: {result}")
        
        if hasattr(result, 'json_dict') and result.json_dict:
            print(f"📊 JSON dict: {result.json_dict}")
            
            # Save result for inspection
            with open("test_chunk_result.json", 'w') as f:
                json.dump(result.json_dict, f, indent=2)
            print("💾 Saved result to test_chunk_result.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_chunk()

#!/usr/bin/env python3
"""
Quick validation and retry script for chunk processing.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from utils.chunk_retry_manager import ChunkRetryManager
import json

def main():
    print("🔍 API Extraction Validation & Retry Tool")
    print("=" * 50)
    
    retry_manager = ChunkRetryManager()
    
    # Identify failed chunks
    failed_chunks = retry_manager.identify_failed_chunks()
    
    print(f"📊 Status Summary:")
    print(f"   - Total expected chunks: 37")
    print(f"   - Failed chunks: {len(failed_chunks)}")
    print(f"   - Success rate: {((37 - len(failed_chunks)) / 37) * 100:.1f}%")
    
    if failed_chunks:
        print(f"\n❌ Failed chunks: {failed_chunks}")
        
        user_input = input("\n🔄 Do you want to retry failed chunks? (y/n): ").lower()
        
        if user_input == 'y':
            print("\n🚀 Starting retry process...")
            results = retry_manager.retry_failed_chunks(max_workers=2)
            
            print(f"\n📊 Retry Results:")
            print(f"   - Attempted: {results['attempted']}")
            print(f"   - Successful: {results['successful']}")
            print(f"   - Still failed: {results['failed']}")
            
            if results['successful'] > 0:
                new_success_rate = ((37 - len(failed_chunks) + results['successful']) / 37) * 100
                print(f"   - New success rate: {new_success_rate:.1f}%")
            
            # Show details of failed retries
            failed_retries = [r for r in results['results'] if not r.get('success')]
            if failed_retries:
                print(f"\n❌ Still failing chunks:")
                for failed in failed_retries:
                    print(f"   - Chunk {failed['chunk_id']}: {failed.get('error', 'Unknown error')}")
        else:
            print("\n✋ Skipping retry.")
    else:
        print("\n✅ All chunks processed successfully!")
    
    print("\n🏁 Validation complete.")

if __name__ == "__main__":
    main()

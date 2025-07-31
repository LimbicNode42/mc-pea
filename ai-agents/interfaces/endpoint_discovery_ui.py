"""
Simple Endpoint Discovery Interface

A fresh Streamlit interface that:
1. Takes a URL input
2. Shows progress of discovery flow
3. Presents discovered endpoints grouped by category
4. Allows user to select which endpoints they want to extract
"""

import streamlit as st
import os
import sys
from urllib.parse import urlparse
import json
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the parent directory to the path so we can import from the ai-agents module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_extraction_flow import ApiExtractionFlow
from models.api_flow_models import DiscoveryResult, ChunkData


def main():
    st.set_page_config(
        page_title="API Endpoint Discovery",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 API Endpoint Discovery & Selection")
    st.markdown("Discover API endpoints and select which ones you want to extract usage examples for.")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        st.markdown("### Environment Setup")
        
        # Check for required environment variables
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Option to input API key manually if not found in environment
        if not anthropic_key:
            st.warning("⚠️ Anthropic API Key not found in environment")
            anthropic_key = st.text_input(
                "Enter Anthropic API Key:", 
                type="password",
                help="Your Anthropic API key for Claude access"
            )
            if anthropic_key:
                # Set the environment variable for this session
                os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                st.success("✅ API Key set for this session")
        else:
            st.success("✅ Anthropic API Key found in environment")
            
        # Show current status
        if anthropic_key:
            st.markdown("**Status:** Ready to discover endpoints")
        else:
            st.markdown("**Status:** API Key required")
    
    # Main input section
    st.header("📡 API Documentation URL")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        url_input = st.text_input(
            "Enter the API documentation URL",
            value="https://docs.github.com/en/rest",
            placeholder="https://api.example.com/docs"
        )
    
    with col2:
        discover_button = st.button("🚀 Discover Endpoints", type="primary")
    
    # URL validation
    if url_input:
        try:
            parsed = urlparse(url_input)
            if not parsed.scheme or not parsed.netloc:
                st.error("Please enter a valid URL with http:// or https://")
        except Exception as e:
            st.error(f"Invalid URL: {e}")
    
    # Discovery process
    if discover_button and url_input:
        # Get the current API key (either from env or manual input)
        current_anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not current_anthropic_key:
            st.error("❌ Cannot proceed without Anthropic API Key")
            st.info("💡 Please set your API key in the sidebar or as an environment variable")
            return
            
        try:
            # Initialize agentops if not already done
            import agentops
            if not hasattr(agentops, '_initialized'):
                agentops.init()
                agentops._initialized = True
            
            # Create the flow
            flow = ApiExtractionFlow(website_url=url_input)
            
            # Progress tracking
            progress_container = st.container()
            
            with progress_container:
                st.header("📊 Discovery Progress")
                
                # Phase 1: Discovery
                with st.status("🔍 Phase 1: Discovering API endpoints...", expanded=True) as status:
                    st.write("Analyzing the API documentation website...")
                    st.write("Using AI agents to find all available endpoints...")
                    
                    # Run discovery phase directly (not through flow.kickoff())
                    discovery_result = flow.discovery_phase()
                    
                    st.write(f"✅ Found {discovery_result.total_endpoints} endpoints")
                    status.update(label="✅ Phase 1: Discovery Complete", state="complete")
                
                # Phase 2: Chunking
                with st.status("📦 Phase 2: Organizing endpoints...", expanded=True) as status:
                    st.write("Grouping endpoints by category...")
                    st.write("Creating manageable chunks for processing...")
                    
                    # Run chunking phase directly
                    chunks = flow.chunk_endpoints(discovery_result)
                    
                    st.write(f"✅ Organized into {len(chunks)} chunks")
                    status.update(label="✅ Phase 2: Organization Complete", state="complete")
            
            # Store results in session state for user selection
            st.session_state.discovery_result = discovery_result
            st.session_state.chunks = chunks
            st.session_state.url = url_input
            
            st.success(f"🎉 Discovery complete! Found {discovery_result.total_endpoints} endpoints in {len(chunks)} categories.")
            
        except Exception as e:
            st.error(f"Discovery failed: {str(e)}")
            st.exception(e)
    
    # Display results if available
    if hasattr(st.session_state, 'discovery_result') and hasattr(st.session_state, 'chunks'):
        display_endpoint_selection()


def display_endpoint_selection():
    """Display the discovered endpoints grouped by category with selection checkboxes."""
    
    st.header("🎯 Select Endpoints for Extraction")
    st.markdown("Choose which endpoints you want to extract API usage examples for:")
    
    discovery_result = st.session_state.discovery_result
    chunks = st.session_state.chunks
    
    # Initialize selection state
    if 'selected_endpoints' not in st.session_state:
        st.session_state.selected_endpoints = {}
    
    # Group endpoints by category for display
    categories = {}
    for chunk in chunks:
        for endpoint in chunk.endpoints:
            category = endpoint['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(endpoint)
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Categories", len(categories))
    with col2:
        st.metric("Total Endpoints", discovery_result.total_endpoints)
    with col3:
        selected_count = sum(len(endpoints) for endpoints in st.session_state.selected_endpoints.values())
        st.metric("Selected Endpoints", selected_count)
    
    # Selection controls
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("✅ Select All"):
            st.session_state.selected_endpoints = {cat: [ep['endpoint']['path'] for ep in endpoints] 
                                                 for cat, endpoints in categories.items()}
            st.rerun()
    
    with col2:
        if st.button("❌ Clear All"):
            st.session_state.selected_endpoints = {}
            st.rerun()
    
    # Category-wise endpoint display
    for category, endpoints in categories.items():
        with st.expander(f"📁 {category} ({len(endpoints)} endpoints)", expanded=False):
            
            # Category controls
            col1, col2 = st.columns([1, 3])
            with col1:
                category_key = f"select_all_{category}"
                if st.button(f"Select All in {category}", key=category_key):
                    if category not in st.session_state.selected_endpoints:
                        st.session_state.selected_endpoints[category] = []
                    st.session_state.selected_endpoints[category] = [ep['endpoint']['path'] for ep in endpoints]
                    st.rerun()
            
            # Initialize category in selection state
            if category not in st.session_state.selected_endpoints:
                st.session_state.selected_endpoints[category] = []
            
            # Display endpoints with checkboxes
            for i, endpoint in enumerate(endpoints):
                endpoint_path = endpoint['endpoint']['path']
                endpoint_title = endpoint['endpoint']['title']
                endpoint_url = endpoint['endpoint']['url']
                category_name = endpoint['category']
                
                # Create display name with category prefix
                display_name = f"{category_name} > {endpoint_title}"
                
                # Checkbox for this endpoint
                checkbox_key = f"{category}_{i}_{endpoint_path}"
                is_selected = endpoint_path in st.session_state.selected_endpoints[category]
                
                if st.checkbox(
                    f"**{display_name}**",
                    value=is_selected,
                    key=checkbox_key,
                    help=f"URL: {endpoint_url}"
                ):
                    if endpoint_path not in st.session_state.selected_endpoints[category]:
                        st.session_state.selected_endpoints[category].append(endpoint_path)
                else:
                    if endpoint_path in st.session_state.selected_endpoints[category]:
                        st.session_state.selected_endpoints[category].remove(endpoint_path)
                
                # Display endpoint details - only show URL, not path
                with st.container():
                    st.markdown(f"**URL:** {endpoint_url}")
                    st.markdown("---")
    
    # Summary and next steps
    if st.session_state.selected_endpoints:
        st.header("📋 Selection Summary")
        
        total_selected = sum(len(endpoints) for endpoints in st.session_state.selected_endpoints.values())
        
        if total_selected > 0:
            st.success(f"You have selected {total_selected} endpoints across {len([cat for cat, eps in st.session_state.selected_endpoints.items() if eps])} categories.")
            
            # Show selected endpoints by category with remove buttons
            for category, selected_paths in st.session_state.selected_endpoints.items():
                if selected_paths:
                    # Category header with remove all button
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{category}:** {len(selected_paths)} endpoints")
                    with col2:
                        remove_category_key = f"remove_category_{category}"
                        if st.button("🗑️ All", key=remove_category_key, help=f"Remove all {category} endpoints"):
                            st.session_state.selected_endpoints[category] = []
                            st.rerun()
                    
                    # Find the endpoints in chunks to get title and URL
                    for chunk in st.session_state.chunks:
                        for endpoint in chunk.endpoints:
                            if (endpoint['category'] == category and 
                                endpoint['endpoint']['path'] in selected_paths):
                                title = endpoint['endpoint']['title']
                                url = endpoint['endpoint']['url']
                                path = endpoint['endpoint']['path']
                                
                                # Create a row with endpoint info and remove button
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(f"  - **{title}** - {url}")
                                with col2:
                                    remove_key = f"remove_{category}_{path}"
                                    if st.button("🗑️", key=remove_key, help=f"Remove {title}"):
                                        # Remove this endpoint from selection
                                        if path in st.session_state.selected_endpoints[category]:
                                            st.session_state.selected_endpoints[category].remove(path)
                                        # Clean up empty categories
                                        if not st.session_state.selected_endpoints[category]:
                                            st.session_state.selected_endpoints[category] = []
                                        st.rerun()
            
            # Next steps
            st.header("🚀 Next Steps")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Save Selection", type="primary"):
                    save_selection()
            
            with col2:
                if st.button("🔄 Extract API Usage", type="secondary", disabled=True):
                    st.info("API usage extraction will be implemented in the next phase")


def save_selection():
    """Save the current endpoint selection to a file."""
    try:
        # Build detailed selection data with titles and URLs
        detailed_selection = {}
        for category, selected_paths in st.session_state.selected_endpoints.items():
            if selected_paths:
                detailed_selection[category] = []
                
                # Find the endpoints in chunks to get full details
                for chunk in st.session_state.chunks:
                    for endpoint in chunk.endpoints:
                        if (endpoint['category'] == category and 
                            endpoint['endpoint']['path'] in selected_paths):
                            detailed_selection[category].append({
                                'title': endpoint['endpoint']['title'],
                                'path': endpoint['endpoint']['path'],
                                'url': endpoint['endpoint']['url']
                            })
        
        selection_data = {
            "url": st.session_state.url,
            "discovery_timestamp": st.session_state.discovery_result.__dict__,
            "selected_endpoints": detailed_selection,
            "selected_paths_only": st.session_state.selected_endpoints,  # Keep for backward compatibility
            "total_selected": sum(len(endpoints) for endpoints in st.session_state.selected_endpoints.values())
        }
        
        # Create filename based on URL
        parsed_url = urlparse(st.session_state.url)
        hostname = parsed_url.netloc.replace('.', '_')
        filename = f"endpoint_selection_{hostname}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(selection_data, f, indent=2, ensure_ascii=False, default=str)
        
        st.success(f"✅ Selection saved to {filename}")
        
    except Exception as e:
        st.error(f"Failed to save selection: {e}")


if __name__ == "__main__":
    main()

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
    
    # Template configuration section (moved outside sidebar for global access)
    st.markdown("---")
    st.markdown("### 🏗️ MCP Server Template Configuration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        template_option = st.radio(
            "Choose template source:",
            ["Default MC-PEA Template", "Custom Template Path"],
            help="Use the default MC-PEA template or specify your own custom template",
            horizontal=True
        )
    
    template_path = None
    if template_option == "Custom Template Path":
        template_path = st.text_input(
            "Template directory path:",
            placeholder="/path/to/your/mcp-server-template",
            help="Absolute or relative path to your custom MCP server template directory"
        )
        
        if template_path:
            # Validate template path
            if os.path.exists(template_path):
                # Check if it looks like a valid template
                required_files = ['package.json', 'tsconfig.json']
                has_required = any(
                    os.path.exists(os.path.join(template_path, f)) 
                    for f in required_files
                )
                
                if has_required:
                    st.success(f"✅ Custom template validated: {template_path}")
                else:
                    st.warning("⚠️ Template path exists but missing expected files (package.json, tsconfig.json)")
            else:
                st.error(f"❌ Template path does not exist: {template_path}")
    else:
        # Check if default template exists for info display
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(current_dir)
        default_template = os.path.join(project_root, 'templates', 'mcp-server-template')
        if os.path.exists(default_template):
            st.success("✅ Default MC-PEA template available")
        else:
            st.info("ℹ️ Using default template (will be resolved at runtime)")
    
    # Store template_path in session state for use in other functions
    st.session_state.template_path = template_path
            
    # Main content
    st.markdown("---")
    st.markdown("### 🌐 Website URL Input")
    
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
            
            # Create the flow with template path support
            flow = ApiExtractionFlow(
                website_url=url_input,
                template_path=getattr(st.session_state, 'template_path', None)
            )
            
            # Progress tracking
            progress_container = st.container()
            
            with progress_container:
                st.header("📊 Discovery Progress")
                
                # Phase 1: Parallel Discovery and MCP Generation
                with st.status("� Phase 1: Discovery & MCP Server Generation (Parallel)...", expanded=True) as status:
                    st.write("🔍 **Discovery Task:** Analyzing the API documentation website...")
                    st.write("🏗️ **MCP Generation Task:** Creating base MCP server structure...")
                    st.write("⚡ Both tasks running in parallel for optimal efficiency!")
                    
                    # Create detailed progress display
                    progress_display = st.empty()
                    
                    with progress_display.container():
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.info("🔍 **Discovery Agent Active**")
                            st.write("**Current Task:** Scanning documentation")
                            st.write("**Processing Steps:**")
                            st.write("  1. 🌐 Fetching main documentation page")
                            st.write("  2. 🔍 Analyzing page structure")
                            st.write("  3. 📝 Extracting endpoint information")
                            st.write("  4. 📂 Categorizing discovered endpoints")
                            st.write("  5. ✅ Compiling final endpoint list")
                        
                        with col2:
                            st.info("🏗️ **MCP Generator Agent Active**")
                            st.write("**Current Task:** Building MCP server base")
                            st.write("**Processing Steps:**")
                            st.write("  1. 📁 Copying template structure")
                            st.write("  2. ⚙️ Customizing package.json")
                            st.write("  3. 📝 Updating README.md")
                            st.write("  4. 🔧 Configuring TypeScript files")
                            st.write("  5. ✅ Validating server structure")
                    
                    # Run the new parallel method
                    parallel_result = flow.parallel_discovery_and_mcp_generation()
                    
                    # Extract results
                    discovery_data = parallel_result.get('discovery')
                    mcp_data = parallel_result.get('mcp_base')
                    
                    if discovery_data:
                        discovery_result = DiscoveryResult(**discovery_data)
                    else:
                        discovery_result = None
                    
                    # Update with results
                    with progress_display.container():
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if discovery_result:
                                st.success("🎉 **Discovery Agent Completed!**")
                                st.write(f"**Final Results:**")
                                st.write(f"  • Total endpoints: {discovery_result.total_endpoints}")
                                
                                # Show category breakdown
                                if 'cs' in discovery_result.discovery_data:
                                    categories = discovery_result.discovery_data['cs']
                                    st.write(f"  • Categories: {len(categories)}")
                                    for cat in categories[:3]:
                                        cat_name = cat.get('n', cat.get('name', 'Unknown'))
                                        endpoint_count = len(cat.get('ls', []))
                                        st.write(f"    - {cat_name}: {endpoint_count} endpoints")
                                    if len(categories) > 3:
                                        st.write(f"    - ... and {len(categories) - 3} more")
                            else:
                                st.error("❌ **Discovery Failed**")
                        
                        with col2:
                            if mcp_data and mcp_data.get('success'):
                                st.success("🎉 **MCP Server Generated!**")
                                st.write(f"**Server Details:**")
                                st.write(f"  • Server name: {mcp_data.get('server_name', 'Unknown')}")
                                st.write(f"  • Template used: {mcp_data.get('template_used', 'Default')}")
                                st.write(f"  • Files created: {len(mcp_data.get('files_created', []))}")
                                st.write(f"  • Location: {mcp_data.get('output_directory', 'Unknown')}")
                            else:
                                st.error("❌ **MCP Generation Failed**")
                                if mcp_data and mcp_data.get('error'):
                                    st.write(f"Error: {mcp_data['error']}")
                    
                    # Status based on both results
                    if parallel_result.get('ready_for_api_integration'):
                        st.write("✅ **System Ready:** Both discovery and MCP server generation completed successfully!")
                        status.update(label="✅ Phase 1: Parallel Setup Complete", state="complete")
                    else:
                        st.write("⚠️ **Setup Issues:** Some tasks failed - check details above")
                        status.update(label="⚠️ Phase 1: Setup Issues", state="error")
                
                # Phase 2: Organization (only if discovery succeeded)
                if discovery_result and discovery_result.total_endpoints > 0:
                    with st.status("📦 Phase 2: Organizing endpoints...", expanded=True) as status:
                        st.write("Organizing endpoints by category for selection...")
                        st.write("Preparing endpoint data for user review...")
                        
                        # No chunking - just organize the data for display
                        st.write(f"✅ Organized {discovery_result.total_endpoints} endpoints")
                        status.update(label="✅ Phase 2: Organization Complete", state="complete")
                else:
                    st.error("❌ Cannot proceed to organization phase - discovery failed or found no endpoints")
            
            # Store results in session state for user selection
            st.session_state.discovery_result = discovery_result
            st.session_state.url = url_input
            
            # Count categories from discovery data
            categories_count = len(discovery_result.discovery_data.get('cs', []))
            
            st.success(f"🎉 Discovery complete! Found {discovery_result.total_endpoints} endpoints in {categories_count} categories.")
            
        except Exception as e:
            st.error(f"Discovery failed: {str(e)}")
            st.exception(e)
    
    # Display results if available
    if hasattr(st.session_state, 'discovery_result'):
        display_endpoint_selection()


def display_endpoint_selection():
    """Display the discovered endpoints grouped by category with selection checkboxes."""
    
    st.header("🎯 Select Endpoints for Extraction")
    st.markdown("Choose which endpoints you want to extract API usage examples for:")
    
    discovery_result = st.session_state.discovery_result
    
    # Initialize selection state
    if 'selected_endpoints' not in st.session_state:
        st.session_state.selected_endpoints = {}
    
    # Get categories directly from discovery data
    from urllib.parse import urlparse
    parsed_url = urlparse(discovery_result.website_url)
    hostname = parsed_url.netloc
    
    categories = {}
    if 'cs' in discovery_result.discovery_data:
        for category in discovery_result.discovery_data['cs']:
            category_name = category.get('n', category.get('name', 'Unknown'))
            categories[category_name] = []
            
            for endpoint in category.get('ls', []):
                endpoint_data = {
                    'category': category_name,
                    'endpoint': {
                        'title': endpoint.get('t', ''),
                        'path': endpoint.get('l', ''),
                        'url': f"https://{hostname}{endpoint.get('l', '')}"
                    }
                }
                categories[category_name].append(endpoint_data)
    
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
                    
                    # Find the endpoints in discovery data to get title and URL  
                    from urllib.parse import urlparse
                    parsed_url = urlparse(discovery_result.website_url)
                    hostname = parsed_url.netloc
                    
                    for category_data in discovery_result.discovery_data.get('cs', []):
                        if category_data.get('n', category_data.get('name', 'Unknown')) == category:
                            for endpoint in category_data.get('ls', []):
                                endpoint_path = endpoint.get('l', '')
                                if endpoint_path in selected_paths:
                                    title = endpoint.get('t', '')
                                    url = f"https://{hostname}{endpoint_path}"
                                    
                                    # Create a row with endpoint info and remove button
                                    col1, col2 = st.columns([4, 1])
                                    with col1:
                                        st.markdown(f"  - **{title}** - {url}")
                                    with col2:
                                        remove_key = f"remove_{category}_{endpoint_path}"
                                        if st.button("🗑️", key=remove_key, help=f"Remove {title}"):
                                            # Remove this endpoint from selection
                                            if endpoint_path in st.session_state.selected_endpoints[category]:
                                                st.session_state.selected_endpoints[category].remove(endpoint_path)
                                            # Clean up empty categories
                                            if not st.session_state.selected_endpoints[category]:
                                                st.session_state.selected_endpoints[category] = []
                                            st.rerun()
            
            # Next steps
            st.header("🚀 Next Steps")
            
            # Single button for proceeding to extraction
            if st.button("Next: 🔄 Extract API Usage", type="primary"):
                extract_selected_endpoints()


def extract_selected_endpoints():
    """Extract API usage for the selected endpoints."""
    try:
        # Get the current API key
        current_anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not current_anthropic_key:
            st.error("❌ Cannot proceed without Anthropic API Key")
            return
        
        # Initialize agentops if not already done
        import agentops
        if not hasattr(agentops, '_initialized'):
            agentops.init()
            agentops._initialized = True
        
        # Get the flow instance with template path support
        flow = ApiExtractionFlow(
            website_url=st.session_state.url,
            template_path=getattr(st.session_state, 'template_path', None)
        )
        
        # Run the complete extraction workflow
        with st.status("🔄 Extracting API Usage Examples...", expanded=True) as status:
            st.write("Phase 1: Creating chunks from your selected endpoints...")
            
            # Get total selected count for progress tracking
            total_selected = sum(len(paths) for paths in st.session_state.selected_endpoints.values())
            st.write(f"Processing {total_selected} selected endpoints...")
            
            # Create progress containers for real-time updates
            chunk_progress_container = st.empty()
            agent_activity_container = st.empty()
            detailed_progress_container = st.empty()
            
            # Show chunking phase
            with chunk_progress_container.container():
                st.info("📦 Creating optimal chunks for parallel processing...")
            
            # Get chunks to show chunking details
            chunks = flow.process_selected_endpoints(
                st.session_state.discovery_result, 
                st.session_state.selected_endpoints
            )
            
            # Update chunking status
            with chunk_progress_container.container():
                st.success(f"✅ Created {len(chunks)} chunks for processing")
                chunk_details = []
                for chunk in chunks:
                    chunk_details.append(f"Chunk {chunk.chunk_id}: {len(chunk.endpoints)} endpoints")
                st.write("**Chunk Distribution:**")
                for detail in chunk_details:
                    st.write(f"  • {detail}")
            
            status.update(label="🔄 Phase 2: Processing chunks in parallel...", state="running")
            
            # Show parallel processing details
            with agent_activity_container.container():
                st.info("🤖 Initializing AI agents for parallel processing...")
                st.write("**Agent Configuration:**")
                st.write(f"  • Total Chunks: {len(chunks)}")
                st.write(f"  • Max Parallel Workers: {min(len(chunks), 5)}")
                st.write(f"  • Agent Type: API Content Extractor")
                st.write("  • Processing Mode: ThreadPoolExecutor")
                
                # Create progress tracking for each chunk
                chunk_status_container = st.empty()
                with chunk_status_container.container():
                    st.write("**Chunk Processing Status:**")
                    for chunk in chunks:
                        st.write(f"  🔄 Chunk {chunk.chunk_id}: Queued ({len(chunk.endpoints)} endpoints)")
            
            st.write("Running AI agents to extract API usage examples...")
            st.write("This may take several minutes depending on the number of endpoints...")
            
            # Add a progress bar for overall completion
            progress_bar = st.progress(0, text="Starting parallel processing...")
            
            # Show live agent activity updates
            with detailed_progress_container.container():
                st.write("**Live Agent Activity:**")
                activity_placeholder = st.empty()
                chunk_status_placeholder = st.empty()
                
                with activity_placeholder.container():
                    st.write("⏳ Waiting for agents to start processing...")
            
            # Create progress callback for real-time updates
            def update_progress(progress_info):
                """Update the UI with real-time progress information"""
                completed = progress_info['completed']
                total = progress_info['total']
                current_chunk = progress_info['current_chunk']
                success = progress_info['success']
                thread_id = progress_info.get('thread_id', 'Unknown')
                endpoints = progress_info.get('endpoints_processed', 0)
                
                # Update progress bar
                progress_percentage = (completed / total) * 100
                progress_bar.progress(int(progress_percentage), 
                                    text=f"Processing: {completed}/{total} chunks completed ({progress_percentage:.1f}%)")
                
                # Update activity display
                with activity_placeholder.container():
                    status_icon = "✅" if success else "❌"
                    status_text = "SUCCESS" if success else "FAILED"
                    st.write(f"**Current Activity:** {status_icon} Chunk {current_chunk} - {status_text}")
                    st.write(f"  • Thread: {thread_id}")
                    st.write(f"  • Endpoints processed: {endpoints}")
                    st.write(f"  • Overall progress: {completed}/{total} chunks ({progress_percentage:.1f}%)")
                
                # Update chunk status overview
                with chunk_status_placeholder.container():
                    st.write("**Real-time Chunk Status:**")
                    for i, chunk in enumerate(chunks):
                        if i < completed:
                            # This chunk is completed - show final status
                            st.write(f"  ✅ Chunk {chunk.chunk_id}: Completed")
                        elif chunk.chunk_id == current_chunk:
                            # This is the current chunk being processed
                            st.write(f"  🔄 Chunk {chunk.chunk_id}: Processing now...")
                        else:
                            # This chunk is still queued
                            st.write(f"  ⏳ Chunk {chunk.chunk_id}: Queued")
            
            # Run the full extraction workflow with enhanced monitoring
            st.write("🚀 Launching parallel agent processing...")
            extraction_results = flow.extract_selected_endpoints_full(
                st.session_state.discovery_result, 
                st.session_state.selected_endpoints,
                progress_callback=update_progress
            )
            
            # Update progress bar to completion
            progress_bar.progress(100, text="Processing complete!")
            
            # Update final activity status
            with detailed_progress_container.container():
                st.write("**Live Agent Activity:**")
                with activity_placeholder.container():
                    st.success("✅ All agents completed processing!")
                    if extraction_results:
                        completed_chunks = len([r for r in extraction_results if 'error' not in r])
                        failed_chunks = len([r for r in extraction_results if 'error' in r])
                        st.write(f"  • Successful chunks: {completed_chunks}")
                        st.write(f"  • Failed chunks: {failed_chunks}")
                        for result in extraction_results:
                            status_icon = "✅" if 'error' not in result else "❌"
                            thread_info = f" (Thread {result.get('thread_id', 'Unknown')})" if 'thread_id' in result else ""
                            st.write(f"  {status_icon} Chunk {result['chunk_id']}: {result.get('endpoints_processed', 0)} endpoints{thread_info}")
            
            status.update(label="🔄 Phase 3: Finalizing results...", state="running")
            
            if not extraction_results:
                st.error("❌ No results could be extracted")
                return
            
            st.write(f"✅ Completed processing {len(extraction_results)} chunks!")
            status.update(label="✅ Extraction Complete!", state="complete")
        
        # Store the results in session state
        st.session_state.extraction_results = extraction_results
        
        # Calculate enhanced statistics
        total_chunks = len(extraction_results)
        successful_chunks = len([r for r in extraction_results if 'error' not in r])
        failed_chunks = len([r for r in extraction_results if 'error' in r])
        
        # Calculate endpoint-level statistics
        total_endpoints_processed = sum(r.get('endpoints_processed', 0) for r in extraction_results)
        successful_endpoints = sum(r.get('endpoints_processed', 0) for r in extraction_results if 'error' not in r)
        failed_endpoints = sum(r.get('endpoints_processed', 0) for r in extraction_results if 'error' in r)
        
        # Display results summary
        st.success(f"🎉 Extraction Complete!")
        
        # Enhanced statistics display
        st.subheader("📈 Processing Statistics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Processed Chunks", total_chunks)
            st.metric("Successful Chunks", successful_chunks)
            st.metric("Failed Chunks", failed_chunks)
            
        with col2:
            st.metric("Processed Endpoints", total_endpoints_processed)
            st.metric("Successful Endpoints", successful_endpoints)
            st.metric("Failed Endpoints", failed_endpoints)
            
        with col3:
            if total_chunks > 0:
                chunk_success_rate = (successful_chunks / total_chunks) * 100
                st.metric("Chunk Success Rate", f"{chunk_success_rate:.1f}%")
            
            if total_endpoints_processed > 0:
                endpoint_success_rate = (successful_endpoints / total_endpoints_processed) * 100
                st.metric("Endpoint Success Rate", f"{endpoint_success_rate:.1f}%")
        
        # Show detailed results
        st.header("📊 Extraction Details")
        
        # Show successful results
        if successful_chunks > 0:
            st.subheader("✅ Successful Extractions")
            
            for result in extraction_results:
                if 'error' not in result:
                    # Get the specific endpoints processed in this chunk from the flow
                    flow = ApiExtractionFlow(
                        website_url=st.session_state.url,
                        template_path=getattr(st.session_state, 'template_path', None)
                    )
                    
                    # Recreate the chunks to get endpoint details
                    chunks = flow.process_selected_endpoints(
                        st.session_state.discovery_result, 
                        st.session_state.selected_endpoints
                    )
                    
                    # Find the matching chunk
                    matching_chunk = None
                    for chunk in chunks:
                        if chunk.chunk_id == result['chunk_id']:
                            matching_chunk = chunk
                            break
                    
                    chunk_title = f"Chunk {result['chunk_id']} - {result['endpoints_processed']} endpoints"
                    
                    with st.expander(chunk_title, expanded=False):
                        if matching_chunk:
                            st.write("**Processed Endpoints:**")
                            for endpoint_data in matching_chunk.endpoints:
                                endpoint = endpoint_data['endpoint']
                                category = endpoint_data['category']
                                st.write(f"  • **{endpoint['title']}** ({category})")
                                st.write(f"    URL: `{endpoint['url']}`")
                        else:
                            st.write(f"**Endpoints:** {result['endpoints_processed']} endpoints processed successfully")
        
        # Show failures if any
        if failed_chunks > 0:
            st.subheader("❌ Failed Extractions")
            
            for result in extraction_results:
                if 'error' in result:
                    # Get the specific endpoints that failed
                    flow = ApiExtractionFlow(
                        website_url=st.session_state.url,
                        template_path=getattr(st.session_state, 'template_path', None)
                    )
                    chunks = flow.process_selected_endpoints(
                        st.session_state.discovery_result, 
                        st.session_state.selected_endpoints
                    )
                    
                    # Find the matching chunk
                    matching_chunk = None
                    for chunk in chunks:
                        if chunk.chunk_id == result['chunk_id']:
                            matching_chunk = chunk
                            break
                    
                    chunk_title = f"Chunk {result['chunk_id']} - ERROR"
                    
                    with st.expander(chunk_title, expanded=False):
                        st.error(f"**Error:** {result['error']}")
                        
                        if matching_chunk:
                            st.write("**Failed Endpoints:**")
                            for endpoint_data in matching_chunk.endpoints:
                                endpoint = endpoint_data['endpoint']
                                category = endpoint_data['category']
                                st.write(f"  • **{endpoint['title']}** ({category})")
                                st.write(f"    URL: `{endpoint['url']}`")
                        else:
                            st.write(f"**Affected Endpoints:** {result.get('endpoints_processed', 'Unknown')} endpoints")
        
        # Show processing summary
        st.header("� Processing Summary")
        if successful_chunks > 0:
            st.success(f"✅ Successfully extracted API usage examples from {successful_chunks} chunks containing {total_endpoints_processed} endpoints")
        
        if failed_chunks > 0:
            st.warning(f"⚠️ {failed_chunks} chunks failed to process. See details above.")
        
        st.info("💡 The extraction results contain API usage examples, code samples, and documentation for your selected endpoints.")
        
    except Exception as e:
        st.error(f"Failed to extract API usage: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    main()

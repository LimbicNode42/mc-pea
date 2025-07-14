"""
Agent Configuration Management for Streamlit Interface
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any
import streamlit as st

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from core.agent_config_loader import get_agent_config
except ImportError:
    def get_agent_config(agent_name: str) -> Dict[str, Any]:
        """Fallback agent config loader."""
        config_file = Path(__file__).parent.parent / "agent_configs.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                configs = json.load(f)
            return configs.get("agents", {}).get(agent_name, {})
        return {}


def render_agent_configuration_panel(agent: Dict[str, Any]):
    """Render configuration panel for a specific agent.
    
    Args:
        agent: Agent information dictionary
    """
    agent_name = agent["name"]
    
    st.markdown(f"### ⚙️ Configure {agent_name.replace('_', ' ').title()}")
    
    # Load current agent configuration
    try:
        config_data = get_agent_config(agent_name)
    except Exception as e:
        st.error(f"Failed to load agent configuration: {str(e)}")
        return
    
    # Agent-specific configuration based on agent type
    if agent_name == "web_scraper":
        render_web_scraper_config(config_data, agent_name)
    elif agent_name == "mcp_generator":
        render_mcp_generator_config(config_data, agent_name)
    elif agent_name == "api_analyzer":
        render_api_analyzer_config(config_data, agent_name)
    elif agent_name == "orchestrator":
        render_orchestrator_config(config_data, agent_name)
    elif agent_name == "validator":
        render_validator_config(config_data, agent_name)
    elif agent_name == "github_agent":
        render_github_agent_config(config_data, agent_name)
    else:
        render_generic_agent_config(config_data, agent_name)


def render_web_scraper_config(config_data: Dict[str, Any], agent_name: str):
    """Render configuration panel for WebScraperAgent."""
    st.markdown("#### 🕷️ Web Scraper Configuration")
    
    # Crawling configuration
    crawling_config = config_data.get("crawling", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Crawling Depth**")
        current_depth = crawling_config.get("default_depth", 2)
        min_depth = crawling_config.get("min_depth", 1)
        max_depth = crawling_config.get("max_depth", 5)
        
        new_depth = st.slider(
            "Crawl Depth",
            min_value=min_depth,
            max_value=max_depth,
            value=current_depth,
            help=f"Number of page levels to crawl. Current: {current_depth}"
        )
        
        # Show depth explanation
        if new_depth == 1:
            st.info("📄 **Depth 1**: Only the starting page")
        elif new_depth == 2:
            st.info("📄➡️📄 **Depth 2**: Starting page + direct links (recommended)")
        elif new_depth >= 3:
            st.warning(f"📄➡️📄➡️📄 **Depth {new_depth}**: May crawl many pages - use with caution")
    
    with col2:
        st.markdown("**Other Settings**")
        
        follow_external = st.checkbox(
            "Follow External Links",
            value=crawling_config.get("follow_external_links", False),
            help="Whether to follow links to external domains"
        )
        
        respect_robots = st.checkbox(
            "Respect robots.txt",
            value=crawling_config.get("respect_robots_txt", True),
            help="Whether to respect robots.txt files"
        )
        
        max_pages = st.number_input(
            "Max Pages per Domain",
            min_value=1,
            max_value=1000,
            value=crawling_config.get("max_pages_per_domain", 100),
            help="Maximum pages to crawl per domain"
        )
        
        request_delay = st.number_input(
            "Request Delay (seconds)",
            min_value=0.1,
            max_value=10.0,
            value=crawling_config.get("request_delay_seconds", 1.0),
            step=0.1,
            help="Delay between requests to be respectful"
        )
    
    # Save configuration button
    if st.button("💾 Save Web Scraper Config", type="primary"):
        try:
            # Update configuration
            updated_config = config_data.copy()
            updated_config["crawling"] = {
                "default_depth": new_depth,
                "max_depth": max_depth,
                "min_depth": min_depth,
                "follow_external_links": follow_external,
                "respect_robots_txt": respect_robots,
                "max_pages_per_domain": max_pages,
                "request_delay_seconds": request_delay
            }
            
            # Save to file
            save_agent_config(agent_name, updated_config)
            st.success(f"✅ Configuration saved for {agent_name}!")
            
        except Exception as e:
            st.error(f"❌ Failed to save configuration: {str(e)}")
    
    # Test configuration section
    st.markdown("#### 🧪 Test Configuration")
    test_url = st.text_input(
        "Test URL",
        value="https://docs.github.com/en/rest",
        help="URL to test the scraper configuration with"
    )
    
    if st.button("🚀 Test Scraper"):
        if test_url:
            with st.spinner("Testing web scraper configuration..."):
                try:
                    # Import and test the agent
                    from agents.web_scraper.web_scraper import WebScraperAgent
                    
                    # Create agent with new depth setting
                    agent = WebScraperAgent(crawl_depth=new_depth)
                    
                    # Get configuration to show
                    config = agent.get_crawling_config()
                    
                    st.success("🎉 Web scraper configuration test successful!")
                    st.json(config)
                    
                except Exception as e:
                    st.error(f"❌ Test failed: {str(e)}")
        else:
            st.warning("Please enter a test URL")


def render_github_agent_config(config_data: Dict[str, Any], agent_name: str):
    """Render configuration panel for GitHub Agent."""
    st.markdown("#### 🐙 GitHub Agent Configuration")
    
    # GitHub-specific configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Repository Settings**")
        
        default_owner = st.text_input(
            "Default Repository Owner",
            value=config_data.get("github", {}).get("default_owner", ""),
            help="Default GitHub username or organization"
        )
        
        default_branch = st.text_input(
            "Default Branch",
            value=config_data.get("github", {}).get("default_branch", "main"),
            help="Default branch for new repositories"
        )
        
        auto_create_issues = st.checkbox(
            "Auto-create Issues",
            value=config_data.get("github", {}).get("auto_create_issues", True),
            help="Automatically create issues for workflow steps"
        )
    
    with col2:
        st.markdown("**Workflow Settings**")
        
        enable_pr_workflow = st.checkbox(
            "Enable PR Workflow",
            value=config_data.get("github", {}).get("enable_pr_workflow", True),
            help="Create pull requests for generated code"
        )
        
        auto_merge = st.checkbox(
            "Auto-merge PRs",
            value=config_data.get("github", {}).get("auto_merge", False),
            help="Automatically merge passing PRs"
        )
        
        required_checks = st.text_input(
            "Required Status Checks",
            value=", ".join(config_data.get("github", {}).get("required_checks", ["ci", "tests"])),
            help="Comma-separated list of required checks"
        )
    
    # MCP Server Configuration
    st.markdown("**MCP Server Settings**")
    
    mcp_config = config_data.get("mcp_config", {})
    
    use_github_mcp = st.checkbox(
        "Use GitHub MCP Server",
        value=mcp_config.get("use_github_mcp", True),
        help="Use official GitHub MCP server for operations"
    )
    
    if use_github_mcp:
        github_token = st.text_input(
            "GitHub Personal Access Token",
            type="password",
            help="Required for GitHub API access"
        )
        
        if not github_token:
            st.warning("⚠️ GitHub token required for MCP server operations")
    
    # Save configuration button
    if st.button("💾 Save GitHub Agent Config", type="primary"):
        try:
            # Update configuration
            updated_config = config_data.copy()
            
            # Parse required checks
            checks_list = [check.strip() for check in required_checks.split(",") if check.strip()]
            
            updated_config["github"] = {
                "default_owner": default_owner,
                "default_branch": default_branch,
                "auto_create_issues": auto_create_issues,
                "enable_pr_workflow": enable_pr_workflow,
                "auto_merge": auto_merge,
                "required_checks": checks_list
            }
            
            updated_config["mcp_config"] = {
                "use_github_mcp": use_github_mcp
            }
            
            # Save to file
            save_agent_config(agent_name, updated_config)
            st.success(f"✅ Configuration saved for {agent_name}!")
            
        except Exception as e:
            st.error(f"❌ Failed to save configuration: {str(e)}")
    
    # Test GitHub connection
    st.markdown("#### 🧪 Test GitHub Connection")
    
    if st.button("🚀 Test GitHub Connection"):
        if github_token:
            with st.spinner("Testing GitHub connection..."):
                try:
                    # Test GitHub connection
                    import requests
                    headers = {"Authorization": f"token {github_token}"}
                    response = requests.get("https://api.github.com/user", headers=headers)
                    
                    if response.status_code == 200:
                        user_info = response.json()
                        st.success(f"🎉 Connected as: {user_info.get('login', 'Unknown')}")
                        st.json({
                            "login": user_info.get("login"),
                            "name": user_info.get("name"),
                            "public_repos": user_info.get("public_repos"),
                            "private_repos": user_info.get("total_private_repos")
                        })
                    else:
                        st.error(f"❌ GitHub API error: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"❌ Connection test failed: {str(e)}")
        else:
            st.warning("Please enter a GitHub token to test the connection")


def render_generic_agent_config(config_data: Dict[str, Any], agent_name: str):
    """Render generic configuration panel for agents without specific config."""
    st.markdown(f"#### ⚙️ {agent_name.replace('_', ' ').title()} Configuration")
    
    # Show basic agent info
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Agent Details**")
        st.write(f"**Name:** {config_data.get('name', agent_name)}")
        st.write(f"**Role:** {config_data.get('role', 'Unknown')}")
        st.write(f"**Goal:** {config_data.get('goal', 'Not specified')}")
    
    with col2:
        st.markdown("**Dependencies**")
        deps = config_data.get("mcp_dependencies", [])
        if deps:
            for dep in deps:
                st.write(f"• {dep.get('name', 'Unknown')}")
        else:
            st.write("No MCP dependencies")
    
    # Show backstory
    backstory = config_data.get("backstory", "")
    if backstory:
        st.markdown("**Agent Backstory**")
        st.text_area("Backstory", value=backstory, height=100, disabled=True)
    
    st.info("🔧 Specific configuration options will be added for this agent type in future updates.")


def render_mcp_generator_config(config_data: Dict[str, Any], agent_name: str):
    """Render configuration panel for MCP Generator Agent."""
    st.markdown("#### 🏗️ MCP Generator Configuration")
    
    # Generator-specific settings
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Generation Settings**")
        
        include_tests = st.checkbox(
            "Include Tests",
            value=config_data.get("generation", {}).get("include_tests", True),
            help="Generate test files for MCP servers"
        )
        
        include_docs = st.checkbox(
            "Include Documentation",
            value=config_data.get("generation", {}).get("include_docs", True),
            help="Generate README and documentation files"
        )
        
        use_typescript = st.checkbox(
            "Use TypeScript",
            value=config_data.get("generation", {}).get("use_typescript", True),
            help="Generate TypeScript MCP servers (recommended)"
        )
    
    with col2:
        st.markdown("**Template Settings**")
        
        template_source = st.selectbox(
            "Template Source",
            ["official", "custom", "minimal"],
            index=0,
            help="Template to use for server generation"
        )
        
        follow_standards = st.checkbox(
            "Follow MC-PEA Standards",
            value=config_data.get("generation", {}).get("follow_standards", True),
            help="Ensure generated servers follow MC-PEA project standards"
        )
    
    # Save configuration
    if st.button("💾 Save MCP Generator Config", type="primary"):
        try:
            updated_config = config_data.copy()
            updated_config["generation"] = {
                "include_tests": include_tests,
                "include_docs": include_docs,
                "use_typescript": use_typescript,
                "template_source": template_source,
                "follow_standards": follow_standards
            }
            
            save_agent_config(agent_name, updated_config)
            st.success(f"✅ Configuration saved for {agent_name}!")
            
        except Exception as e:
            st.error(f"❌ Failed to save configuration: {str(e)}")


def render_api_analyzer_config(config_data: Dict[str, Any], agent_name: str):
    """Render configuration panel for API Analyzer Agent."""
    st.markdown("#### 🔍 API Analyzer Configuration")
    st.info("🔧 API Analyzer specific configuration options coming soon!")
    render_generic_agent_config(config_data, agent_name)


def render_orchestrator_config(config_data: Dict[str, Any], agent_name: str):
    """Render configuration panel for Orchestrator Agent."""
    st.markdown("#### 🎭 Orchestrator Configuration")
    st.info("🔧 Orchestrator specific configuration options coming soon!")
    render_generic_agent_config(config_data, agent_name)


def render_validator_config(config_data: Dict[str, Any], agent_name: str):
    """Render configuration panel for Validator Agent."""
    st.markdown("#### ✅ Validator Configuration")
    st.info("🔧 Validator specific configuration options coming soon!")
    render_generic_agent_config(config_data, agent_name)


def save_agent_config(agent_name: str, config_data: Dict[str, Any]):
    """Save agent configuration to file.
    
    Args:
        agent_name: Name of the agent
        config_data: Configuration data to save
    """
    config_file = Path(__file__).parent.parent / "agent_configs.json"
    
    # Load existing configuration
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            all_configs = json.load(f)
    else:
        all_configs = {"agents": {}}
    
    # Update specific agent configuration
    all_configs["agents"][agent_name] = config_data
    
    # Save back to file
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(all_configs, f, indent=2, ensure_ascii=False)

"""
Test script for GitHub Agent functionality.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the ai-agents directory to the path
current_dir = Path(__file__).parent
ai_agents_dir = current_dir
sys.path.insert(0, str(ai_agents_dir))

from agents.github_agent import GitHubAgent, RepositoryManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_github_agent():
    """Test GitHub agent functionality."""
    print("🧪 Testing GitHub Agent")
    print("=" * 50)
    
    try:
        # Initialize GitHub agent
        github_agent = GitHubAgent()
        print("✅ GitHub agent initialized successfully")
        
        # Test GitHub access validation
        print("\n🔍 Testing GitHub access validation...")
        validation_result = github_agent.validate_github_access()
        print(f"Validation result: {json.dumps(validation_result, indent=2)}")
        
        if not validation_result.get('success'):
            print("❌ GitHub access validation failed")
            return False
        
        # Test user info
        print("\n👤 Testing user info retrieval...")
        user_info = github_agent.get_user_info()
        print(f"User info: {json.dumps(user_info, indent=2)}")
        
        # Test repository manager
        print("\n📁 Testing Repository Manager...")
        repo_manager = RepositoryManager()
        
        # Create a test specification
        test_spec = {
            'name': 'test-api-mcp-server',
            'description': 'A test MCP server for API integration',
            'github_org': 'test-org',
            'language': 'TypeScript',
            'api_url': 'https://api.example.com',
            'api_docs_url': 'https://docs.api.example.com',
            'auth_type': 'api_key',
            'tools': ['get_data', 'post_data'],
            'resources': ['api_status', 'api_docs']
        }
        
        # Test file preparation
        mock_generated_code = {
            "src/index.ts": "// Generated MCP server code\nexport {};\n",
            "src/tools/api_tools.ts": "// Generated API tools\nexport {};\n"
        }
        
        repository_files = repo_manager.prepare_repository_files(test_spec, mock_generated_code)
        print(f"✅ Prepared {len(repository_files)} repository files")
        
        # Show some example files
        print("\n📄 Sample generated files:")
        for file_path in list(repository_files.keys())[:5]:
            print(f"  - {file_path}")
        
        # Test complete repository setup (mock mode)
        print("\n🚀 Testing complete repository setup...")
        setup_result = github_agent.setup_mcp_server_repository(test_spec, repository_files)
        print(f"Setup result: {json.dumps(setup_result, indent=2)}")
        
        print("\n✅ GitHub agent tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_repository_manager():
    """Test repository manager functionality."""
    print("\n🧪 Testing Repository Manager")
    print("=" * 50)
    
    try:
        repo_manager = RepositoryManager()
        
        # Test specification
        test_spec = {
            'name': 'weather-api-mcp-server',
            'description': 'MCP server for weather API integration',
            'github_org': 'weather-org',
            'language': 'TypeScript',
            'api_url': 'https://api.weather.com',
            'api_docs_url': 'https://docs.weather.com/api',
            'auth_type': 'api_key',
            'tools': ['get_weather', 'get_forecast', 'get_alerts'],
            'resources': ['weather_stations', 'weather_data']
        }
        
        # Mock generated code
        generated_code = {
            "src/index.ts": "// Weather MCP server\nexport {};\n",
            "src/tools/weather_tools.ts": "// Weather API tools\nexport {};\n",
            "src/resources/weather_resources.ts": "// Weather resources\nexport {};\n"
        }
        
        # Generate repository files
        repo_files = repo_manager.prepare_repository_files(test_spec, generated_code)
        
        print(f"✅ Generated {len(repo_files)} files for repository")
        
        # Show file structure
        print("\n📁 Repository structure:")
        for file_path in sorted(repo_files.keys()):
            file_size = len(repo_files[file_path])
            print(f"  {file_path} ({file_size} bytes)")
        
        # Show package.json content
        if "package.json" in repo_files:
            print("\n📦 package.json content:")
            package_json = json.loads(repo_files["package.json"])
            print(json.dumps(package_json, indent=2))
        
        # Show README.md preview
        if "README.md" in repo_files:
            readme_lines = repo_files["README.md"].split('\n')
            print(f"\n📄 README.md preview (first 10 lines):")
            for i, line in enumerate(readme_lines[:10]):
                print(f"  {i+1}: {line}")
        
        print("\n✅ Repository manager tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during repository manager testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🤖 GitHub Agent Test Suite")
    print("=" * 60)
    
    # Check environment variables
    github_token = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')
    if not github_token:
        print("⚠️  GITHUB_PERSONAL_ACCESS_TOKEN environment variable not set")
        print("   GitHub API operations will run in mock mode")
    else:
        print(f"✅ GitHub token found: {github_token[:8]}...")
    
    # Run tests
    repo_success = test_repository_manager()
    github_success = test_github_agent()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"  Repository Manager: {'✅ PASSED' if repo_success else '❌ FAILED'}")
    print(f"  GitHub Agent: {'✅ PASSED' if github_success else '❌ FAILED'}")
    
    if repo_success and github_success:
        print("\n🎉 All tests passed! GitHub agent is ready for use.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

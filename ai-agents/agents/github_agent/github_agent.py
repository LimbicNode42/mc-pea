"""
GitHub Agent - AI agent for GitHub operations using the official GitHub MCP server.

This agent handles repository creation, management, commits, pull requests,
and other GitHub operations by leveraging the official GitHub MCP server tools.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from crewai import Agent, Task
except ImportError:
    Agent = object
    Task = object

from core.base_agent import BaseAgent, AgentConfig, AgentMessage, AgentResult

try:
    from tools.mcp_validators import MCPValidator
except ImportError:
    class MCPValidator:
        def __init__(self):
            pass


class GitHubAgent(BaseAgent):
    """
    AI agent for GitHub operations using the official GitHub MCP server.
    
    This agent provides:
    - Repository creation and management
    - Branch operations
    - File operations (create, update, delete)
    - Issue and pull request management  
    - GitHub Actions integration
    - Organization and user management
    
    Uses the official GitHub MCP server: https://github.com/github/github-mcp-server
    """

    def __init__(self, github_token: str = None, toolsets: List[str] = None):
        """
        Initialize GitHub Agent.
        
        Args:
            github_token: GitHub Personal Access Token (optional, can use env var)
            toolsets: List of GitHub MCP server toolsets to enable 
                     (e.g., ['repos', 'issues', 'pull_requests'])
        """
        # Create agent configuration
        agent_config = AgentConfig(
            name="github_agent",
            role='GitHub Operations Agent',
            goal='Manage GitHub repositories, issues, pull requests, and automations',
            backstory=(
                'Expert GitHub automation specialist with deep knowledge of '
                'Git workflows, repository management, and GitHub APIs. '
                'Specializes in creating and managing repositories for MCP servers.'
            )
        )
        
        # Initialize base agent
        super().__init__(agent_config)
        
        self.github_token = github_token or os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')
        self.toolsets = toolsets or ['repos', 'issues', 'pull_requests', 'actions', 'context']
        self.mcp_validator = MCPValidator()
        
        # MCP Server dependency
        self.mcp_server_dependency = {
            "name": "github-mcp-server",
            "package": "github-mcp-server",
            "description": "Official GitHub MCP server for repository operations, issues, and pull requests",
            "repository": "https://github.com/github/github-mcp-server",
            "required": True,
            "status": "official",
            "docker_required": False,
            "installation": {
                "method": "npm",
                "command": "npm install -g github-mcp-server",
                "alternative": "npx github-mcp-server",
                "verification": "github-mcp-server --version"
            },
            "config": {
                "mcpServers": {
                    "github": {
                        "command": "github-mcp-server",
                        "env": {
                            "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
                        }
                    }
                }
            },
            "tools_provided": [
                "create_repository",
                "create_branch", 
                "push_files",
                "create_pull_request",
                "create_issue",
                "get_me",
                "list_repositories",
                "get_repository",
                "update_repository",
                "delete_repository"
            ],
            "fallback_available": False,
            "fallback_description": "No fallback available - requires GitHub MCP server for repository operations"
        }
        
        if not self.github_token:
            raise ValueError(
                "GitHub Personal Access Token is required. "
                "Set GITHUB_PERSONAL_ACCESS_TOKEN environment variable or pass github_token parameter."
            )
    
    def create_repository(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new GitHub repository for an MCP server.
        
        Args:
            specification: Server specification containing:
                - name: Repository name
                - description: Repository description  
                - github_org: GitHub organization/profile
                - language: Programming language (TypeScript)
                - private: Whether repository should be private (default: False)
        
        Returns:
            Dict containing repository creation results
        """
        try:
            repo_name = specification.get('name')
            github_org = specification.get('github_org')
            description = specification.get('description', f'MCP Server for {repo_name}')
            is_private = specification.get('private', False)
            
            if not repo_name or not github_org:
                raise ValueError("Repository name and GitHub organization are required")
            
            # Prepare repository creation data
            repo_data = {
                'name': repo_name,
                'description': description,
                'private': is_private,
                'auto_init': True,  # Initialize with README
                'gitignore_template': 'Node',  # TypeScript/Node.js template
                'license_template': 'mit'
            }
            
            # Use GitHub MCP server to create repository
            # This would be called through the MCP client interface
            result = self._call_github_mcp_tool('create_repository', {
                'owner': github_org,
                'data': repo_data
            })
            
            logging.info(f"Created repository: {github_org}/{repo_name}")
            
            return {
                'success': True,
                'repository_url': f"https://github.com/{github_org}/{repo_name}",
                'clone_url': f"git@github.com:{github_org}/{repo_name}.git",
                'repository_data': result
            }
            
        except Exception as e:
            logging.error(f"Failed to create repository: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_branch(self, repo_owner: str, repo_name: str, branch_name: str, 
                     from_branch: str = 'main') -> Dict[str, Any]:
        """
        Create a new branch in the repository.
        
        Args:
            repo_owner: Repository owner/organization
            repo_name: Repository name
            branch_name: Name for the new branch
            from_branch: Source branch (default: 'main')
        
        Returns:
            Dict containing branch creation results
        """
        try:
            result = self._call_github_mcp_tool('create_branch', {
                'owner': repo_owner,
                'repo': repo_name,
                'branch': branch_name,
                'from_branch': from_branch
            })
            
            logging.info(f"Created branch {branch_name} in {repo_owner}/{repo_name}")
            
            return {
                'success': True,
                'branch_name': branch_name,
                'branch_data': result
            }
            
        except Exception as e:
            logging.error(f"Failed to create branch: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def push_files(self, repo_owner: str, repo_name: str, branch: str, 
                   files: List[Dict[str, str]], commit_message: str) -> Dict[str, Any]:
        """
        Push multiple files to a repository in a single commit.
        
        Args:
            repo_owner: Repository owner/organization
            repo_name: Repository name  
            branch: Target branch
            files: List of file objects with 'path' and 'content' keys
            commit_message: Commit message
        
        Returns:
            Dict containing push results
        """
        try:
            result = self._call_github_mcp_tool('push_files', {
                'owner': repo_owner,
                'repo': repo_name,
                'branch': branch,
                'files': files,
                'message': commit_message
            })
            
            logging.info(f"Pushed {len(files)} files to {repo_owner}/{repo_name}:{branch}")
            
            return {
                'success': True,
                'commit_sha': result.get('commit', {}).get('sha'),
                'files_count': len(files),
                'commit_data': result
            }
            
        except Exception as e:
            logging.error(f"Failed to push files: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_pull_request(self, repo_owner: str, repo_name: str, 
                           head_branch: str, base_branch: str = 'main',
                           title: str = None, description: str = None) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            repo_owner: Repository owner/organization
            repo_name: Repository name
            head_branch: Source branch
            base_branch: Target branch (default: 'main')
            title: Pull request title
            description: Pull request description
        
        Returns:
            Dict containing pull request creation results
        """
        try:
            pr_title = title or f"Add MCP server implementation from {head_branch}"
            pr_description = description or f"Generated MCP server code from branch {head_branch}"
            
            result = self._call_github_mcp_tool('create_pull_request', {
                'owner': repo_owner,
                'repo': repo_name,
                'title': pr_title,
                'head': head_branch,
                'base': base_branch,
                'body': pr_description
            })
            
            logging.info(f"Created pull request in {repo_owner}/{repo_name}")
            
            return {
                'success': True,
                'pull_request_url': result.get('html_url'),
                'pull_request_number': result.get('number'),
                'pull_request_data': result
            }
            
        except Exception as e:
            logging.error(f"Failed to create pull request: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_issue(self, repo_owner: str, repo_name: str, title: str, 
                    description: str, labels: List[str] = None) -> Dict[str, Any]:
        """
        Create an issue in the repository.
        
        Args:
            repo_owner: Repository owner/organization
            repo_name: Repository name
            title: Issue title
            description: Issue description
            labels: List of labels to add
        
        Returns:
            Dict containing issue creation results
        """
        try:
            result = self._call_github_mcp_tool('create_issue', {
                'owner': repo_owner,
                'repo': repo_name,
                'title': title,
                'body': description,
                'labels': labels or []
            })
            
            logging.info(f"Created issue in {repo_owner}/{repo_name}: {title}")
            
            return {
                'success': True,
                'issue_url': result.get('html_url'),
                'issue_number': result.get('number'),
                'issue_data': result
            }
            
        except Exception as e:
            logging.error(f"Failed to create issue: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated GitHub user.
        
        Returns:
            Dict containing user information
        """
        try:
            result = self._call_github_mcp_tool('get_me', {})
            
            return {
                'success': True,
                'username': result.get('login'),
                'user_data': result
            }
            
        except Exception as e:
            logging.error(f"Failed to get user info: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def setup_mcp_server_repository(self, specification: Dict[str, Any], 
                                   generated_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Complete setup of an MCP server repository.
        
        This method:
        1. Creates the repository
        2. Creates a development branch
        3. Pushes all generated files
        4. Creates a pull request for review
        
        Args:
            specification: Server specification
            generated_files: Dict mapping file paths to content
        
        Returns:
            Dict containing complete setup results
        """
        try:
            repo_name = specification.get('name')
            github_org = specification.get('github_org')
            
            # Step 1: Create repository
            repo_result = self.create_repository(specification)
            if not repo_result.get('success'):
                return repo_result
            
            # Step 2: Create development branch
            dev_branch = f"feature/initial-implementation"
            branch_result = self.create_branch(github_org, repo_name, dev_branch)
            if not branch_result.get('success'):
                return branch_result
            
            # Step 3: Prepare files for push
            files_to_push = []
            for file_path, content in generated_files.items():
                files_to_push.append({
                    'path': file_path,
                    'content': content
                })
            
            # Step 4: Push all files
            commit_message = f"Initial MCP server implementation\n\nGenerated {repo_name} MCP server with:\n- TypeScript implementation\n- Complete tool and resource definitions\n- Testing infrastructure\n- Documentation"
            
            push_result = self.push_files(
                github_org, repo_name, dev_branch, 
                files_to_push, commit_message
            )
            if not push_result.get('success'):
                return push_result
            
            # Step 5: Create pull request
            pr_title = f"Initial implementation of {repo_name} MCP server"
            pr_description = f"""# {repo_name} MCP Server

This pull request contains the initial implementation of the {repo_name} MCP server.

## Features
- **Language**: {specification.get('language', 'TypeScript')}
- **Authentication**: {specification.get('auth_type', 'api_key')}
- **API Base**: {specification.get('api_url', 'N/A')}
- **Documentation**: {specification.get('api_docs_url', 'N/A')}

## Generated Components
- Complete TypeScript MCP server implementation
- Tool definitions for API operations
- Resource definitions for data access
- Comprehensive test suite
- Docker configuration
- Documentation

## Next Steps
1. Review the generated code
2. Test the MCP server locally
3. Configure environment variables
4. Deploy to production

Generated by MC-PEA AI Agent System 🤖
"""
            
            pr_result = self.create_pull_request(
                github_org, repo_name, dev_branch, 'main',
                pr_title, pr_description
            )
            
            return {
                'success': True,
                'repository_url': repo_result.get('repository_url'),
                'pull_request_url': pr_result.get('pull_request_url'),
                'files_pushed': len(files_to_push),
                'results': {
                    'repository': repo_result,
                    'branch': branch_result,
                    'files': push_result,
                    'pull_request': pr_result
                }
            }
            
        except Exception as e:
            logging.error(f"Failed to setup MCP server repository: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _call_github_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Call a GitHub MCP server tool.
        
        This is a placeholder for the actual MCP client interface.
        In the real implementation, this would communicate with the GitHub MCP server.
        
        Args:
            tool_name: Name of the GitHub MCP tool to call
            params: Parameters for the tool
        
        Returns:
            Tool execution result
        """
        # TODO: Implement actual MCP client interface
        # For now, return mock response for development
        logging.info(f"Calling GitHub MCP tool: {tool_name} with params: {params}")
        
        # Mock responses for development
        mock_responses = {
            'create_repository': {
                'id': 123456,
                'name': params.get('data', {}).get('name', 'test-repo'),
                'full_name': f"{params.get('owner', 'test-org')}/{params.get('data', {}).get('name', 'test-repo')}",
                'html_url': f"https://github.com/{params.get('owner', 'test-org')}/{params.get('data', {}).get('name', 'test-repo')}",
                'clone_url': f"git@github.com:{params.get('owner', 'test-org')}/{params.get('data', {}).get('name', 'test-repo')}.git"
            },
            'create_branch': {
                'ref': f"refs/heads/{params.get('branch', 'test-branch')}",
                'sha': 'abc123def456'
            },
            'push_files': {
                'commit': {
                    'sha': 'def456abc123',
                    'message': params.get('message', 'Test commit')
                }
            },
            'create_pull_request': {
                'number': 1,
                'html_url': f"https://github.com/{params.get('owner', 'test-org')}/{params.get('repo', 'test-repo')}/pull/1",
                'title': params.get('title', 'Test PR')
            },
            'create_issue': {
                'number': 1,
                'html_url': f"https://github.com/{params.get('owner', 'test-org')}/{params.get('repo', 'test-repo')}/issues/1",
                'title': params.get('title', 'Test Issue')
            },
            'get_me': {
                'login': 'test-user',
                'id': 12345,
                'name': 'Test User'
            }
        }
        
        return mock_responses.get(tool_name, {})
    
    def validate_github_access(self) -> Dict[str, Any]:
        """
        Validate GitHub access and permissions.
        
        Returns:
            Dict containing validation results
        """
        try:
            user_info = self.get_user_info()
            if user_info.get('success'):
                return {
                    'success': True,
                    'message': f"GitHub access validated for user: {user_info.get('username')}",
                    'user_info': user_info
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to authenticate with GitHub'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"GitHub validation failed: {str(e)}"
            }
    
    def get_tools(self) -> List[Any]:
        """Get tools available to this agent.
        
        Returns:
            List of tools for GitHub operations
        """
        # For now, return empty list since tools are handled via MCP client interface
        # In future iterations, these could be proper CrewAI tool instances
        return []
    
    def get_mcp_dependencies(self) -> List[Dict[str, Any]]:
        """Get MCP server dependencies for this agent.
        
        Returns:
            List of MCP server dependencies
        """
        return [self.mcp_server_dependency]
    
    async def process_message(self, message: AgentMessage) -> AgentResult:
        """Process an incoming message.
        
        Args:
            message: Incoming message
            
        Returns:
            Processing result
        """
        try:
            message_type = message.message_type
            content = message.content
            
            if message_type == "create_repository":
                result = self.create_repository(content)
            elif message_type == "setup_mcp_server_repository":
                result = self.setup_mcp_server_repository(
                    content.get('specification', {}),
                    content.get('generated_files', {})
                )
            elif message_type == "validate_github_access":
                result = self.validate_github_access()
            else:
                return AgentResult(
                    success=False,
                    error=f"Unknown message type: {message_type}"
                )
            
            return AgentResult(
                success=result.get('success', False),
                result=result,
                metadata={'message_id': message.correlation_id}
            )
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e),
                metadata={'message_id': message.correlation_id}
            )
    
    async def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        """Execute a specific task.
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        try:
            task_type = task.get('type')
            task_data = task.get('data', {})
            
            if task_type == "create_repository":
                result = self.create_repository(task_data)
            elif task_type == "setup_mcp_server_repository":
                result = self.setup_mcp_server_repository(
                    task_data.get('specification', {}),
                    task_data.get('generated_files', {})
                )
            elif task_type == "validate_github_access":
                result = self.validate_github_access()
            else:
                return AgentResult(
                    success=False,
                    error=f"Unknown task type: {task_type}"
                )
            
            return AgentResult(
                success=result.get('success', False),
                result=result,
                metadata={'task_id': task.get('id')}
            )
            
        except Exception as e:
            self.logger.error(f"Error executing task: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e),
                metadata={'task_id': task.get('id')}
            )

    # GitHub-specific methods (keeping all the existing implementation)

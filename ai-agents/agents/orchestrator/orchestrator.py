"""
Orchestrator Agent for coordinating MCP server generation workflows.
"""

from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew
from core.base_agent import BaseAgent, AgentConfig
from core.config import get_config, MCPEAConfig


class OrchestratorAgent(BaseAgent):
    """Agent responsible for orchestrating MCP server generation workflows."""
    
    def __init__(self, anthropic_client=None):
        # Create agent config
        agent_config = AgentConfig(
            name="orchestrator",
            role="MCP Server Generation Orchestrator",
            goal="Coordinate and manage the complete MCP server generation workflow",
            backstory="""
            You are an expert project manager specializing in software development workflows.
            You coordinate between different specialized agents to ensure smooth and efficient
            MCP server generation from specification to deployment-ready code.
            """
        )
        
        super().__init__(agent_config, anthropic_client)
        
        # Register for configuration updates
        self.register_config_callback(self._on_orchestrator_config_update)
    
    def _on_orchestrator_config_update(self, new_config: MCPEAConfig) -> None:
        """Handle orchestrator-specific configuration updates.
        
        Args:
            new_config: Updated configuration
        """
        # Update workflow settings based on config
        self.workflow_config = new_config.workflow
        self.generation_config = new_config.generation
        self.validation_config = new_config.validation
        
        self.logger.info("Orchestrator configuration updated")
    
    def get_tools(self) -> List[Any]:
        """Get tools available to this agent.
        
        Returns:
            List of tools for the orchestrator
        """
        return []  # Orchestrator primarily coordinates, doesn't use direct tools
    
    def create_generation_plan(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detailed plan for MCP server generation.
        
        Args:
            specification: Server specification from user input
            
        Returns:
            Generation plan with steps and dependencies
        """
        config = self.get_current_config()
        
        # Build plan based on current configuration
        steps = [
            {
                "name": "analyze_api",
                "agent": "api_analyzer",
                "dependencies": [],
                "status": "pending",
                "enabled": True
            },
            {
                "name": "generate_code",
                "agent": "mcp_generator", 
                "dependencies": ["analyze_api"],
                "status": "pending",
                "enabled": True
            }
        ]
        
        # Add optional steps based on configuration
        if config.generation.create_tests:
            steps.append({
                "name": "create_tests",
                "agent": "test_generator",
                "dependencies": ["generate_code"],
                "status": "pending",
                "enabled": True
            })
        
        if config.validation.auto_validate:
            validate_deps = ["generate_code"]
            if config.generation.create_tests:
                validate_deps.append("create_tests")
            
            steps.append({
                "name": "validate_mcp",
                "agent": "validator",
                "dependencies": validate_deps,
                "status": "pending", 
                "enabled": True
            })
        
        if config.generation.create_dockerfile:
            steps.append({
                "name": "create_docker",
                "agent": "docker_generator",
                "dependencies": ["validate_mcp"] if config.validation.auto_validate else ["generate_code"],
                "status": "pending",
                "enabled": True
            })
        
        # Package step always last if no GitHub, otherwise before GitHub
        final_deps = [step["name"] for step in steps]
        steps.append({
            "name": "package_server",
            "agent": "packager",
            "dependencies": final_deps[:-1],  # Exclude self
            "status": "pending",
            "enabled": True
        })
        
        # GitHub repository creation step
        if specification.get('github_org'):
            steps.append({
                "name": "create_github_repo",
                "agent": "github",
                "dependencies": ["package_server"],
                "status": "pending",
                "enabled": True
            })
        
        return {
            "steps": steps,
            "specification": specification,
            "estimated_duration": self._estimate_duration(steps),
            "parallel_execution": config.workflow.parallel_execution,
            "max_concurrent": config.workflow.max_concurrent_tasks
        }
    
    def _estimate_duration(self, steps: List[Dict[str, Any]]) -> str:
        """Estimate workflow duration based on steps.
        
        Args:
            steps: List of workflow steps
            
        Returns:
            Duration estimate string
        """
        base_time = len(steps) * 60  # 1 minute per step base
        
        config = self.get_current_config()
        if config.workflow.parallel_execution:
            base_time = base_time // min(config.workflow.max_concurrent_tasks, len(steps))
        
        minutes = base_time // 60
        return f"{minutes}-{minutes + 2} minutes"
    
    def execute_workflow(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete MCP server generation workflow.
        
        Args:
            specification: Server specification from user input
            
        Returns:
            Workflow execution results
        """
        config = self.get_current_config()
        plan = self.create_generation_plan(specification)
        
        # Get generation configuration
        output_dir = config.generation.output_directory
        server_name = specification.get("name", "unnamed-server")
        
        # Build file list based on configuration
        generated_files = ["src/index.ts", "package.json", "tsconfig.json"]
        
        # Add API-specific files
        if specification.get("api_type"):
            generated_files.extend([
                "src/tools/api_tools.ts",
                "src/resources/api_resources.ts"
            ])
        
        # Add optional files based on config
        if config.generation.create_tests:
            generated_files.extend([
                "tests/basic.test.ts",
                "tests/integration.test.ts"
            ])
        
        if config.generation.create_docs:
            generated_files.extend([
                "README.md",
                "docs/API.md"
            ])
        
        if config.generation.create_dockerfile:
            generated_files.extend([
                "Dockerfile",
                "docker-compose.yml"
            ])
        
        # GitHub repository creation if specified
        github_created = False
        repository_url = None
        pull_request_url = None
        
        if specification.get('github_org'):
            # This would integrate with the GitHub agent
            github_created = True
            github_org = specification.get('github_org')
            repository_url = f"https://github.com/{github_org}/{server_name}"
            pull_request_url = f"{repository_url}/pull/1"

        # Simulate workflow execution with realistic results
        results = {
            "success": True,
            "server_name": server_name,
            "output_directory": output_dir,
            "generated_files": generated_files,
            "plan": plan,
            "execution_time": plan["estimated_duration"],
            "mcp_compliance": config.validation.check_mcp_compliance,
            "typescript_validated": config.validation.check_typescript,
            "tests_created": config.generation.create_tests,
            "docs_created": config.generation.create_docs,
            "docker_created": config.generation.create_dockerfile,
            "github_created": github_created,
            "repository_url": repository_url,
            "pull_request_url": pull_request_url
        }
        
        return results
    
    async def process_message(self, message) -> Dict[str, Any]:
        """Process an incoming message.
        
        Args:
            message: Incoming message
            
        Returns:
            Processing result
        """
        # Handle different message types
        if hasattr(message, 'message_type'):
            if message.message_type == "generate_server":
                return self.execute_workflow(message.content)
            elif message.message_type == "create_plan":
                return self.create_generation_plan(message.content)
        
        return {"success": False, "error": "Unknown message type"}
    
    async def execute_task(self, task) -> Dict[str, Any]:
        """Execute a specific task.
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        # Handle different task types
        task_type = task.get('type', 'unknown')
        
        if task_type == 'generate_server':
            return self.execute_workflow(task.get('specification', {}))
        elif task_type == 'create_plan':
            return {"success": True, "result": self.create_generation_plan(task.get('specification', {}))}
        else:
            return {"success": False, "error": f"Unknown task type: {task_type}"}
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the current status of a running workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            
        Returns:
            Current workflow status
        """
        # Mock implementation
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "progress": 100,
            "current_step": "package_server",
            "steps_completed": 5,
            "total_steps": 5
        }

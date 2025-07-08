"""
CrewAI Workflow Definitions for MCP Server Development.
"""

from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew
from crewai.process import Process
from ..agents.mcp_generator import MCPServerGeneratorAgent
from ..agents.api_analyzer import APIAnalyzerAgent
from ..agents.validator import ValidatorAgent
from ..agents.orchestrator import OrchestratorAgent


class MCPServerDevelopmentCrew:
    """CrewAI crew for MCP server development workflows."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents = {}
        self.crew = None
        self._initialize_agents()
        self._setup_crew()
    
    def _initialize_agents(self):
        """Initialize CrewAI agents."""
        
        # API Analyzer Agent
        self.agents['api_analyzer'] = Agent(
            role='API Analyzer',
            goal='Analyze external APIs and generate comprehensive MCP server specifications',
            backstory="""You are an expert API analyst with deep knowledge of REST APIs, GraphQL, 
            and various API patterns. You excel at understanding API structures, authentication 
            methods, and data flows to create detailed specifications for MCP server development.""",
            verbose=True,
            allow_delegation=False,
            tools=[]  # Custom tools will be added
        )
        
        # MCP Server Generator Agent
        self.agents['mcp_generator'] = Agent(
            role='MCP Server Developer',
            goal='Generate high-quality, protocol-compliant MCP servers from specifications',
            backstory="""You are a senior TypeScript developer specializing in the Model Context 
            Protocol (MCP). You have extensive experience with the MCP SDK, server architecture, 
            and best practices for creating robust, secure, and performant MCP servers.""",
            verbose=True,
            allow_delegation=False,
            tools=[]  # Custom tools will be added
        )
        
        # Validator Agent
        self.agents['validator'] = Agent(
            role='Quality Assurance Engineer',
            goal='Validate MCP servers for protocol compliance, security, and performance',
            backstory="""You are a meticulous QA engineer with expertise in MCP protocol validation, 
            security testing, and performance optimization. You ensure that all generated servers 
            meet the highest standards of quality and reliability.""",
            verbose=True,
            allow_delegation=False,
            tools=[]  # Custom tools will be added
        )
        
        # Orchestrator Agent
        self.agents['orchestrator'] = Agent(
            role='Project Coordinator',
            goal='Coordinate multi-agent workflows and ensure successful project delivery',
            backstory="""You are an experienced project coordinator who excels at managing 
            complex workflows, coordinating team efforts, and ensuring timely delivery of 
            high-quality software projects.""",
            verbose=True,
            allow_delegation=True,
            tools=[]  # Custom tools will be added
        )
    
    def _setup_crew(self):
        """Setup the CrewAI crew with agents and process."""
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=[],  # Tasks will be added dynamically
            process=Process.hierarchical,
            manager_agent=self.agents['orchestrator'],
            verbose=True
        )
    
    def create_api_analysis_workflow(self, api_spec: Dict[str, Any]) -> List[Task]:
        """Create tasks for API analysis workflow."""
        
        analysis_task = Task(
            description=f"""
            Analyze the provided API specification and generate a comprehensive MCP server specification.
            
            API Details:
            - URL: {api_spec.get('url', 'N/A')}
            - Name: {api_spec.get('name', 'N/A')}
            - Description: {api_spec.get('description', 'N/A')}
            - Documentation: {api_spec.get('docs_url', 'N/A')}
            
            Requirements:
            1. Analyze API endpoints, authentication, and data structures
            2. Generate MCP server specification including tools and resources
            3. Identify security considerations and rate limiting requirements
            4. Provide recommendations for implementation approach
            5. Estimate complexity and development effort
            
            Output: Detailed MCP server specification in JSON format
            """,
            agent=self.agents['api_analyzer'],
            expected_output="A comprehensive MCP server specification with tools, resources, and implementation guidelines"
        )
        
        return [analysis_task]
    
    def create_server_generation_workflow(self, mcp_spec: Dict[str, Any], server_config: Dict[str, Any]) -> List[Task]:
        """Create tasks for MCP server generation workflow."""
        
        generation_task = Task(
            description=f"""
            Generate a complete MCP server implementation based on the provided specification.
            
            MCP Specification:
            {mcp_spec}
            
            Server Configuration:
            {server_config}
            
            Requirements:
            1. Generate TypeScript MCP server using the official SDK
            2. Implement all specified tools with proper schema validation
            3. Create resource endpoints for data access
            4. Implement authentication and security measures
            5. Add comprehensive error handling and logging
            6. Include proper TypeScript types and documentation
            7. Generate package.json, tsconfig.json, and build configuration
            8. Create Dockerfile for containerization
            9. Add unit tests and integration tests
            10. Generate README with usage instructions
            
            Output: Complete MCP server project with all necessary files
            """,
            agent=self.agents['mcp_generator'],
            expected_output="A complete TypeScript MCP server project with all source code, configuration, tests, and documentation"
        )
        
        return [generation_task]
    
    def create_validation_workflow(self, server_path: str, validation_config: Dict[str, Any]) -> List[Task]:
        """Create tasks for server validation workflow."""
        
        validation_task = Task(
            description=f"""
            Perform comprehensive validation of the MCP server at: {server_path}
            
            Validation Configuration:
            {validation_config}
            
            Requirements:
            1. Validate MCP protocol compliance using SDK client
            2. Check TypeScript compilation and code quality
            3. Run security analysis for vulnerabilities
            4. Measure performance metrics (startup time, memory usage)
            5. Validate test coverage and test quality
            6. Check documentation completeness
            7. Verify Docker build and containerization
            8. Test authentication and authorization flows
            9. Validate error handling and edge cases
            10. Generate detailed validation report with recommendations
            
            Output: Comprehensive validation report with scores and improvement recommendations
            """,
            agent=self.agents['validator'],
            expected_output="A detailed validation report with protocol compliance, quality metrics, and improvement recommendations"
        )
        
        return [validation_task]
    
    def create_full_development_workflow(self, api_spec: Dict[str, Any], server_config: Dict[str, Any]) -> List[Task]:
        """Create tasks for complete MCP server development workflow."""
        
        # API Analysis Task
        analysis_task = Task(
            description=f"""
            Analyze the provided API and generate MCP server specification.
            
            API: {api_spec.get('name', 'Unknown')} - {api_spec.get('url', '')}
            
            Analyze endpoints, authentication, data structures, and generate comprehensive
            MCP server specification with tools, resources, and implementation guidelines.
            """,
            agent=self.agents['api_analyzer'],
            expected_output="MCP server specification with tools, resources, and implementation details"
        )
        
        # Server Generation Task
        generation_task = Task(
            description="""
            Generate complete MCP server implementation from the analysis results.
            
            Use the MCP specification from the API analysis to create a full TypeScript
            MCP server with proper SDK usage, tools, resources, tests, and documentation.
            """,
            agent=self.agents['mcp_generator'],
            expected_output="Complete MCP server project with source code, tests, and documentation",
            depends_on=[analysis_task]
        )
        
        # Initial Validation Task
        validation_task = Task(
            description="""
            Validate the generated MCP server for protocol compliance and quality.
            
            Perform comprehensive validation including protocol compliance, code quality,
            security analysis, and performance testing. Generate detailed report.
            """,
            agent=self.agents['validator'],
            expected_output="Validation report with compliance scores and recommendations",
            depends_on=[generation_task]
        )
        
        # Refinement Task
        refinement_task = Task(
            description="""
            Refine the MCP server based on validation feedback.
            
            Use the validation report to improve the server implementation,
            fix issues, and enhance quality while maintaining protocol compliance.
            """,
            agent=self.agents['mcp_generator'],
            expected_output="Refined MCP server with improved quality and compliance",
            depends_on=[validation_task]
        )
        
        # Final Validation Task
        final_validation_task = Task(
            description="""
            Perform final validation of the refined MCP server.
            
            Verify that all issues have been resolved and the server meets
            all quality and compliance standards for production deployment.
            """,
            agent=self.agents['validator'],
            expected_output="Final validation report confirming production readiness",
            depends_on=[refinement_task]
        )
        
        return [analysis_task, generation_task, validation_task, refinement_task, final_validation_task]
    
    def create_orchestration_workflow(self, workflow_config: Dict[str, Any]) -> List[Task]:
        """Create tasks for workflow orchestration."""
        
        orchestration_task = Task(
            description=f"""
            Coordinate the execution of a complex MCP server development workflow.
            
            Workflow Configuration:
            {workflow_config}
            
            Requirements:
            1. Plan and sequence workflow steps
            2. Coordinate agent interactions
            3. Monitor progress and handle errors
            4. Ensure quality gates are met
            5. Manage dependencies and resource allocation
            6. Generate progress reports and metrics
            7. Handle workflow optimization and adaptation
            
            Output: Workflow execution report with results and metrics
            """,
            agent=self.agents['orchestrator'],
            expected_output="Workflow execution report with coordinated results from all agents"
        )
        
        return [orchestration_task]
    
    def execute_workflow(self, workflow_type: str, **kwargs) -> Dict[str, Any]:
        """Execute a workflow using CrewAI."""
        
        # Create tasks based on workflow type
        if workflow_type == 'api_analysis':
            tasks = self.create_api_analysis_workflow(kwargs.get('api_spec', {}))
        elif workflow_type == 'server_generation':
            tasks = self.create_server_generation_workflow(
                kwargs.get('mcp_spec', {}),
                kwargs.get('server_config', {})
            )
        elif workflow_type == 'validation':
            tasks = self.create_validation_workflow(
                kwargs.get('server_path', ''),
                kwargs.get('validation_config', {})
            )
        elif workflow_type == 'full_development':
            tasks = self.create_full_development_workflow(
                kwargs.get('api_spec', {}),
                kwargs.get('server_config', {})
            )
        elif workflow_type == 'orchestration':
            tasks = self.create_orchestration_workflow(kwargs.get('workflow_config', {}))
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        # Update crew with tasks
        self.crew.tasks = tasks
        
        # Execute the workflow
        result = self.crew.kickoff()
        
        return {
            'workflow_type': workflow_type,
            'result': result,
            'tasks_completed': len(tasks),
            'success': True
        }


class WorkflowTemplates:
    """Predefined workflow templates for common MCP server development scenarios."""
    
    @staticmethod
    def get_api_to_mcp_template() -> Dict[str, Any]:
        """Template for converting API to MCP server."""
        return {
            'name': 'API to MCP Server',
            'description': 'Convert external API to MCP server implementation',
            'steps': [
                {'type': 'api_analysis', 'agent': 'api_analyzer'},
                {'type': 'server_generation', 'agent': 'mcp_generator'},
                {'type': 'validation', 'agent': 'validator'}
            ],
            'inputs': ['api_spec', 'server_config'],
            'outputs': ['mcp_server_project', 'validation_report']
        }
    
    @staticmethod
    def get_validation_template() -> Dict[str, Any]:
        """Template for MCP server validation."""
        return {
            'name': 'MCP Server Validation',
            'description': 'Comprehensive validation of existing MCP server',
            'steps': [
                {'type': 'validation', 'agent': 'validator'}
            ],
            'inputs': ['server_path', 'validation_config'],
            'outputs': ['validation_report']
        }
    
    @staticmethod
    def get_full_cycle_template() -> Dict[str, Any]:
        """Template for full development cycle."""
        return {
            'name': 'Full Development Cycle',
            'description': 'Complete MCP server development from API to production',
            'steps': [
                {'type': 'api_analysis', 'agent': 'api_analyzer'},
                {'type': 'server_generation', 'agent': 'mcp_generator'},
                {'type': 'validation', 'agent': 'validator'},
                {'type': 'refinement', 'agent': 'mcp_generator'},
                {'type': 'final_validation', 'agent': 'validator'}
            ],
            'inputs': ['api_spec', 'server_config', 'quality_requirements'],
            'outputs': ['mcp_server_project', 'validation_report', 'deployment_package']
        }
    
    @staticmethod
    def get_all_templates() -> Dict[str, Dict[str, Any]]:
        """Get all available workflow templates."""
        return {
            'api_to_mcp': WorkflowTemplates.get_api_to_mcp_template(),
            'validation': WorkflowTemplates.get_validation_template(),
            'full_cycle': WorkflowTemplates.get_full_cycle_template()
        }

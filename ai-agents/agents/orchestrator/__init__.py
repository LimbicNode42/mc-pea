"""
Orchestrator Agent - Coordinates multi-agent workflows for MCP server development.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from ...core.base_agent import BaseAgent
from ...core.message_bus import MessageBus
from ..mcp_generator import MCPServerGeneratorAgent
from ..api_analyzer import APIAnalyzerAgent
from ..validator import ValidatorAgent


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrchestratorAgent(BaseAgent):
    """Agent that orchestrates multi-agent workflows for MCP server development."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.agents = {}
        self.workflows = {}
        self.active_workflows = {}
        self.workflow_history = []
        self.message_bus = MessageBus()
        
        # Initialize sub-agents
        self._initialize_agents()
        
        # Register workflow templates
        self._register_workflow_templates()
    
    def _initialize_agents(self):
        """Initialize sub-agents."""
        try:
            self.agents['generator'] = MCPServerGeneratorAgent(self.config)
            self.agents['analyzer'] = APIAnalyzerAgent(self.config)
            self.agents['validator'] = ValidatorAgent(self.config)
            
            # Subscribe to agent messages
            for agent_name, agent in self.agents.items():
                self.message_bus.subscribe(f"{agent_name}.*", self._handle_agent_message)
                
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
    
    def _register_workflow_templates(self):
        """Register predefined workflow templates."""
        self.workflows = {
            'generate_from_api': {
                'name': 'Generate MCP Server from API',
                'description': 'Analyze an API and generate a complete MCP server',
                'steps': [
                    {'agent': 'analyzer', 'action': 'analyze_api'},
                    {'agent': 'generator', 'action': 'generate_server'},
                    {'agent': 'validator', 'action': 'validate_server'}
                ],
                'parallel_steps': [],
                'dependencies': {
                    'generator': ['analyzer'],
                    'validator': ['generator']
                }
            },
            'validate_existing_server': {
                'name': 'Validate Existing MCP Server',
                'description': 'Comprehensive validation of an existing MCP server',
                'steps': [
                    {'agent': 'validator', 'action': 'validate_server'}
                ],
                'parallel_steps': [],
                'dependencies': {}
            },
            'full_development_cycle': {
                'name': 'Full MCP Server Development Cycle',
                'description': 'Complete development cycle from API analysis to validated server',
                'steps': [
                    {'agent': 'analyzer', 'action': 'analyze_api'},
                    {'agent': 'generator', 'action': 'generate_server'},
                    {'agent': 'validator', 'action': 'validate_server'},
                    {'agent': 'generator', 'action': 'refine_server'},
                    {'agent': 'validator', 'action': 'validate_server'}
                ],
                'parallel_steps': [],
                'dependencies': {
                    'generator': ['analyzer'],
                    'validator': ['generator']
                }
            }
        }
    
    async def execute_workflow(self, workflow_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow with given inputs.
        
        Args:
            workflow_id: ID of the workflow to execute
            inputs: Input parameters for the workflow
            
        Returns:
            Workflow execution results
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        execution_id = f"{workflow_id}_{datetime.now().timestamp()}"
        
        # Initialize workflow execution
        execution = {
            'id': execution_id,
            'workflow_id': workflow_id,
            'status': WorkflowStatus.PENDING,
            'inputs': inputs,
            'outputs': {},
            'steps': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'errors': [],
            'metrics': {}
        }
        
        self.active_workflows[execution_id] = execution
        
        try:
            await self._emit_message('workflow_started', {
                'execution_id': execution_id,
                'workflow_id': workflow_id
            })
            
            execution['status'] = WorkflowStatus.RUNNING
            
            # Execute workflow steps
            result = await self._execute_workflow_steps(workflow, execution, inputs)
            
            execution['status'] = WorkflowStatus.COMPLETED
            execution['outputs'] = result
            execution['end_time'] = datetime.now().isoformat()
            
            await self._emit_message('workflow_completed', {
                'execution_id': execution_id,
                'outputs': result
            })
            
            return execution
            
        except Exception as e:
            execution['status'] = WorkflowStatus.FAILED
            execution['errors'].append(str(e))
            execution['end_time'] = datetime.now().isoformat()
            
            await self._emit_message('workflow_failed', {
                'execution_id': execution_id,
                'error': str(e)
            })
            
            raise
        finally:
            # Move to history
            self.workflow_history.append(execution)
            if execution_id in self.active_workflows:
                del self.active_workflows[execution_id]
    
    async def _execute_workflow_steps(self, workflow: Dict[str, Any], execution: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow steps in the correct order."""
        steps = workflow['steps']
        dependencies = workflow.get('dependencies', {})
        outputs = {}
        step_results = {}
        
        for i, step in enumerate(steps):
            agent_name = step['agent']
            action = step['action']
            
            # Check dependencies
            if agent_name in dependencies:
                for dep_agent in dependencies[agent_name]:
                    if dep_agent not in step_results:
                        raise ValueError(f"Dependency {dep_agent} not satisfied for {agent_name}")
            
            # Prepare step inputs
            step_inputs = self._prepare_step_inputs(inputs, step_results, step)
            
            # Execute step
            step_execution = {
                'step_index': i,
                'agent': agent_name,
                'action': action,
                'inputs': step_inputs,
                'start_time': datetime.now().isoformat(),
                'status': 'running'
            }
            
            execution['steps'].append(step_execution)
            
            try:
                await self._emit_message('step_started', {
                    'execution_id': execution['id'],
                    'step_index': i,
                    'agent': agent_name,
                    'action': action
                })
                
                # Execute agent task
                if agent_name in self.agents:
                    agent = self.agents[agent_name]
                    task = {
                        'type': action,
                        **step_inputs
                    }
                    
                    result = await agent.execute(task)
                    
                    step_execution['outputs'] = result
                    step_execution['status'] = 'completed'
                    step_execution['end_time'] = datetime.now().isoformat()
                    
                    step_results[agent_name] = result
                    outputs[f"{agent_name}_{action}"] = result
                    
                    await self._emit_message('step_completed', {
                        'execution_id': execution['id'],
                        'step_index': i,
                        'outputs': result
                    })
                    
                else:
                    raise ValueError(f"Agent {agent_name} not found")
                    
            except Exception as e:
                step_execution['status'] = 'failed'
                step_execution['error'] = str(e)
                step_execution['end_time'] = datetime.now().isoformat()
                
                await self._emit_message('step_failed', {
                    'execution_id': execution['id'],
                    'step_index': i,
                    'error': str(e)
                })
                
                raise
        
        return outputs
    
    def _prepare_step_inputs(self, workflow_inputs: Dict[str, Any], step_results: Dict[str, Any], step: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare inputs for a workflow step."""
        inputs = {}
        
        # Add workflow inputs
        inputs.update(workflow_inputs)
        
        # Add outputs from previous steps
        agent_name = step['agent']
        action = step['action']
        
        if action == 'analyze_api':
            inputs['api_spec'] = workflow_inputs.get('api_spec', {})
            
        elif action == 'generate_server':
            if 'analyzer' in step_results:
                inputs['mcp_specification'] = step_results['analyzer'].get('mcp_specification', {})
            inputs['server_config'] = workflow_inputs.get('server_config', {})
            
        elif action == 'validate_server':
            if 'generator' in step_results:
                inputs['server_path'] = step_results['generator'].get('output_path', '')
            else:
                inputs['server_path'] = workflow_inputs.get('server_path', '')
            inputs['validation_config'] = workflow_inputs.get('validation_config', {})
            
        elif action == 'refine_server':
            if 'validator' in step_results:
                inputs['validation_results'] = step_results['validator']
            if 'generator' in step_results:
                inputs['server_path'] = step_results['generator'].get('output_path', '')
        
        return inputs
    
    async def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow execution."""
        if execution_id in self.active_workflows:
            return self.active_workflows[execution_id]
        
        # Check history
        for execution in self.workflow_history:
            if execution['id'] == execution_id:
                return execution
        
        return None
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List available workflow templates."""
        return [
            {
                'id': workflow_id,
                'name': workflow['name'],
                'description': workflow['description'],
                'steps': len(workflow['steps'])
            }
            for workflow_id, workflow in self.workflows.items()
        ]
    
    async def list_active_workflows(self) -> List[Dict[str, Any]]:
        """List currently active workflow executions."""
        return [
            {
                'id': execution['id'],
                'workflow_id': execution['workflow_id'],
                'status': execution['status'].value,
                'start_time': execution['start_time'],
                'current_step': len(execution['steps'])
            }
            for execution in self.active_workflows.values()
        ]
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow."""
        if execution_id in self.active_workflows:
            execution = self.active_workflows[execution_id]
            execution['status'] = WorkflowStatus.CANCELLED
            execution['end_time'] = datetime.now().isoformat()
            
            await self._emit_message('workflow_cancelled', {
                'execution_id': execution_id
            })
            
            # Move to history
            self.workflow_history.append(execution)
            del self.active_workflows[execution_id]
            
            return True
        
        return False
    
    async def create_custom_workflow(self, workflow_config: Dict[str, Any]) -> str:
        """Create a custom workflow from configuration."""
        workflow_id = f"custom_{datetime.now().timestamp()}"
        
        # Validate workflow configuration
        required_fields = ['name', 'description', 'steps']
        for field in required_fields:
            if field not in workflow_config:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate steps
        for step in workflow_config['steps']:
            if 'agent' not in step or 'action' not in step:
                raise ValueError("Each step must have 'agent' and 'action' fields")
            
            if step['agent'] not in self.agents:
                raise ValueError(f"Unknown agent: {step['agent']}")
        
        # Register workflow
        self.workflows[workflow_id] = workflow_config
        
        return workflow_id
    
    async def _handle_agent_message(self, topic: str, message: Dict[str, Any]):
        """Handle messages from sub-agents."""
        # Extract agent name from topic
        agent_name = topic.split('.')[0]
        
        # Forward message with orchestrator context
        await self._emit_message(f"agent_{agent_name}_message", {
            'agent': agent_name,
            'original_topic': topic,
            'message': message
        })
    
    async def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent."""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            return {
                'name': agent_name,
                'status': 'active',
                'last_activity': getattr(agent, 'last_activity', None),
                'config': agent.config
            }
        
        return None
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestrator task."""
        task_type = task.get('type', 'execute_workflow')
        
        if task_type == 'execute_workflow':
            workflow_id = task.get('workflow_id', '')
            inputs = task.get('inputs', {})
            return await self.execute_workflow(workflow_id, inputs)
            
        elif task_type == 'get_workflow_status':
            execution_id = task.get('execution_id', '')
            return await self.get_workflow_status(execution_id)
            
        elif task_type == 'list_workflows':
            return await self.list_workflows()
            
        elif task_type == 'list_active_workflows':
            return await self.list_active_workflows()
            
        elif task_type == 'cancel_workflow':
            execution_id = task.get('execution_id', '')
            return await self.cancel_workflow(execution_id)
            
        elif task_type == 'create_custom_workflow':
            workflow_config = task.get('workflow_config', {})
            return await self.create_custom_workflow(workflow_config)
            
        else:
            raise ValueError(f"Unknown task type: {task_type}")

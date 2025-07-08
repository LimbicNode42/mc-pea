"""Base agent class for MC-PEA AI agents."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from anthropic import Anthropic
from crewai import Agent, Task
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for an AI agent."""
    
    name: str = Field(..., description="Agent name")
    role: str = Field(..., description="Agent role")
    goal: str = Field(..., description="Agent goal")
    backstory: str = Field(..., description="Agent backstory")
    max_iterations: int = Field(default=5, description="Maximum iterations")
    verbose: bool = Field(default=True, description="Enable verbose logging")
    temperature: float = Field(default=0.7, description="LLM temperature")


class AgentMessage(BaseModel):
    """Message structure for inter-agent communication."""
    
    sender: str = Field(..., description="Sender agent name")
    recipient: str = Field(..., description="Recipient agent name")
    message_type: str = Field(..., description="Message type")
    content: Dict[str, Any] = Field(..., description="Message content")
    timestamp: float = Field(..., description="Message timestamp")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")


class AgentResult(BaseModel):
    """Result from agent execution."""
    
    success: bool = Field(..., description="Execution success")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    error: Optional[str] = Field(None, description="Error message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseAgent(ABC):
    """Base class for all MC-PEA AI agents."""
    
    def __init__(
        self,
        config: AgentConfig,
        anthropic_client: Optional[Anthropic] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the base agent.
        
        Args:
            config: Agent configuration
            anthropic_client: Anthropic client instance
            logger: Logger instance
        """
        self.config = config
        self.anthropic_client = anthropic_client
        self.logger = logger or logging.getLogger(f"agent.{config.name}")
        
        # Agent state
        self.is_running = False
        self.current_task = None
        self.message_queue = asyncio.Queue()
        
        # Initialize CrewAI agent
        self._crew_agent = self._create_crew_agent()
        
        self.logger.info(f"Initialized agent: {config.name}")
    
    def _create_crew_agent(self) -> Agent:
        """Create CrewAI agent instance."""
        return Agent(
            role=self.config.role,
            goal=self.config.goal,
            backstory=self.config.backstory,
            verbose=self.config.verbose,
            max_iter=self.config.max_iterations,
            llm=self.anthropic_client,
            tools=self.get_tools(),
        )
    
    @abstractmethod
    def get_tools(self) -> List[Any]:
        """Get tools available to this agent.
        
        Returns:
            List of tools for the agent
        """
        pass
    
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> AgentResult:
        """Process an incoming message.
        
        Args:
            message: Incoming message
            
        Returns:
            Processing result
        """
        pass
    
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> AgentResult:
        """Execute a specific task.
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        pass
    
    async def start(self) -> None:
        """Start the agent."""
        if self.is_running:
            self.logger.warning(f"Agent {self.config.name} is already running")
            return
        
        self.is_running = True
        self.logger.info(f"Starting agent: {self.config.name}")
        
        # Start message processing loop
        asyncio.create_task(self._message_loop())
    
    async def stop(self) -> None:
        """Stop the agent."""
        if not self.is_running:
            self.logger.warning(f"Agent {self.config.name} is not running")
            return
        
        self.is_running = False
        self.logger.info(f"Stopping agent: {self.config.name}")
    
    async def send_message(self, message: AgentMessage) -> None:
        """Send a message to the message queue.
        
        Args:
            message: Message to send
        """
        await self.message_queue.put(message)
        self.logger.debug(f"Queued message from {message.sender} to {message.recipient}")
    
    async def _message_loop(self) -> None:
        """Main message processing loop."""
        while self.is_running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(), timeout=1.0
                )
                
                # Process the message
                result = await self.process_message(message)
                
                if not result.success:
                    self.logger.error(
                        f"Failed to process message: {result.error}"
                    )
                
            except asyncio.TimeoutError:
                # No message received, continue
                continue
            except Exception as e:
                self.logger.error(f"Error in message loop: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status.
        
        Returns:
            Agent status information
        """
        return {
            "name": self.config.name,
            "role": self.config.role,
            "is_running": self.is_running,
            "current_task": self.current_task,
            "queue_size": self.message_queue.qsize(),
        }
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"<{self.__class__.__name__}(name='{self.config.name}', role='{self.config.role}')>"

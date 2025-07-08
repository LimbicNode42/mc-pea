"""MC-PEA AI Agents Package

A comprehensive framework for AI-powered MCP server generation and management.
"""

__version__ = "0.1.0"
__author__ = "MC-PEA Team"
__email__ = "team@mc-pea.com"

from .core.base_agent import BaseAgent
from .core.message_bus import MessageBus
from .core.state_manager import StateManager

__all__ = [
    "BaseAgent",
    "MessageBus", 
    "StateManager",
]

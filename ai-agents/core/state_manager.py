"""State manager for persistent agent state."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import aiofiles
from pydantic import BaseModel


class StateManagerConfig(BaseModel):
    """Configuration for state manager."""
    
    persistence_path: str = "./agent_state"
    auto_save_interval: float = 60.0  # seconds
    backup_count: int = 5
    compression: bool = False


class AgentState(BaseModel):
    """Agent state container."""
    
    agent_name: str
    state_data: Dict[str, Any]
    last_updated: float
    version: int = 1


class StateManager:
    """Manages persistent state for AI agents."""
    
    def __init__(
        self,
        config: StateManagerConfig,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the state manager.
        
        Args:
            config: State manager configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger("state_manager")
        
        # State storage
        self._agent_states: Dict[str, AgentState] = {}
        self._dirty_agents: set = set()
        
        # Ensure persistence directory exists
        self.persistence_path = Path(config.persistence_path)
        self.persistence_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"State manager initialized with path: {self.persistence_path}")
    
    async def load_agent_state(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Load state for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent state data or None if not found
        """
        # Check in-memory cache first
        if agent_name in self._agent_states:
            return self._agent_states[agent_name].state_data.copy()
        
        # Try to load from disk
        state_file = self.persistence_path / f"{agent_name}.json"
        
        if not state_file.exists():
            self.logger.debug(f"No state file found for agent: {agent_name}")
            return None
        
        try:
            async with aiofiles.open(state_file, 'r') as f:
                content = await f.read()
                state_data = json.loads(content)
                
                # Create AgentState object
                agent_state = AgentState(**state_data)
                self._agent_states[agent_name] = agent_state
                
                self.logger.info(f"Loaded state for agent: {agent_name}")
                return agent_state.state_data.copy()
                
        except Exception as e:
            self.logger.error(f"Failed to load state for agent {agent_name}: {e}")
            return None
    
    async def save_agent_state(
        self, agent_name: str, state_data: Dict[str, Any]
    ) -> None:
        """Save state for an agent.
        
        Args:
            agent_name: Name of the agent
            state_data: State data to save
        """
        import time
        
        # Update in-memory state
        if agent_name in self._agent_states:
            agent_state = self._agent_states[agent_name]
            agent_state.state_data = state_data.copy()
            agent_state.last_updated = time.time()
            agent_state.version += 1
        else:
            agent_state = AgentState(
                agent_name=agent_name,
                state_data=state_data.copy(),
                last_updated=time.time(),
            )
            self._agent_states[agent_name] = agent_state
        
        # Mark as dirty for persistence
        self._dirty_agents.add(agent_name)
        
        self.logger.debug(f"Updated state for agent: {agent_name}")
    
    async def persist_dirty_states(self) -> None:
        """Persist all dirty agent states to disk."""
        if not self._dirty_agents:
            return
        
        for agent_name in list(self._dirty_agents):
            await self._persist_agent_state(agent_name)
            self._dirty_agents.remove(agent_name)
        
        self.logger.debug(f"Persisted {len(self._dirty_agents)} dirty states")
    
    async def _persist_agent_state(self, agent_name: str) -> None:
        """Persist a single agent's state to disk.
        
        Args:
            agent_name: Name of the agent
        """
        if agent_name not in self._agent_states:
            return
        
        agent_state = self._agent_states[agent_name]
        state_file = self.persistence_path / f"{agent_name}.json"
        
        try:
            # Create backup if file exists
            if state_file.exists():
                await self._create_backup(state_file)
            
            # Write state to file
            state_dict = agent_state.dict()
            
            async with aiofiles.open(state_file, 'w') as f:
                await f.write(json.dumps(state_dict, indent=2))
            
            self.logger.debug(f"Persisted state for agent: {agent_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to persist state for agent {agent_name}: {e}")
    
    async def _create_backup(self, state_file: Path) -> None:
        """Create a backup of an existing state file.
        
        Args:
            state_file: Path to the state file
        """
        if not state_file.exists():
            return
        
        # Create backup filename
        backup_file = state_file.with_suffix(f".backup.{state_file.suffix}")
        
        try:
            # Copy the file
            async with aiofiles.open(state_file, 'r') as src:
                content = await src.read()
            
            async with aiofiles.open(backup_file, 'w') as dst:
                await dst.write(content)
            
            # Clean up old backups
            await self._cleanup_backups(state_file)
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {state_file}: {e}")
    
    async def _cleanup_backups(self, state_file: Path) -> None:
        """Clean up old backup files.
        
        Args:
            state_file: Path to the original state file
        """
        try:
            # Find all backup files for this agent
            backup_pattern = f"{state_file.stem}.backup.*"
            backup_files = list(self.persistence_path.glob(backup_pattern))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Remove excess backups
            for backup_file in backup_files[self.config.backup_count:]:
                backup_file.unlink()
                self.logger.debug(f"Removed old backup: {backup_file}")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup backups: {e}")
    
    async def delete_agent_state(self, agent_name: str) -> None:
        """Delete state for an agent.
        
        Args:
            agent_name: Name of the agent
        """
        # Remove from memory
        if agent_name in self._agent_states:
            del self._agent_states[agent_name]
        
        self._dirty_agents.discard(agent_name)
        
        # Remove from disk
        state_file = self.persistence_path / f"{agent_name}.json"
        if state_file.exists():
            state_file.unlink()
        
        self.logger.info(f"Deleted state for agent: {agent_name}")
    
    def get_agent_names(self) -> list[str]:
        """Get list of agents with saved state.
        
        Returns:
            List of agent names
        """
        # Get from memory
        memory_agents = set(self._agent_states.keys())
        
        # Get from disk
        disk_agents = set()
        for state_file in self.persistence_path.glob("*.json"):
            if not state_file.name.startswith(".") and ".backup." not in state_file.name:
                disk_agents.add(state_file.stem)
        
        return list(memory_agents.union(disk_agents))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get state manager statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "persistence_path": str(self.persistence_path),
            "agents_in_memory": len(self._agent_states),
            "dirty_agents": len(self._dirty_agents),
            "total_agents": len(self.get_agent_names()),
        }
    
    async def shutdown(self) -> None:
        """Shutdown the state manager and persist all dirty states."""
        self.logger.info("Shutting down state manager")
        await self.persist_dirty_states()
        self.logger.info("State manager shutdown complete")

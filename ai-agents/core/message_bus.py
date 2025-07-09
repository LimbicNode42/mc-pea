"""Message bus for inter-agent communication."""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel

from core.base_agent import AgentMessage


class MessageBusConfig(BaseModel):
    """Configuration for the message bus."""
    
    max_queue_size: int = 1000
    message_timeout: float = 30.0
    enable_persistence: bool = False
    persistence_path: Optional[str] = None


class MessageSubscription(BaseModel):
    """Message subscription for agents."""
    
    agent_name: str
    message_types: Set[str]
    callback: Callable[[AgentMessage], None]


class MessageBus:
    """Central message bus for agent communication."""
    
    def __init__(
        self,
        config: MessageBusConfig,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the message bus.
        
        Args:
            config: Message bus configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger("message_bus")
        
        # Message routing
        self._subscriptions: Dict[str, List[MessageSubscription]] = {}
        self._message_queue = asyncio.Queue(maxsize=config.max_queue_size)
        
        # State
        self._running = False
        self._stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
        }
        
        self.logger.info("Message bus initialized")
    
    async def start(self) -> None:
        """Start the message bus."""
        if self._running:
            self.logger.warning("Message bus is already running")
            return
        
        self._running = True
        self.logger.info("Starting message bus")
        
        # Start message processing loop
        asyncio.create_task(self._process_messages())
    
    async def stop(self) -> None:
        """Stop the message bus."""
        if not self._running:
            self.logger.warning("Message bus is not running")
            return
        
        self._running = False
        self.logger.info("Stopping message bus")
    
    def subscribe(
        self,
        agent_name: str,
        message_types: Set[str],
        callback: Callable[[AgentMessage], None],
    ) -> None:
        """Subscribe an agent to specific message types.
        
        Args:
            agent_name: Name of the subscribing agent
            message_types: Set of message types to subscribe to
            callback: Callback function for message delivery
        """
        subscription = MessageSubscription(
            agent_name=agent_name,
            message_types=message_types,
            callback=callback,
        )
        
        if agent_name not in self._subscriptions:
            self._subscriptions[agent_name] = []
        
        self._subscriptions[agent_name].append(subscription)
        
        self.logger.info(
            f"Agent {agent_name} subscribed to message types: {message_types}"
        )
    
    def unsubscribe(self, agent_name: str, message_types: Set[str]) -> None:
        """Unsubscribe an agent from message types.
        
        Args:
            agent_name: Name of the agent
            message_types: Message types to unsubscribe from
        """
        if agent_name not in self._subscriptions:
            return
        
        # Remove subscriptions for specified message types
        self._subscriptions[agent_name] = [
            sub for sub in self._subscriptions[agent_name]
            if not sub.message_types.intersection(message_types)
        ]
        
        # Remove agent if no subscriptions remain
        if not self._subscriptions[agent_name]:
            del self._subscriptions[agent_name]
        
        self.logger.info(
            f"Agent {agent_name} unsubscribed from message types: {message_types}"
        )
    
    async def send_message(self, message: AgentMessage) -> None:
        """Send a message through the bus.
        
        Args:
            message: Message to send
        """
        try:
            await asyncio.wait_for(
                self._message_queue.put(message),
                timeout=self.config.message_timeout,
            )
            self._stats["messages_sent"] += 1
            
            self.logger.debug(
                f"Queued message from {message.sender} to {message.recipient}"
            )
            
        except asyncio.TimeoutError:
            self._stats["messages_failed"] += 1
            self.logger.error(
                f"Failed to queue message: timeout after {self.config.message_timeout}s"
            )
            raise
    
    async def broadcast_message(
        self, message: AgentMessage, exclude: Optional[Set[str]] = None
    ) -> None:
        """Broadcast a message to all subscribers.
        
        Args:
            message: Message to broadcast
            exclude: Set of agent names to exclude from broadcast
        """
        exclude = exclude or set()
        
        for agent_name in self._subscriptions:
            if agent_name in exclude:
                continue
            
            # Create a copy of the message for each recipient
            broadcast_message = AgentMessage(
                sender=message.sender,
                recipient=agent_name,
                message_type=message.message_type,
                content=message.content,
                timestamp=message.timestamp,
                correlation_id=message.correlation_id,
            )
            
            await self.send_message(broadcast_message)
    
    async def _process_messages(self) -> None:
        """Main message processing loop."""
        while self._running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    self._message_queue.get(), timeout=1.0
                )
                
                # Deliver message to subscribers
                await self._deliver_message(message)
                
            except asyncio.TimeoutError:
                # No message received, continue
                continue
            except Exception as e:
                self.logger.error(f"Error in message processing loop: {e}")
    
    async def _deliver_message(self, message: AgentMessage) -> None:
        """Deliver a message to its recipient.
        
        Args:
            message: Message to deliver
        """
        delivered = False
        
        # Check for specific recipient
        if message.recipient in self._subscriptions:
            for subscription in self._subscriptions[message.recipient]:
                if message.message_type in subscription.message_types:
                    try:
                        # Call the callback function
                        if asyncio.iscoroutinefunction(subscription.callback):
                            await subscription.callback(message)
                        else:
                            subscription.callback(message)
                        
                        delivered = True
                        self._stats["messages_delivered"] += 1
                        
                        self.logger.debug(
                            f"Delivered message to {message.recipient}"
                        )
                        
                    except Exception as e:
                        self._stats["messages_failed"] += 1
                        self.logger.error(
                            f"Failed to deliver message to {message.recipient}: {e}"
                        )
        
        if not delivered:
            self._stats["messages_failed"] += 1
            self.logger.warning(
                f"No subscribers found for message to {message.recipient} "
                f"with type {message.message_type}"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "running": self._running,
            "queue_size": self._message_queue.qsize(),
            "subscriptions": {
                agent: len(subs) for agent, subs in self._subscriptions.items()
            },
            **self._stats,
        }
    
    def get_subscriptions(self) -> Dict[str, List[str]]:
        """Get current subscriptions.
        
        Returns:
            Dictionary mapping agent names to subscribed message types
        """
        return {
            agent: list(set().union(*(sub.message_types for sub in subs)))
            for agent, subs in self._subscriptions.items()
        }

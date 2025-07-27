"""
API Documentation Extraction Manager Agent

This agent acts as a manager in CrewAI's hierarchical process, coordinating
discovery and content extraction tasks across multiple specialized agents.
"""

from crewai import Agent, LLM
from core.agent_managers_config_loader import AgentConfigLoader
from dotenv import load_dotenv
import os

class ApiContentOrchestratorAgent(Agent):
    def __init__(self):
        load_dotenv()
        
        # Load agent configuration - update to use manager config
        agent_loader = AgentConfigLoader()
        config_data = agent_loader.get_agent_config("api_orchestrator")
        
        # Setup LLM similar to existing agents
        if "claude" in config_data.get("llm"):
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model=config_data.get("llm"),
                max_tokens=config_data.get("max_tokens"),
                temperature=config_data.get("temperature"),
                max_retries=config_data.get("max_retry_limit"),
            )
            print("Using Claude LLM for manager")
        elif "gemini" in config_data.get("llm"):
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini models")
            
            # Extract just the model name (remove the provider prefix)
            model_name = config_data.get("llm").replace("gemini/", "")
            
            # Use CrewAI's LLM class for Gemini models
            llm = LLM(
                model=f"gemini/{model_name}",
                api_key=google_api_key,
                max_tokens=config_data.get("max_input_tokens"),
                max_completion_tokens=config_data.get("max_output_tokens"),
                temperature=config_data.get("temperature"),
                reasoning_effort=config_data.get("reasoning_effort"),
            )
            print(f"Using Gemini LLM for manager: {model_name}")
        else:
            raise ValueError("Unsupported LLM type in configuration")
        
        super().__init__(
            role=config_data.get("role"),
            goal=config_data.get("goal"),
            backstory=config_data.get("backstory"),
            llm=llm,
            respect_context_window=config_data.get("respect_context_window"),
            cache=config_data.get("cache"),
            reasoning=config_data.get("reasoning"),
            max_iter=config_data.get("max_iterations"),
            max_retry_limit=config_data.get("max_retry_limit"),
            verbose=config_data.get("verbose")
        )
        
        self._config_data = config_data

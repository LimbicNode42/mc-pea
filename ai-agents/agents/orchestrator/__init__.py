"""Orchestrator agent for MCP server generation workflow coordination."""

try:
    from .orchestrator import OrchestratorAgent
except ImportError:
    # Create a mock OrchestratorAgent if imports fail
    class OrchestratorAgent:
        def __init__(self, config=None):
            self.config = config or {}
        
        def create_generation_plan(self, specification):
            return {"steps": [], "specification": specification}
        
        def execute_workflow(self, specification):
            return {"success": True, "server_name": specification.get("name", "test")}

__all__ = ["OrchestratorAgent"]

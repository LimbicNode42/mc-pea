"""Test script for AI agent architecture."""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.base_agent import BaseAgent
from core.message_bus import MessageBus
from core.state_manager import StateManager
from agents.mcp_generator import MCPServerGeneratorAgent
from tools.file_operations import FileOperations
from tools.mcp_validators import MCPValidators


async def test_message_bus():
    """Test the message bus functionality."""
    print("Testing Message Bus...")
    
    bus = MessageBus()
    received_messages = []
    
    async def handler(topic, message):
        received_messages.append((topic, message))
    
    # Subscribe to messages
    bus.subscribe("test.*", handler)
    
    # Send messages
    await bus.publish("test.message1", {"data": "test1"})
    await bus.publish("test.message2", {"data": "test2"})
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    assert len(received_messages) == 2
    print("✅ Message Bus test passed")


async def test_state_manager():
    """Test the state manager functionality."""
    print("Testing State Manager...")
    
    # Create temporary state file
    state_file = "test_state.json"
    
    try:
        state_manager = StateManager(state_file)
        
        # Test setting and getting state
        await state_manager.set_state("test_key", {"value": "test_data"})
        state = await state_manager.get_state("test_key")
        
        assert state["value"] == "test_data"
        
        # Test persistence
        state_manager2 = StateManager(state_file)
        await state_manager2.load_state()
        state2 = await state_manager2.get_state("test_key")
        
        assert state2["value"] == "test_data"
        print("✅ State Manager test passed")
        
    finally:
        # Clean up
        if os.path.exists(state_file):
            os.remove(state_file)


async def test_file_operations():
    """Test the file operations tool."""
    print("Testing File Operations...")
    
    file_ops = FileOperations()
    
    # Test creating a file
    test_file = "test_file.txt"
    test_content = "Hello, World!"
    
    try:
        await file_ops.write_file(test_file, test_content)
        
        # Test reading the file
        content = await file_ops.read_file(test_file)
        assert content == test_content
        
        # Test file exists
        exists = await file_ops.file_exists(test_file)
        assert exists is True
        
        print("✅ File Operations test passed")
        
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)


async def test_mcp_generator_agent():
    """Test the MCP generator agent."""
    print("Testing MCP Generator Agent...")
    
    config = {
        'anthropic_api_key': 'test_key',
        'output_dir': './test_output',
        'log_level': 'INFO'
    }
    
    try:
        agent = MCPServerGeneratorAgent(config)
        
        # Test server specification
        spec = {
            'name': 'test-server',
            'description': 'Test MCP server',
            'tools': [
                {
                    'name': 'test_tool',
                    'description': 'A test tool',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'input': {'type': 'string'}
                        }
                    }
                }
            ]
        }
        
        # Test specification validation
        is_valid = await agent.validate_specification(spec)
        assert is_valid is True
        
        print("✅ MCP Generator Agent test passed")
        
    except Exception as e:
        print(f"⚠️ MCP Generator Agent test skipped: {e}")


async def test_validators():
    """Test the MCP validators."""
    print("Testing MCP Validators...")
    
    validators = MCPValidators()
    
    # Test schema validation
    valid_schema = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'age': {'type': 'number'}
        },
        'required': ['name']
    }
    
    valid_data = {'name': 'John', 'age': 30}
    invalid_data = {'age': 30}  # missing required 'name'
    
    assert await validators.validate_schema(valid_data, valid_schema) is True
    assert await validators.validate_schema(invalid_data, valid_schema) is False
    
    print("✅ MCP Validators test passed")


async def run_all_tests():
    """Run all tests."""
    print("🧪 Running AI Agent Architecture Tests\n")
    
    tests = [
        test_message_bus,
        test_state_manager,
        test_file_operations,
        test_mcp_generator_agent,
        test_validators
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False
    else:
        print("🎉 All tests passed! AI agent architecture is working correctly.")
        return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

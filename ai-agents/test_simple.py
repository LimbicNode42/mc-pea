"""Simple test runner for AI agent components."""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from core.message_bus import MessageBus, MessageBusConfig
    from core.state_manager import StateManager, StateManagerConfig
    from tools.file_operations import FileOperations
    from tools.mcp_validators import MCPValidator
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


async def test_message_bus():
    """Test the message bus functionality."""
    print("Testing Message Bus...")
    
    config = MessageBusConfig()
    bus = MessageBus(config)
    
    # Start the bus
    await bus.start()
    
    received_messages = []
    
    async def handler(message):
        received_messages.append(message)
    
    # Subscribe to messages
    bus.subscribe("test_agent", {"test.message"}, handler)
    
    # Send messages
    from core.base_agent import AgentMessage
    msg1 = AgentMessage(type="test.message", content={"data": "test1"})
    msg2 = AgentMessage(type="test.message", content={"data": "test2"})
    
    await bus.send_message(msg1)
    await bus.send_message(msg2)
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    # Stop the bus
    await bus.stop()
    
    assert len(received_messages) == 2
    print("✅ Message Bus test passed")


async def test_state_manager():
    """Test the state manager functionality."""
    print("Testing State Manager...")
    
    # Create temporary state file
    state_file = "test_state.json"
    
    try:
        config = StateManagerConfig(persistence_path=state_file)
        state_manager = StateManager(config)
        
        # Test setting and getting state
        await state_manager.set_state("test_key", {"value": "test_data"})
        state = await state_manager.get_state("test_key")
        
        assert state["value"] == "test_data"
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
        exists = file_ops.file_exists(test_file)  # This is sync, not async
        assert exists is True
        
        print("✅ File Operations test passed")
        
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)


async def test_validators():
    """Test the MCP validators."""
    print("Testing MCP Validators...")
    
    validators = MCPValidator()
    
    # Test tool schema validation
    valid_tool_schema = {
        'name': 'test_tool',
        'description': 'A test tool',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'input': {'type': 'string'}
            },
            'required': ['input']
        }
    }
    
    # Test if the tool schema is valid
    result = await validators.validate_tool_schema(valid_tool_schema)
    assert result.is_valid is True
    
    print("✅ MCP Validators test passed")


async def run_tests():
    """Run all tests."""
    print("🧪 Running AI Agent Component Tests\n")
    
    tests = [
        test_message_bus,
        test_state_manager,
        test_file_operations,
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
        print("🎉 All tests passed! Core AI agent components are working correctly.")
        return True


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)

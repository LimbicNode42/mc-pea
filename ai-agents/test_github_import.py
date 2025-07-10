try:
    from agents.github_agent import GitHubAgent
    import os
    
    # Set a test token to avoid validation errors
    os.environ['GITHUB_PERSONAL_ACCESS_TOKEN'] = 'test-token'
    
    agent = GitHubAgent()
    print("✅ GitHub agent instance created successfully")
    print(f"Agent role: {agent.config.role}")
    print(f"Agent goal: {agent.config.goal}")
    
    # Test a method
    validation = agent.validate_github_access()
    print(f"GitHub validation: {validation.get('success', False)}")
    
except Exception as e:
    print(f"❌ Instance creation failed: {e}")
    import traceback
    traceback.print_exc()

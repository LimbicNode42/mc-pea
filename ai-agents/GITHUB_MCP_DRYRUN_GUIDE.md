# GitHub MCP Server Dry-Run Testing Guide

## Overview

This document provides comprehensive guidance for safely testing the GitHub MCP server and GitHub Agent integration without creating or modifying actual repositories.

## 🛡️ Safety Features Discovered

### 1. Read-Only Mode
The GitHub MCP server supports a `--read-only` flag that restricts operations to safe, non-destructive actions:

```bash
./github-mcp-server.exe --read-only stdio
```

### 2. Toolset Filtering
You can limit which tools are available using the `--toolsets` parameter:

```bash
./github-mcp-server.exe --read-only --toolsets context,users stdio
```

### 3. Available Safe Toolsets

| Toolset | Tools Available | Safety Level |
|---------|----------------|--------------|
| `context` | `get_me` | ✅ Safe - user info only |
| `users` | `search_users` | ✅ Safe - search only |
| `notifications` | `list_notifications`, `get_notification_details` | ✅ Safe - read notifications |
| `repos` (read-only) | `get_file_contents`, `list_branches`, `search_repositories`, etc. | ✅ Safe - read operations only |

## 🧪 Test Scripts Created

### 1. Basic Dry-Run Test (`test_github_mcp_dryrun.py`)
- Validates agent MCP dependencies
- Tests server binary availability
- Confirms read-only mode functionality
- Provides safety recommendations

### 2. Advanced Safe Testing (`test_github_mcp_advanced.py`)
- Tests multiple toolset combinations
- Validates read-only enforcement
- Tests proper MCP SDK patterns
- Comprehensive safety validation

### 3. Agent Integration Test (`test_github_agent_integration.py`)
- Tests GitHub Agent awareness of MCP dependencies
- Validates agent-to-server integration
- Tests fallback behavior
- Requires valid GitHub token for full testing

## 🎯 Testing Progression

### Phase 1: No Token Required
1. Server binary validation
2. Read-only mode testing
3. Toolset filtering validation
4. MCP protocol compliance

### Phase 2: Test Token Required
1. Basic context operations (`get_me`)
2. User search operations
3. Notification listing
4. Repository read operations

### Phase 3: Production Token Required
1. Full repository operations
2. Issue management
3. Pull request operations
4. Write operations (with extreme caution)

## 🔧 Command Examples

### Safe Testing Commands
```bash
# Basic read-only mode
./github-mcp-server.exe --read-only stdio

# Context and user operations only
./github-mcp-server.exe --read-only --toolsets context,users stdio

# Repository read operations
./github-mcp-server.exe --read-only --toolsets repos stdio

# With logging for debugging
./github-mcp-server.exe --read-only --log-file test.log --toolsets context stdio
```

### Validation Commands
```bash
# Check server help and options
./github-mcp-server.exe --help

# Test server responsiveness
./github-mcp-server.exe --version

# List available toolsets (documentation needed)
./github-mcp-server.exe --help
```

## 📊 Test Results Summary

### ✅ What Works
- Read-only mode properly restricts write operations
- Toolset filtering effectively limits available tools
- MCP protocol compliance is correct
- Server initialization and tool listing work properly
- Agent correctly reports MCP dependencies

### ⚠️ What Requires GitHub Token
- Actual API calls to GitHub
- User context retrieval
- Repository operations
- Full agent functionality testing

### ❌ What's Not Available
- Write operations in read-only mode (by design)
- Full testing without authentication
- Real repository operations without valid permissions

## 🛡️ Safety Guidelines

### DO:
- Always start with `--read-only` flag
- Test with minimal permission tokens
- Use dedicated test repositories
- Monitor GitHub API rate limits
- Log operations for debugging
- Start with safe toolsets (context, users)

### DON'T:
- Test write operations on production repositories
- Use production tokens for initial testing
- Skip read-only validation
- Test without understanding rate limits
- Assume all operations are safe

## 🔄 Integration with AI Agents

### Agent MCP Dependencies
The GitHub Agent correctly reports its dependencies:
```json
{
  "name": "github-mcp-server",
  "package": "github-mcp-server",
  "required": true,
  "status": "official",
  "docker_required": false,
  "fallback_available": false
}
```

### Streamlit Dashboard Integration
The dashboard displays:
- MCP dependency status
- Docker requirements (none for GitHub MCP)
- Fallback availability
- Installation instructions

## 🚀 Next Steps

### Immediate
1. Set up test GitHub token for validation
2. Create dedicated test repository
3. Validate agent operations with real API calls
4. Test agent orchestration workflows

### Future
1. Implement agent caching for rate limit optimization
2. Add batch operations for efficiency
3. Create agent-specific test suites
4. Implement monitoring and alerting

## 📝 Configuration Files

### Environment Variables
```bash
# Required for full testing
GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here

# Optional for enhanced testing
GITHUB_HOST=github.com  # For GitHub Enterprise
```

### MCP Configuration (`.vscode/mcp.json`)
```json
{
  "servers": {
    "github-local": {
      "command": "d:/HobbyProjects/mc-pea/github-mcp-server.exe",
      "args": ["--read-only", "stdio"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
      }
    }
  }
}
```

## 🔍 Troubleshooting

### Common Issues
1. **Server not found**: Check binary path and build status
2. **Token errors**: Verify environment variable setting
3. **Permission denied**: Check token permissions and repository access
4. **Rate limiting**: Implement delays and monitor usage
5. **Protocol errors**: Validate MCP client implementation

### Debug Commands
```bash
# Enable detailed logging
./github-mcp-server.exe --read-only --enable-command-logging --log-file debug.log stdio

# Test specific toolset
./github-mcp-server.exe --read-only --toolsets context stdio

# Check server capabilities
./github-mcp-server.exe --help
```

## 📚 References

- [GitHub MCP Server Repository](https://github.com/github/github-mcp-server)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [VS Code MCP Extension](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)

## 🎉 Success Criteria

A successful dry-run test should:
1. ✅ Server starts in read-only mode
2. ✅ MCP protocol initialization succeeds
3. ✅ Tools list correctly in filtered mode
4. ✅ Write operations are properly restricted
5. ✅ Agent reports correct dependencies
6. ✅ No destructive operations possible

This comprehensive testing approach ensures safe validation of the GitHub MCP server integration while protecting against accidental repository modifications.

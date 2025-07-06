# Getting Started: GitHub MCP Server Setup

## Prerequisites

Make sure you have these installed:
- Node.js (LTS version)
- Git
- A GitHub account with a Personal Access Token

## Step 1: Install the GitHub MCP Server

```bash
# Clone the official MCP servers repository
git clone https://github.com/modelcontextprotocol/servers.git
cd servers/src/github

# Install dependencies
npm install

# Build the server
npm run build
```

## Step 2: Create GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read org and team membership)
   - `read:user` (Read user profile data)
4. Copy the token (you'll need it for configuration)

## Step 3: Configure the Server

Create a configuration file for the GitHub MCP server:

```json
{
  "mcpServers": {
    "github": {
      "command": "node",
      "args": ["path/to/servers/src/github/dist/index.js"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

## Step 4: Test the Server

```bash
# Run the server directly for testing
cd servers/src/github
GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here npm start

# Or run with specific configuration
node dist/index.js
```

## Step 5: Verify Functionality

The GitHub MCP server provides these tools:
- `create_repository` - Create a new repository
- `get_file` - Get file contents from a repository
- `push_files` - Push files to a repository
- `create_or_update_file` - Create or update a single file
- `search_repositories` - Search for repositories
- `create_issue` - Create an issue
- `create_pull_request` - Create a pull request
- `fork_repository` - Fork a repository
- `create_branch` - Create a new branch

## Troubleshooting

### Common Issues:
1. **Token permissions**: Make sure your GitHub token has the right scopes
2. **Network access**: Ensure you can reach github.com
3. **Node.js version**: Use Node.js LTS (18+ recommended)

### Testing Connection:
```bash
# Test if the server can authenticate
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

## Next Steps

Once the GitHub MCP server is working:
1. Test basic operations (create repo, read files)
2. Understand the MCP protocol flow
3. Use this as a template for building the Keycloak MCP server
4. Integrate with mc-pea conductor system

## Configuration for Claude Desktop

If you want to test with Claude Desktop, add this to your config:

```json
{
  "mcpServers": {
    "github": {
      "command": "node",
      "args": ["D:\\HobbyProjects\\mc-pea\\servers\\src\\github\\dist\\index.js"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

The config file location:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

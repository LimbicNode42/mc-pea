# MC-PEA MCP Server Management Strategy

> **Objective**: Create a hybrid monorepo structure that allows independent development and publication while enabling centralized orchestration

## 🏗️ **Recommended Architecture: Hybrid Monorepo**

### **Structure**:
```
mc-pea/
├── package.json                    # Workspace root with shared dependencies
├── packages/
│   ├── core/                       # MC-PEA orchestrator engine
│   │   ├── src/
│   │   │   ├── generators/         # MCP server generators
│   │   │   ├── orchestrator/       # Multi-server coordination
│   │   │   └── templates/          # Server templates
│   │   └── package.json
│   ├── auth-mcp-server/            # Auth MCP server (imported/generated)
│   │   ├── src/
│   │   ├── package.json            # Independent publishable package
│   │   └── README.md
│   ├── database-mcp-server/        # Database MCP server
│   └── storage-mcp-server/         # File storage MCP server
├── tools/
│   ├── deployment/                 # Deployment scripts
│   ├── testing/                    # Cross-server testing
│   └── dev-server/                 # Local development orchestration
└── docs/
    └── orchestration/              # How servers work together
```

### **Benefits**:
1. **Independent Publishing**: Each server can be published to NPM independently
2. **Shared Dependencies**: Common packages managed at root level
3. **Cross-Server Development**: Easy to test server interactions
4. **Centralized Orchestration**: MC-PEA core can manage all servers
5. **Easy Import**: Can import existing servers as packages

## 🔧 **Implementation Steps**

### **Step 1: Set Up Workspace Root**
```json
{
  "name": "mc-pea-ecosystem",
  "version": "1.0.0",
  "private": true,
  "workspaces": [
    "packages/*"
  ],
  "scripts": {
    "build:all": "npm run build --workspaces",
    "test:all": "npm run test --workspaces", 
    "dev:orchestrator": "node tools/dev-server/start.js",
    "publish:servers": "npm run publish --workspaces --if-present"
  },
  "devDependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "typescript": "^5.0.0",
    "concurrently": "^8.0.0"
  }
}
```

### **Step 2: Import Existing Auth Server**
```bash
# Method 1: Copy existing auth server
cp -r /d/HobbyProjects/mike-cok-protracting/auth-mcp-server packages/

# Method 2: Git subtree (if it's in a separate repo)
git subtree add --prefix=packages/auth-mcp-server \
  https://github.com/your-org/auth-mcp-server.git main

# Method 3: Clone and reorganize
git clone https://github.com/your-org/auth-mcp-server.git temp-auth
mv temp-auth packages/auth-mcp-server
rm -rf temp-auth/.git
```

### **Step 3: Create Orchestration Layer**
```typescript
// packages/core/src/orchestrator/ServerManager.ts
export class MCPServerManager {
  private servers = new Map<string, MCPServerInstance>();
  
  async loadServer(serverPath: string, config: ServerConfig): Promise<void> {
    const server = await import(serverPath);
    const instance = new server.default(config);
    this.servers.set(config.name, instance);
  }
  
  async startAllServers(): Promise<void> {
    for (const [name, server] of this.servers) {
      await server.start();
      console.log(`Started ${name} MCP server`);
    }
  }
  
  async routeRequest(serverName: string, request: any): Promise<any> {
    const server = this.servers.get(serverName);
    if (!server) {
      throw new Error(`Server ${serverName} not found`);
    }
    return server.handleRequest(request);
  }
  
  async orchestrateWorkflow(workflow: WorkflowDefinition): Promise<any> {
    // Coordinate multiple servers for complex operations
    const results = [];
    for (const step of workflow.steps) {
      const result = await this.routeRequest(step.server, step.request);
      results.push(result);
    }
    return results;
  }
}
```

### **Step 4: Development Orchestration**
```javascript
// tools/dev-server/start.js
const { MCPServerManager } = require('../../packages/core/dist/orchestrator/ServerManager');

async function startDevelopmentEnvironment() {
  const manager = new MCPServerManager();
  
  // Load all servers from packages
  await manager.loadServer('../../packages/auth-mcp-server', {
    name: 'auth',
    port: 3001,
    config: { /* auth config */ }
  });
  
  await manager.loadServer('../../packages/database-mcp-server', {
    name: 'database', 
    port: 3002,
    config: { /* db config */ }
  });
  
  // Start orchestration server
  await manager.startAllServers();
  console.log('🚀 MC-PEA ecosystem running in development mode');
}

startDevelopmentEnvironment().catch(console.error);
```

## 🔄 **Server Lifecycle Management**

### **Import Existing Server**:
```bash
# Import your existing auth server
npm run import-server -- --source=/d/HobbyProjects/mike-cok-protracting/auth-mcp-server --name=auth
```

### **Generate New Server**:
```bash
# Generate new MCP server from template
npm run generate-server -- --type=storage --name=file-storage
```

### **Publish Individual Server**:
```bash
# Publish just the auth server
cd packages/auth-mcp-server
npm publish

# Or publish all servers
npm run publish:servers
```

### **Local Development**:
```bash
# Run entire ecosystem locally
npm run dev:orchestrator

# Run specific server for testing
cd packages/auth-mcp-server
npm run dev
```

## 🎯 **Configuration Management**

### **Shared Configuration**:
```typescript
// packages/core/src/config/ecosystem.ts
export interface EcosystemConfig {
  servers: {
    [serverName: string]: {
      enabled: boolean;
      development: ServerConfig;
      production: ServerConfig;
    };
  };
  orchestration: {
    workflows: WorkflowDefinition[];
    dependencies: ServerDependency[];
  };
}
```

### **Server Independence**:
```json
// packages/auth-mcp-server/package.json
{
  "name": "@mc-pea/auth-mcp-server",
  "version": "1.0.0",
  "main": "dist/index.js",
  "bin": {
    "auth-mcp-server": "dist/cli.js"
  },
  "scripts": {
    "build": "tsc",
    "dev": "tsx src/index.ts",
    "publish": "npm publish --access public"
  }
}
```

## 🚀 **Next Steps**

1. **Set up workspace structure**
2. **Import your existing auth server**
3. **Create basic orchestration layer**
4. **Test local development environment**
5. **Add server generation capabilities**

Would you like me to start implementing this structure? I can:
1. Set up the workspace package.json
2. Create the basic orchestration framework  
3. Help import your existing auth server
4. Build the development orchestration tools

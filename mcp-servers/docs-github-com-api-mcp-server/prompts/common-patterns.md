# Common MCP Implementation Patterns

This document contains proven, reusable patterns for common MCP server implementations.

## 🔧 Tool Implementation Patterns

### 1. API Client Tool Pattern

For tools that interact with external APIs:

```typescript
// Tool Definition
export const apiToolDefinitions = {
  call_api: {
    name: 'call_api',
    description: 'Make HTTP requests to external APIs',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'API endpoint URL' },
        method: { type: 'string', enum: ['GET', 'POST', 'PUT', 'DELETE'] },
        headers: { type: 'object', description: 'Request headers' },
        body: { type: 'string', description: 'Request body (JSON string)' }
      },
      required: ['url', 'method']
    }
  }
};

// Tool Handler with Session-Aware Client
export const apiToolHandlers = {
  call_api: async (args: any, sessionId: string) => {
    const session = getSession(sessionId);
    
    try {
      const response = await session.httpClient.request({
        url: args.url,
        method: args.method,
        headers: args.headers,
        body: args.body
      });
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            status: response.status,
            headers: response.headers,
            data: response.data
          }, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text', text: `API Error: ${error.message}` }],
        isError: true
      };
    }
  }
};
```

### 2. Database Tool Pattern

For tools that interact with databases:

```typescript
// Tool Definition
export const dbToolDefinitions = {
  query_database: {
    name: 'query_database',
    description: 'Execute SQL queries against the database',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'SQL query to execute' },
        parameters: { type: 'array', description: 'Query parameters' }
      },
      required: ['query']
    }
  }
};

// Tool Handler with Connection Pooling
export const dbToolHandlers = {
  query_database: async (args: any, sessionId: string) => {
    const session = getSession(sessionId);
    
    try {
      const results = await session.dbClient.query(args.query, args.parameters);
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            rowCount: results.rowCount,
            rows: results.rows
          }, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Database Error: ${error.message}` }],
        isError: true
      };
    }
  }
};
```

### 3. File System Tool Pattern

For tools that interact with file systems:

```typescript
// Tool Definition
export const fsToolDefinitions = {
  read_file: {
    name: 'read_file',
    description: 'Read contents of a file',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'File path to read' },
        encoding: { type: 'string', enum: ['utf8', 'base64'], default: 'utf8' }
      },
      required: ['path']
    }
  }
};

// Tool Handler with Security Checks
export const fsToolHandlers = {
  read_file: async (args: any, sessionId: string) => {
    const session = getSession(sessionId);
    
    // Security: Validate file path
    if (!isPathAllowed(args.path, session.allowedPaths)) {
      return {
        content: [{ type: 'text', text: 'Error: Access denied to file path' }],
        isError: true
      };
    }
    
    try {
      const content = await fs.readFile(args.path, args.encoding || 'utf8');
      
      return {
        content: [{
          type: args.encoding === 'base64' ? 'image' : 'text',
          [args.encoding === 'base64' ? 'data' : 'text']: content
        }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text', text: `File Error: ${error.message}` }],
        isError: true
      };
    }
  }
};
```

## 📚 Resource Implementation Patterns

### 1. Dynamic Content Resource Pattern

For resources that provide dynamic content:

```typescript
// Resource Definition
export const dynamicResourceDefinitions = {
  'status': {
    uri: 'status://server',
    name: 'Server Status',
    description: 'Current server status and metrics',
    mimeType: 'application/json'
  }
};

// Resource Handler
export const dynamicResourceHandlers = {
  'status://server': async (sessionId: string) => {
    const session = getSession(sessionId);
    
    const status = {
      timestamp: new Date().toISOString(),
      sessionId,
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      connections: sessions.size
    };
    
    return {
      contents: [{
        uri: 'status://server',
        mimeType: 'application/json',
        text: JSON.stringify(status, null, 2)
      }]
    };
  }
};
```

### 2. File-Based Resource Pattern

For resources that serve file content:

```typescript
// Resource Definition
export const fileResourceDefinitions = {
  'config': {
    uri: 'file:///app/config.json',
    name: 'Application Configuration',
    description: 'Current application configuration',
    mimeType: 'application/json'
  }
};

// Resource Handler
export const fileResourceHandlers = {
  'file:///app/config.json': async (sessionId: string) => {
    try {
      const content = await fs.readFile('/app/config.json', 'utf8');
      
      return {
        contents: [{
          uri: 'file:///app/config.json',
          mimeType: 'application/json',
          text: content
        }]
      };
    } catch (error) {
      return {
        contents: [{
          uri: 'file:///app/config.json',
          mimeType: 'text/plain',
          text: `Error reading config: ${error.message}`
        }]
      };
    }
  }
};
```

## 🎯 Prompt Implementation Patterns

### 1. Contextual Prompt Pattern

For prompts that provide context-aware instructions:

```typescript
// Prompt Definition
export const contextualPromptDefinitions = {
  analyze_data: {
    name: 'analyze_data',
    description: 'Generate data analysis prompt with current context',
    arguments: [
      {
        name: 'dataset',
        description: 'Dataset identifier to analyze',
        required: true
      },
      {
        name: 'analysis_type',
        description: 'Type of analysis to perform',
        required: false
      }
    ]
  }
};

// Prompt Handler
export const contextualPromptHandlers = {
  analyze_data: async (args: any, sessionId: string) => {
    const session = getSession(sessionId);
    
    // Get dataset metadata
    const dataset = await session.dataClient.getDataset(args.dataset);
    
    const prompt = `
# Data Analysis Task

## Dataset: ${dataset.name}
- **Rows**: ${dataset.rowCount}
- **Columns**: ${dataset.columns.join(', ')}
- **Last Updated**: ${dataset.lastModified}

## Analysis Type: ${args.analysis_type || 'General'}

## Instructions:
1. Examine the dataset structure and content
2. Identify patterns, trends, and anomalies
3. Generate insights and recommendations
4. Create visualizations where appropriate

## Available Tools:
- query_database: Execute SQL queries
- generate_chart: Create data visualizations
- calculate_stats: Compute statistical measures

Please analyze the dataset and provide comprehensive insights.
`;

    return {
      description: `Data analysis prompt for ${dataset.name}`,
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: prompt
          }
        }
      ]
    };
  }
};
```

## 🔧 Session Management Patterns

### 1. Client Initialization Pattern

```typescript
// Session Data Interface
interface SessionData {
  sessionId: string;
  initialized: boolean;
  httpClient: HttpClient;
  dbClient: DatabaseClient;
  allowedPaths: string[];
  userContext: UserContext;
}

// Session Initialization
function initializeSession(sessionId: string): SessionData {
  return {
    sessionId,
    initialized: true,
    httpClient: new HttpClient({
      timeout: 30000,
      maxRetries: 3
    }),
    dbClient: new DatabaseClient({
      connectionString: process.env.DATABASE_URL,
      pool: { min: 1, max: 5 }
    }),
    allowedPaths: getAllowedPaths(),
    userContext: createUserContext(sessionId)
  };
}

// Session Cleanup
function cleanupSession(sessionId: string) {
  const session = sessions.get(sessionId);
  if (session) {
    session.dbClient?.close();
    session.httpClient?.destroy();
    sessions.delete(sessionId);
  }
}
```

### 2. Session State Management Pattern

```typescript
// State Storage
const sessions = new Map<string, SessionData>();
const sessionStates = new Map<string, any>();

// State Persistence
function saveSessionState(sessionId: string, state: any) {
  sessionStates.set(sessionId, {
    ...sessionStates.get(sessionId),
    ...state,
    lastUpdated: Date.now()
  });
}

function getSessionState(sessionId: string) {
  return sessionStates.get(sessionId) || {};
}

// Cleanup Expired Sessions
setInterval(() => {
  const expiredTime = Date.now() - (30 * 60 * 1000); // 30 minutes
  
  for (const [sessionId, state] of sessionStates) {
    if (state.lastUpdated < expiredTime) {
      cleanupSession(sessionId);
      sessionStates.delete(sessionId);
    }
  }
}, 5 * 60 * 1000); // Check every 5 minutes
```

## 🔐 Security Patterns

### 1. Input Validation Pattern

```typescript
// Schema Validation
import Ajv from 'ajv';
const ajv = new Ajv();

function validateToolInput(toolName: string, input: any): boolean {
  const schema = toolDefinitions[toolName]?.inputSchema;
  if (!schema) return false;
  
  const validate = ajv.compile(schema);
  return validate(input);
}

// Tool Wrapper with Validation
export function createSecureToolHandler(toolName: string, handler: Function) {
  return async (args: any, sessionId: string) => {
    // Input validation
    if (!validateToolInput(toolName, args)) {
      return {
        content: [{ type: 'text', text: 'Error: Invalid input parameters' }],
        isError: true
      };
    }
    
    // Rate limiting
    if (isRateLimited(sessionId, toolName)) {
      return {
        content: [{ type: 'text', text: 'Error: Rate limit exceeded' }],
        isError: true
      };
    }
    
    // Execute handler
    return await handler(args, sessionId);
  };
}
```

### 2. Access Control Pattern

```typescript
// Permission System
interface Permissions {
  tools: string[];
  resources: string[];
  maxRequestsPerMinute: number;
}

function getUserPermissions(sessionId: string): Permissions {
  const session = getSession(sessionId);
  // Determine permissions based on API key, user role, etc.
  return {
    tools: ['read_file', 'query_database'],
    resources: ['status://server'],
    maxRequestsPerMinute: 60
  };
}

// Authorization Check
function isAuthorized(sessionId: string, capability: string, type: 'tool' | 'resource'): boolean {
  const permissions = getUserPermissions(sessionId);
  return permissions[type + 's'].includes(capability);
}
```

## 📋 Monitoring Patterns

### 1. Structured Logging Pattern

```typescript
// Logger Setup
interface LogContext {
  sessionId: string;
  toolName?: string;
  resourceUri?: string;
  duration?: number;
  error?: string;
}

function log(level: string, message: string, context: LogContext) {
  console.log(JSON.stringify({
    timestamp: new Date().toISOString(),
    level,
    message,
    ...context
  }));
}

// Usage in Handlers
export const monitoredToolHandlers = {
  example_tool: async (args: any, sessionId: string) => {
    const startTime = Date.now();
    
    try {
      log('info', 'Tool execution started', { sessionId, toolName: 'example_tool' });
      
      const result = await executeToolLogic(args, sessionId);
      
      log('info', 'Tool execution completed', {
        sessionId,
        toolName: 'example_tool',
        duration: Date.now() - startTime
      });
      
      return result;
    } catch (error) {
      log('error', 'Tool execution failed', {
        sessionId,
        toolName: 'example_tool',
        duration: Date.now() - startTime,
        error: error.message
      });
      
      throw error;
    }
  }
};
```

### 2. Health Check Pattern

```typescript
// Health Check Resource
export const healthResourceDefinitions = {
  'health': {
    uri: 'health://check',
    name: 'Health Check',
    description: 'Server health and status information',
    mimeType: 'application/json'
  }
};

export const healthResourceHandlers = {
  'health://check': async (sessionId: string) => {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      sessions: sessions.size,
      checks: {
        database: await checkDatabaseHealth(),
        external_apis: await checkExternalAPIs(),
        file_system: await checkFileSystemAccess()
      }
    };
    
    const overallStatus = Object.values(health.checks).every(check => check === 'healthy')
      ? 'healthy'
      : 'unhealthy';
    
    return {
      contents: [{
        uri: 'health://check',
        mimeType: 'application/json',
        text: JSON.stringify({ ...health, status: overallStatus }, null, 2)
      }]
    };
  }
};
```

These patterns can be mixed and matched based on your specific MCP server requirements while maintaining protocol compliance.

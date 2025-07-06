/**
 * MCP Server Template - Main Entry Point
 * 
 * This is the CANONICAL REFERENCE implementation for MCP servers.
 * DO NOT modify this file without updating all dependent projects.
 * 
 * This file demonstrates:
 * - Proper MCP server initialization
 * - Session management with StreamableHTTPServerTransport
 * - API key authentication
 * - Environment variable configuration
 * - Error handling and graceful shutdown
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { randomUUID } from 'crypto';
import { registerToolsAndResources } from './registrations.js';

// Environment validation
const requiredEnvVars = ['API_KEY', 'PORT'];
const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
if (missingVars.length > 0) {
  console.error(`❌ Missing required environment variables: ${missingVars.join(', ')}`);
  console.error('Please create a .env file based on .env.example');
  process.exit(1);
}

// Configuration
const config = {
  port: parseInt(process.env.PORT || '3000'),
  apiKey: process.env.API_KEY!,
  nodeEnv: process.env.NODE_ENV || 'development',
  serverName: process.env.SERVER_NAME || 'mcp-server-template',
  serverVersion: process.env.SERVER_VERSION || '1.0.0',
};

// Session storage for stateful HTTP transport
interface SessionData {
  sessionId: string;
  initialized: boolean;
  createdAt: Date;
  // Add session-specific clients and data here
  // Example: httpClient: HttpClient;
  // Example: dbClient: DatabaseClient;
}

const sessions: Map<string, SessionData> = new Map();

/**
 * Initialize session-specific clients and data
 * This is called when a new session is created by the transport
 */
function initializeSession(sessionId: string): SessionData {
  console.error(`[${sessionId}] Initializing new session`);
  
  const session: SessionData = {
    sessionId,
    initialized: true,
    createdAt: new Date(),
    // Initialize session-specific clients here
    // httpClient: new HttpClient(),
    // dbClient: new DatabaseClient(),
  };
  
  sessions.set(sessionId, session);
  return session;
}

/**
 * Get session data, creating if it doesn't exist
 */
export function getSession(sessionId: string): SessionData {
  let session = sessions.get(sessionId);
  if (!session) {
    session = initializeSession(sessionId);
  }
  return session;
}

/**
 * API key validation
 * Checks both x-api-key and authorization headers
 */
function isValidApiKey(headers: Headers): boolean {
  const apiKey = headers.get('x-api-key') || 
                headers.get('authorization')?.replace('Bearer ', '');
  
  if (!apiKey) {
    console.error('No API key provided in request headers');
    return false;
  }
  
  const isValid = apiKey === config.apiKey;
  if (!isValid) {
    console.error('Invalid API key provided');
  }
  
  return isValid;
}

/**
 * Validate authentication for MCP requests
 * This function extracts headers from the request context
 */
export function validateAuthentication(request: any): boolean {
  // Extract headers from request context
  // The exact method may vary based on transport implementation
  const headers = request.headers || new Headers();
  return isValidApiKey(headers);
}

// Initialize MCP server
const server = new McpServer({
  name: config.serverName,
  version: config.serverVersion,
});

// Register all tools and resources
registerToolsAndResources(server);

// Configure HTTP transport with session management
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => randomUUID(),
  
  onsessioninitialized: (sessionId: string) => {
    console.error(`[${sessionId}] Session initialized`);
    // Session will be created on first access via getSession()
  },
  
  // Security configuration
  enableDnsRebindingProtection: config.nodeEnv === 'production',
  allowedHosts: config.nodeEnv === 'production' 
    ? (process.env.ALLOWED_HOSTS?.split(',') || [])
    : [], // Allow all hosts in development
});

// Graceful shutdown handling
process.on('SIGINT', async () => {
  console.error('🛑 Received SIGINT, shutting down gracefully...');
  
  // Cleanup sessions
  for (const [sessionId, session] of sessions) {
    console.error(`[${sessionId}] Cleaning up session`);
    // Cleanup session-specific resources
    // session.httpClient?.destroy();
    // session.dbClient?.close();
  }
  sessions.clear();
  
  process.exit(0);
});

// Start server
async function startServer() {
  try {
    await server.connect(transport);
    console.error(`🚀 ${config.serverName} v${config.serverVersion} running on port ${config.port}`);
    console.error(`📋 Environment: ${config.nodeEnv}`);
    console.error(`🔐 Authentication: ${config.apiKey ? 'Enabled' : 'Disabled'}`);
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

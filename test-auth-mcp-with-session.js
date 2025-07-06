#!/usr/bin/env node

/**
 * Test Auth MCP Server with proper session management using MCP SDK
 * This demonstrates how to properly connect to the auth MCP server
 * using the official MCP client transport
 */

// Load environment variables
import fs from 'fs';
import { randomUUID } from 'crypto';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

function loadEnvFile() {
  const envPath = '.env';
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    envContent.split('\n').forEach(line => {
      line = line.trim();
      if (line && !line.startsWith('#') && line.includes('=')) {
        const [key, ...valueParts] = line.split('=');
        if (key && valueParts.length > 0) {
          const value = valueParts.join('=').replace(/^["']|["']$/g, '');
          process.env[key] = value;
        }
      }
    });
  }
}

loadEnvFile();

const AUTH_MCP_URL = process.env.AUTH_MCP_URL;
const AUTH_MCP_API_KEY = process.env.AUTH_MCP_API_KEY;

if (!AUTH_MCP_URL || !AUTH_MCP_API_KEY) {
  console.error('❌ Missing required environment variables: AUTH_MCP_URL and AUTH_MCP_API_KEY');
  process.exit(1);
}

class AuthMCPClient {
  constructor(baseUrl, apiKey) {
    // Ensure baseUrl ends with / for proper URL joining
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl : baseUrl + '/';
    this.apiKey = apiKey;
    this.client = null;
    this.transport = null;
  }

  getUrl(endpoint) {
    return `${this.baseUrl}${endpoint}`;
  }

  async connect() {
    console.log('🔌 Creating MCP client transport...');
    
    const mcpUrl = this.getUrl('mcp');
    console.log(`   Base URL: ${this.baseUrl}`);
    console.log(`   MCP URL: ${mcpUrl}`);
    
    // Create the StreamableHTTPClientTransport with proper configuration
    // Headers should be passed via requestInit option
    this.transport = new StreamableHTTPClientTransport(new URL(mcpUrl), {
      requestInit: {
        headers: {
          'API_KEY': this.apiKey
        }
      }
    });

    console.log(`   Transport URL: ${mcpUrl}`);
    console.log(`   Transport Headers: API_KEY`);

    // Create the MCP Client
    this.client = new Client({
      name: 'test-auth-mcp-client',
      version: '1.0.0'
    }, {
      capabilities: {
        resources: {},
        tools: {}
      }
    });

    console.log('🚀 Connecting to MCP server...');
    
    // Connect the client to the transport
    await this.client.connect(this.transport);
    
    console.log('✅ MCP client connected successfully');
    console.log(`   Session ID: ${this.transport.sessionId || 'managed by transport'}`);
    
    return true;
  }

  async disconnect() {
    if (this.client) {
      console.log('🔌 Disconnecting MCP client...');
      await this.client.close();
      this.client = null;
      this.transport = null;
      console.log('✅ MCP client disconnected');
    }
  }

  async listResources() {
    if (!this.client) {
      throw new Error('Client not connected. Call connect() first.');
    }

    console.log('📋 Listing available resources...');
    
    const result = await this.client.listResources();
    
    console.log(`✅ Found ${result.resources?.length || 0} resources`);
    result.resources?.forEach(resource => {
      console.log(`   - ${resource.name}: ${resource.uri}`);
    });
    
    return result.resources;
  }

  async listTools() {
    if (!this.client) {
      throw new Error('Client not connected. Call connect() first.');
    }

    console.log('🔧 Listing available tools...');
    
    const result = await this.client.listTools();
    
    console.log(`✅ Found ${result.tools?.length || 0} tools`);
    result.tools?.forEach(tool => {
      console.log(`   - ${tool.name}: ${tool.description}`);
    });
    
    return result.tools;
  }

  async getResource(uri) {
    if (!this.client) {
      throw new Error('Client not connected. Call connect() first.');
    }

    console.log(`📄 Getting resource: ${uri}`);
    
    const result = await this.client.readResource({ uri });
    
    console.log(`✅ Resource retrieved successfully`);
    return result;
  }

  async callTool(name, arguments_) {
    if (!this.client) {
      throw new Error('Client not connected. Call connect() first.');
    }

    console.log(`🔧 Calling tool: ${name}`);
    
    const result = await this.client.callTool({ name, arguments: arguments_ });
    
    console.log(`✅ Tool executed successfully`);
    return result;
  }
}

async function main() {
  console.log('🔍 Auth MCP Server Test with MCP SDK Client');
  console.log('==========================================\n');

  // Test health endpoint first
  console.log('🏥 Testing health endpoint...');
  try {
    const healthResponse = await fetch(`${AUTH_MCP_URL}health`);
    const health = await healthResponse.json();
    console.log('✅ Health check passed:');
    console.log(`   Status: ${health.status}`);
    console.log(`   Authentication: ${health.authentication?.enabled ? 'ENABLED' : 'DISABLED'}`);
    console.log(`   Active Sessions: ${health.activeSessions}`);
    console.log('');
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
    process.exit(1);
  }

  // Create MCP client
  const client = new AuthMCPClient(AUTH_MCP_URL, AUTH_MCP_API_KEY);

  try {
    // Connect to the server (handles initialization automatically)
    await client.connect();
    console.log('');

    // List available resources
    const resources = await client.listResources();
    console.log('');

    // List available tools
    const tools = await client.listTools();
    console.log('');

    // Try to get a specific resource (example)
    if (resources && resources.length > 0) {
      try {
        console.log('📄 Trying to access first available resource...');
        await client.getResource(resources[0].uri);
      } catch (error) {
        console.log('ℹ️  Resource access failed (may require additional configuration):', error.message);
      }
      console.log('');
    }

    // Try to call a tool if available
    if (tools && tools.length > 0) {
      try {
        console.log('🔧 Trying to call first available tool...');
        // This will likely fail without proper arguments, but tests the call mechanism
        await client.callTool(tools[0].name, {});
      } catch (error) {
        console.log('ℹ️  Tool call failed (expected - may need specific arguments):', error.message);
      }
      console.log('');
    }

    console.log('🎉 MCP SDK client test completed successfully!');
    
    // Disconnect
    await client.disconnect();

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    // Ensure cleanup
    try {
      await client.disconnect();
    } catch (cleanupError) {
      // Ignore cleanup errors
    }
    
    process.exit(1);
  }
}

main().catch(console.error);

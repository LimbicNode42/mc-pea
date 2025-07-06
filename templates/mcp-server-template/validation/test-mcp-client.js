#!/usr/bin/env node

/**
 * MCP Server Validation Client (Template)
 * 
 * This is the CANONICAL REFERENCE implementation for validating MCP servers
 * using the official MCP SDK client transport.
 * 
 * DO NOT modify this file without updating all dependent projects.
 * 
 * This template demonstrates:
 * - Proper MCP SDK client usage
 * - StreamableHTTPClientTransport configuration
 * - Authentication header handling
 * - Environment variable configuration
 * - Comprehensive capability testing
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

const MCP_SERVER_URL = process.env.MCP_SERVER_URL || 'http://localhost:3000';
const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  console.error('❌ Missing required environment variable: API_KEY');
  process.exit(1);
}

class MCPServerValidator {
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
          'x-api-key': this.apiKey
        }
      }
    });

    console.log(`   Transport URL: ${mcpUrl}`);
    console.log(`   Transport Headers: x-api-key`);

    // Create the MCP Client
    this.client = new Client({
      name: 'mcp-server-validator',
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

  async listPrompts() {
    if (!this.client) {
      throw new Error('Client not connected. Call connect() first.');
    }

    console.log('📝 Listing available prompts...');
    
    try {
      const result = await this.client.listPrompts();
      
      console.log(`✅ Found ${result.prompts?.length || 0} prompts`);
      result.prompts?.forEach(prompt => {
        console.log(`   - ${prompt.name}: ${prompt.description}`);
      });
      
      return result.prompts;
    } catch (error) {
      console.log('ℹ️  Prompts not supported or not available');
      return [];
    }
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

  async getPrompt(name, arguments_) {
    if (!this.client) {
      throw new Error('Client not connected. Call connect() first.');
    }

    console.log(`📝 Getting prompt: ${name}`);
    
    try {
      const result = await this.client.getPrompt({ name, arguments: arguments_ });
      
      console.log(`✅ Prompt retrieved successfully`);
      return result;
    } catch (error) {
      console.log('ℹ️  Prompt not available or not supported');
      return null;
    }
  }
}

async function main() {
  console.log('🔍 MCP Server Validation with SDK Client');
  console.log('=======================================\n');

  // Test health endpoint first (if available)
  console.log('🏥 Testing health endpoint...');
  try {
    const healthUrl = `${MCP_SERVER_URL}${MCP_SERVER_URL.endsWith('/') ? '' : '/'}health`;
    const healthResponse = await fetch(healthUrl);
    const health = await healthResponse.json();
    console.log('✅ Health check passed:');
    console.log(`   Status: ${health.status}`);
    console.log(`   Authentication: ${health.authentication?.enabled ? 'ENABLED' : 'DISABLED'}`);
    if (health.activeSessions !== undefined) {
      console.log(`   Active Sessions: ${health.activeSessions}`);
    }
    console.log('');
  } catch (error) {
    console.log('ℹ️  Health check not available or failed:', error.message);
    console.log('');
  }

  // Create MCP client
  const validator = new MCPServerValidator(MCP_SERVER_URL, API_KEY);

  try {
    // Connect to the server (handles initialization automatically)
    await validator.connect();
    console.log('');

    // List available resources
    const resources = await validator.listResources();
    console.log('');

    // List available tools
    const tools = await validator.listTools();
    console.log('');

    // List available prompts (if supported)
    const prompts = await validator.listPrompts();
    console.log('');

    // Try to get the first available resource
    if (resources && resources.length > 0) {
      try {
        console.log('📄 Testing resource access...');
        const resourceData = await validator.getResource(resources[0].uri);
        console.log('✅ Resource access successful');
        console.log(`   Contents: ${resourceData.contents?.length || 0} items`);
      } catch (error) {
        console.log('ℹ️  Resource access failed:', error.message);
      }
      console.log('');
    }

    // Try to call the first available tool
    if (tools && tools.length > 0) {
      try {
        console.log('🔧 Testing tool execution...');
        // Try with minimal arguments first
        const toolResult = await validator.callTool(tools[0].name, {});
        console.log('✅ Tool execution successful');
        console.log(`   Result: ${toolResult.content?.length || 0} content items`);
      } catch (error) {
        console.log('ℹ️  Tool execution failed (may need specific arguments):', error.message);
      }
      console.log('');
    }

    // Try to get the first available prompt
    if (prompts && prompts.length > 0) {
      try {
        console.log('📝 Testing prompt generation...');
        const promptResult = await validator.getPrompt(prompts[0].name, {});
        console.log('✅ Prompt generation successful');
        console.log(`   Messages: ${promptResult.messages?.length || 0} messages`);
      } catch (error) {
        console.log('ℹ️  Prompt generation failed:', error.message);
      }
      console.log('');
    }

    console.log('🎉 MCP Server validation completed successfully!');
    
    // Print summary
    console.log('\n📊 Server Capabilities Summary:');
    console.log(`   🔧 Tools: ${tools?.length || 0}`);
    console.log(`   📚 Resources: ${resources?.length || 0}`);
    console.log(`   📝 Prompts: ${prompts?.length || 0}`);
    
    // Disconnect
    await validator.disconnect();

  } catch (error) {
    console.error('❌ Validation failed:', error.message);
    
    // Ensure cleanup
    try {
      await validator.disconnect();
    } catch (cleanupError) {
      // Ignore cleanup errors
    }
    
    process.exit(1);
  }
}

main().catch(console.error);

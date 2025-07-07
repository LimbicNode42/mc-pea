#!/usr/bin/env node

/**
 * Test DB MCP Server with proper session management using MCP SDK
 * This demonstrates how to properly connect to the db MCP server
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

const DB_MCP_URL = process.env.DB_MCP_URL;
const DB_MCP_API_KEY = process.env.DB_MCP_API_KEY;

if (!DB_MCP_URL || !DB_MCP_API_KEY) {
  console.error('❌ Missing required environment variables: DB_MCP_URL and DB_MCP_API_KEY');
  process.exit(1);
}

class DbMCPClient {
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
      name: 'test-db-mcp-client',
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

async function testDatabaseOperations(client, tools) {
  console.log('🗄️ Testing Database Operations');
  console.log('=============================\n');

  // Test PostgreSQL operations if available
  const postgresTools = tools.filter(tool => tool.name.includes('postgres'));
  if (postgresTools.length > 0) {
    console.log('🐘 Testing PostgreSQL operations...');
    
    // Test simple query if postgres_query tool exists
    const queryTool = postgresTools.find(tool => tool.name === 'postgres_query');
    if (queryTool) {
      try {
        console.log('   Testing PostgreSQL query...');
        await client.callTool('postgres_query', {
          query: 'SELECT version();'
        });
        console.log('   ✅ PostgreSQL query test passed');
      } catch (error) {
        console.log(`   ℹ️  PostgreSQL query test failed (expected if not connected): ${error.message}`);
      }
    }
    console.log('');
  }

  // Test Redis operations if available
  const redisTools = tools.filter(tool => tool.name.includes('redis'));
  if (redisTools.length > 0) {
    console.log('🔴 Testing Redis operations...');
    
    const pingTool = redisTools.find(tool => tool.name === 'redis_ping');
    if (pingTool) {
      try {
        console.log('   Testing Redis ping...');
        await client.callTool('redis_ping', {});
        console.log('   ✅ Redis ping test passed');
      } catch (error) {
        console.log(`   ℹ️  Redis ping test failed (expected if not connected): ${error.message}`);
      }
    }
    console.log('');
  }

  // Test MongoDB operations if available
  const mongoTools = tools.filter(tool => tool.name.includes('mongo'));
  if (mongoTools.length > 0) {
    console.log('🍃 Testing MongoDB operations...');
    
    const statusTool = mongoTools.find(tool => tool.name === 'mongodb_server_status');
    if (statusTool) {
      try {
        console.log('   Testing MongoDB server status...');
        await client.callTool('mongodb_server_status', {});
        console.log('   ✅ MongoDB status test passed');
      } catch (error) {
        console.log(`   ℹ️  MongoDB status test failed (expected if not connected): ${error.message}`);
      }
    }
    console.log('');
  }

  // Test InfluxDB operations if available
  const influxTools = tools.filter(tool => tool.name.includes('influx'));
  if (influxTools.length > 0) {
    console.log('📊 Testing InfluxDB operations...');
    
    const healthTool = influxTools.find(tool => tool.name === 'influxdb_health');
    if (healthTool) {
      try {
        console.log('   Testing InfluxDB health...');
        await client.callTool('influxdb_health', {});
        console.log('   ✅ InfluxDB health test passed');
      } catch (error) {
        console.log(`   ℹ️  InfluxDB health test failed (expected if not connected): ${error.message}`);
      }
    }
    console.log('');
  }
}

async function testDatabaseResources(client, resources) {
  console.log('📚 Testing Database Resources');
  console.log('=============================\n');

  // Group resources by database type
  const resourcesByType = {
    postgres: resources.filter(r => r.uri.includes('postgres')),
    redis: resources.filter(r => r.uri.includes('redis')),
    mongodb: resources.filter(r => r.uri.includes('mongo')),
    influxdb: resources.filter(r => r.uri.includes('influx'))
  };

  for (const [dbType, dbResources] of Object.entries(resourcesByType)) {
    if (dbResources.length > 0) {
      console.log(`📖 Testing ${dbType.toUpperCase()} resources...`);
      
      // Test the first resource of each type
      try {
        await client.getResource(dbResources[0].uri);
        console.log(`   ✅ ${dbType.toUpperCase()} resource access successful`);
      } catch (error) {
        console.log(`   ℹ️  ${dbType.toUpperCase()} resource access failed (may require connection): ${error.message}`);
      }
      console.log('');
    }
  }
}

async function main() {
  console.log('🔍 DB MCP Server Test with MCP SDK Client');
  console.log('=========================================\n');

  // Test health endpoint first
  console.log('🏥 Testing health endpoint...');
  try {
    const healthResponse = await fetch(`${DB_MCP_URL}health`);
    const health = await healthResponse.json();
    console.log('✅ Health check passed:');
    console.log(`   Status: ${health.status}`);
    console.log(`   Active Sessions: ${health.activeSessions || 0}`);
    
    // Show database enablement status if available
    if (health.databases) {
      console.log('   Database Status:');
      Object.entries(health.databases).forEach(([db, enabled]) => {
        console.log(`     ${db}: ${enabled ? 'ENABLED' : 'DISABLED'}`);
      });
    }
    console.log('');
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
    process.exit(1);
  }

  // Create MCP client
  const client = new DbMCPClient(DB_MCP_URL, DB_MCP_API_KEY);

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

    // Test database-specific operations
    if (tools && tools.length > 0) {
      await testDatabaseOperations(client, tools);
    }

    // Test database resources
    if (resources && resources.length > 0) {
      await testDatabaseResources(client, resources);
    }

    console.log('🎉 DB MCP SDK client test completed successfully!');
    
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

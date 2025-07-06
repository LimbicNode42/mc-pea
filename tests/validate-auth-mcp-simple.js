#!/usr/bin/env node

/**
 * Simple Auth MCP Server Validation
 * Tests basic connectivity and authentication
 */

// Load environment variables from .env file if it exists
import fs from 'fs';
import { join } from 'path';

function loadEnvFile() {
  const envPath = join(process.cwd(), '.env');
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

const AUTH_MCP_API_KEY = process.env.AUTH_MCP_API_KEY;
const AUTH_MCP_BASE_URL = process.env.AUTH_MCP_URL || 'http://localhost:8000/';

async function main() {
  console.log('🔍 Auth MCP Server Quick Validation');
  console.log('===================================\n');
  
  if (!AUTH_MCP_API_KEY) {
    console.error('❌ AUTH_MCP_API_KEY not found in environment');
    console.error('   Please create a .env file with AUTH_MCP_API_KEY="your-key"');
    process.exit(1);
  }
  
  console.log('✅ API Key found in environment\n');
  
  // Test 1: Health endpoint (no auth required)
  console.log('🏥 Testing health endpoint...');
  try {
    const healthUrl = `${AUTH_MCP_BASE_URL}health`;
    const healthResponse = await fetch(healthUrl);
    const health = await healthResponse.json();
    console.log('✅ Health check passed:');
    console.log(`   Status: ${health.status}`);
    console.log(`   Authentication: ${health.authentication?.enabled ? 'ENABLED' : 'DISABLED'}`);
    console.log(`   Capabilities: ${health.capabilities?.join(', ')}\n`);
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
    process.exit(1);
  }
  
  // Test 2: Unauthenticated MCP request (should fail)
  console.log('🚫 Testing unauthenticated MCP request (should fail)...');
  try {
    const unauthResponse = await fetch(`${AUTH_MCP_BASE_URL}mcp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'initialize',
        id: 1,
        params: { protocolVersion: '1.0', capabilities: {} }
      })
    });
    
    if (unauthResponse.status === 401) {
      console.log('✅ Unauthenticated request properly rejected (401)\n');
    } else {
      console.error(`❌ Expected 401, got ${unauthResponse.status}\n`);
    }
  } catch (error) {
    console.error('❌ Error testing unauthenticated request:', error.message);
  }
  
  // Test 3: Authenticated MCP request (should work)
  console.log('🔐 Testing authenticated MCP request...');
  try {
    const authResponse = await fetch(`${AUTH_MCP_BASE_URL}mcp`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'API_KEY': AUTH_MCP_API_KEY
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'initialize',
        id: 1,
        params: { 
          protocolVersion: '1.0', 
          capabilities: {
            resources: {},
            tools: {}
          }
        }
      })
    });
    
    if (authResponse.ok) {
      const result = await authResponse.json();
      console.log('✅ Authenticated request successful');
      console.log(`   Response: ${JSON.stringify(result, null, 2)}\n`);
    } else {
      console.error(`❌ Authenticated request failed: ${authResponse.status}`);
      const errorText = await authResponse.text();
      console.error(`   Error: ${errorText}\n`);
    }
  } catch (error) {
    console.error('❌ Error testing authenticated request:', error.message);
  }
  
  console.log('🎯 Validation completed!');
  console.log('💡 To use this server in MCP Inspector, configure:');
  console.log(`   URL: ${AUTH_MCP_BASE_URL}mcp`);
  console.log(`   Headers: { "API_KEY": "${AUTH_MCP_API_KEY}" }`);
}

main().catch(console.error);

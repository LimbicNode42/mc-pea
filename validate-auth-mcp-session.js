#!/usr/bin/env node

/**
 * Simple Auth MCP Server validation with manual session management
 * This shows how to handle session IDs on the client side
 */

// Load environment variables
import fs from 'fs';
import { randomUUID } from 'crypto';

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

async function testWithSession() {
  console.log('🔍 Auth MCP Server Session Test');
  console.log('===============================\n');
  
  if (!AUTH_MCP_URL || !AUTH_MCP_API_KEY) {
    console.error('❌ Missing AUTH_MCP_URL or AUTH_MCP_API_KEY in environment');
    process.exit(1);
  }
  
  // Generate a session ID on the client side
  const sessionId = randomUUID();
  console.log(`📋 Generated session ID: ${sessionId}\n`);
  
  // Test 1: Initialize request without session ID (should create new session)
  console.log('🔌 Testing initialization request...');
  try {
    const initResponse = await fetch(`${AUTH_MCP_URL}mcp`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'API_KEY': AUTH_MCP_API_KEY
        // No session ID for initialization
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
    
    const initResult = await initResponse.json();
    console.log(`   Status: ${initResponse.status}`);
    console.log(`   Response: ${JSON.stringify(initResult, null, 2)}`);
    
    // Check for session ID in response headers
    const responseSessionId = initResponse.headers.get('mcp-session-id');
    if (responseSessionId) {
      console.log(`✅ Server provided session ID: ${responseSessionId}`);
      
      // Test 2: Subsequent request with session ID
      console.log('\n🔄 Testing subsequent request with session ID...');
      const listResponse = await fetch(`${AUTH_MCP_URL}mcp`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'API_KEY': AUTH_MCP_API_KEY,
          'mcp-session-id': responseSessionId
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'resources/list',
          id: 2,
          params: {}
        })
      });
      
      const listResult = await listResponse.json();
      console.log(`   Status: ${listResponse.status}`);
      console.log(`   Response: ${JSON.stringify(listResult, null, 2)}`);
      
      if (listResponse.ok) {
        console.log('✅ Session management working correctly!');
      }
    } else {
      console.log('ℹ️  No session ID in response headers - checking response body');
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

testWithSession();

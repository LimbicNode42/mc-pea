#!/usr/bin/env node

/**
 * Debug session management with detailed HTTP debugging
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

async function debugRequest() {
  console.log('🔍 Debugging Auth MCP Server Session Management');
  console.log('===============================================\n');
  
  console.log(`🌐 Base URL: ${AUTH_MCP_URL}`);
  console.log(`🔑 API Key: ${AUTH_MCP_API_KEY ? 'configured' : 'missing'}\n`);
  
  // Test the health endpoint first
  console.log('🏥 Testing health endpoint...');
  try {
    const healthUrl = `${AUTH_MCP_URL}health`;
    console.log(`   URL: ${healthUrl}`);
    
    const healthResponse = await fetch(healthUrl);
    console.log(`   Status: ${healthResponse.status}`);
    console.log(`   Headers:`, Object.fromEntries(healthResponse.headers.entries()));
    
    const healthText = await healthResponse.text();
    console.log(`   Response: ${healthText.substring(0, 200)}${healthText.length > 200 ? '...' : ''}`);
    
    if (healthResponse.ok) {
      try {
        const health = JSON.parse(healthText);
        console.log('✅ Health endpoint working correctly');
        console.log(`   Active sessions: ${health.activeSessions}`);
      } catch (e) {
        console.log('⚠️  Health response is not JSON');
      }
    }
  } catch (error) {
    console.error('❌ Health endpoint failed:', error.message);
  }
  
  console.log('\n🔌 Testing MCP endpoint...');
  try {
    const mcpUrl = `${AUTH_MCP_URL}mcp`;
    console.log(`   URL: ${mcpUrl}`);
    
    const headers = {
      'Content-Type': 'application/json',
      'API_KEY': AUTH_MCP_API_KEY
    };
    
    const body = {
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
    };
    
    console.log(`   Headers:`, headers);
    console.log(`   Body:`, JSON.stringify(body, null, 2));
    
    const mcpResponse = await fetch(mcpUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    });
    
    console.log(`   Status: ${mcpResponse.status}`);
    console.log(`   Response Headers:`, Object.fromEntries(mcpResponse.headers.entries()));
    
    const mcpText = await mcpResponse.text();
    console.log(`   Response: ${mcpText.substring(0, 500)}${mcpText.length > 500 ? '...' : ''}`);
    
    // Try to parse as JSON
    try {
      const mcpResult = JSON.parse(mcpText);
      console.log('✅ MCP response is valid JSON');
      console.log('   Parsed:', JSON.stringify(mcpResult, null, 2));
    } catch (e) {
      console.log('⚠️  MCP response is not JSON - might be HTML error page');
    }
    
  } catch (error) {
    console.error('❌ MCP endpoint failed:', error.message);
  }
}

debugRequest();

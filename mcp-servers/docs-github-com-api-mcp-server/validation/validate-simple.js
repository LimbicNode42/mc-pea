#!/usr/bin/env node

/**
 * Simple MCP Server Validation
 * 
 * Quick validation script without MCP SDK dependencies
 */

const https = require('https');
const http = require('http');
const { URL } = require('url');

// Load environment variables from .env file
function loadEnvFile() {
  const fs = require('fs');
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

async function makeRequest(url, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    try {
      const urlObj = new URL(url);
      const jsonPayload = JSON.stringify(payload);
      
      const options = {
        hostname: urlObj.hostname,
        port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
        path: urlObj.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(jsonPayload),
          'x-api-key': API_KEY,
          ...headers
        },
        timeout: 10000
      };

      const client = urlObj.protocol === 'https:' ? https : http;
      
      const req = client.request(options, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            if (res.statusCode === 200) {
              const response = JSON.parse(data);
              resolve({ success: true, data: response });
            } else {
              resolve({ success: false, error: `HTTP ${res.statusCode}: ${data}` });
            }
          } catch (error) {
            resolve({ success: false, error: `Parse error: ${error.message}` });
          }
        });
      });

      req.on('error', (error) => {
        resolve({ success: false, error: error.message });
      });

      req.on('timeout', () => {
        req.destroy();
        resolve({ success: false, error: 'Request timeout' });
      });
      
      req.write(jsonPayload);
      req.end();
      
    } catch (error) {
      resolve({ success: false, error: error.message });
    }
  });
}

async function validateMCPServer() {
  console.log('🔍 Simple MCP Server Validation');
  console.log('===============================\n');

  const baseUrl = MCP_SERVER_URL.endsWith('/') ? MCP_SERVER_URL : MCP_SERVER_URL + '/';
  const mcpUrl = baseUrl + 'mcp';
  
  console.log(`🎯 Testing MCP server at: ${mcpUrl}`);
  console.log(`🔐 Using API key: ${API_KEY.substring(0, 8)}...`);
  console.log('');

  // Test 1: Health check (if available)
  console.log('🏥 Testing health endpoint...');
  try {
    const healthResponse = await fetch(baseUrl + 'health');
    const health = await healthResponse.json();
    console.log('✅ Health check passed');
  } catch (error) {
    console.log('ℹ️  Health endpoint not available');
  }

  // Test 2: Initialize
  console.log('🚀 Testing MCP initialize...');
  const initResult = await makeRequest(mcpUrl, {
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
      protocolVersion: "2024-11-05",
      capabilities: {
        roots: { listChanged: true },
        sampling: {}
      },
      clientInfo: {
        name: "simple-validator",
        version: "1.0.0"
      }
    }
  });

  if (initResult.success) {
    console.log('✅ Initialize successful');
  } else {
    console.log(`⚠️  Initialize: ${initResult.error}`);
  }

  // Test 3: List tools
  console.log('🔧 Testing tools/list...');
  const toolsResult = await makeRequest(mcpUrl, {
    jsonrpc: "2.0",
    id: 2,
    method: "tools/list"
  });

  if (toolsResult.success) {
    const tools = toolsResult.data.result?.tools || [];
    console.log(`✅ Found ${tools.length} tools`);
    tools.forEach(tool => {
      console.log(`   - ${tool.name}: ${tool.description}`);
    });
  } else {
    console.log(`⚠️  Tools: ${toolsResult.error}`);
  }

  // Test 4: List resources
  console.log('📚 Testing resources/list...');
  const resourcesResult = await makeRequest(mcpUrl, {
    jsonrpc: "2.0",
    id: 3,
    method: "resources/list"
  });

  if (resourcesResult.success) {
    const resources = resourcesResult.data.result?.resources || [];
    console.log(`✅ Found ${resources.length} resources`);
    resources.forEach(resource => {
      console.log(`   - ${resource.name}: ${resource.uri}`);
    });
  } else {
    console.log(`⚠️  Resources: ${resourcesResult.error}`);
  }

  // Test 5: List prompts
  console.log('📝 Testing prompts/list...');
  const promptsResult = await makeRequest(mcpUrl, {
    jsonrpc: "2.0",
    id: 4,
    method: "prompts/list"
  });

  if (promptsResult.success) {
    const prompts = promptsResult.data.result?.prompts || [];
    console.log(`✅ Found ${prompts.length} prompts`);
    prompts.forEach(prompt => {
      console.log(`   - ${prompt.name}: ${prompt.description}`);
    });
  } else {
    console.log(`ℹ️  Prompts not available: ${promptsResult.error}`);
  }

  console.log('\n🎉 Simple validation completed!');
}

validateMCPServer().catch(console.error);

#!/usr/bin/env node

/**
 * Validation script for Auth MCP Server
 * Tests the deployed auth MCP server capabilities
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables from .env file
function loadEnvFile() {
  const envPath = join(__dirname, '.env');
  if (!fs.existsSync(envPath)) {
    console.error('❌ .env file not found. Please create one with AUTH_MCP_API_KEY');
    process.exit(1);
  }
  
  const envContent = fs.readFileSync(envPath, 'utf8');
  const envVars = {};
  
  envContent.split('\n').forEach(line => {
    line = line.trim();
    if (line && !line.startsWith('#')) {
      const [key, ...valueParts] = line.split('=');
      if (key && valueParts.length > 0) {
        const value = valueParts.join('=').replace(/^["']|["']$/g, '');
        envVars[key] = value;
        process.env[key] = value;
      }
    }
  });
  
  return envVars;
}

// Create temporary MCP configuration
function createTempMcpConfig() {
  const apiKey = process.env.AUTH_MCP_API_KEY;
  const authBaseUrl = process.env.AUTH_MCP_URL;
  
  if (!apiKey) {
    console.error('❌ AUTH_MCP_API_KEY not found in environment variables');
    process.exit(1);
  }
  
  if (!authBaseUrl) {
    console.error('❌ AUTH_MCP_URL not found in environment variables');
    process.exit(1);
  }
  
  const mcpConfig = {
    "servers": {
      "auth-validation": {
        "type": "http",
        "url": `${authBaseUrl}mcp`,
        "headers": {
          "API_KEY": apiKey
        }
      }
    }
  };
  
  const tempConfigPath = join(__dirname, '.temp-mcp-config.json');
  fs.writeFileSync(tempConfigPath, JSON.stringify(mcpConfig, null, 2));
  return tempConfigPath;
}

async function validateAuthMcpServer() {
  console.log('🔍 Auth MCP Server Validation');
  console.log('============================\n');
  
  // Load environment variables
  console.log('📋 Loading environment variables...');
  const envVars = loadEnvFile();
  
  if (!envVars.AUTH_MCP_API_KEY) {
    console.error('❌ AUTH_MCP_API_KEY not found in .env file');
    process.exit(1);
  }
  
  console.log('✅ API Key loaded from environment\n');
  
  // Create temporary MCP config
  console.log('⚙️  Creating temporary MCP configuration...');
  const tempConfigPath = createTempMcpConfig();
  console.log('✅ Temporary config created\n');
  
  // Test health endpoint first
  console.log('🏥 Testing health endpoint...');
  try {
    const healthUrl = `${process.env.AUTH_MCP_URL}health`;
    const response = await fetch(healthUrl);
    const health = await response.json();
    console.log('✅ Health check passed:');
    console.log(`   Status: ${health.status}`);
    console.log(`   Mode: ${health.mode}`);
    console.log(`   Authentication: ${health.authentication?.enabled ? 'ENABLED' : 'DISABLED'}`);
    console.log(`   Active Sessions: ${health.activeSessions}`);
    console.log(`   Capabilities: ${health.capabilities?.join(', ')}\n`);
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
    return false;
  }
  
  // Test MCP connection using mc-pea
  console.log('🔌 Testing MCP connection...');
  return new Promise((resolve) => {
    const mcpProcess = spawn('node', ['demo-mcpea-integration.js', '--config', tempConfigPath], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: __dirname
    });
    
    let output = '';
    let errorOutput = '';
    
    mcpProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    mcpProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    mcpProcess.on('close', (code) => {
      // Clean up temp file
      try {
        fs.unlinkSync(tempConfigPath);
      } catch (e) {
        // Ignore cleanup errors
      }
      
      if (code === 0) {
        console.log('✅ MCP connection test passed\n');
        console.log('📊 Test Results:');
        console.log(output);
        resolve(true);
      } else {
        console.error('❌ MCP connection test failed');
        console.error('Error output:', errorOutput);
        console.error('Standard output:', output);
        resolve(false);
      }
    });
    
    mcpProcess.on('error', (error) => {
      console.error('❌ Failed to start MCP test:', error.message);
      resolve(false);
    });
    
    // Send a simple test command
    setTimeout(() => {
      mcpProcess.stdin.write('test\n');
      setTimeout(() => {
        mcpProcess.kill('SIGTERM');
      }, 3000);
    }, 1000);
  });
}

// Test without authentication to verify it's rejected
async function testUnauthenticatedAccess() {
  console.log('🚫 Testing unauthenticated access (should fail)...');
  try {
    const response = await fetch(`${process.env.AUTH_MCP_URL}mcp`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'initialize',
        id: 1,
        params: {
          protocolVersion: '1.0',
          capabilities: {}
        }
      })
    });
    
    if (response.status === 401) {
      console.log('✅ Unauthenticated access properly rejected (401)\n');
      return true;
    } else {
      console.error(`❌ Expected 401, got ${response.status}\n`);
      return false;
    }
  } catch (error) {
    console.error('❌ Error testing unauthenticated access:', error.message);
    return false;
  }
}

// Main validation function
async function main() {
  let allPassed = true;
  
  // Test unauthenticated access
  const unauthTest = await testUnauthenticatedAccess();
  allPassed = allPassed && unauthTest;
  
  // Test authenticated access
  const authTest = await validateAuthMcpServer();
  allPassed = allPassed && authTest;
  
  console.log('\n🎯 Final Results:');
  console.log('================');
  if (allPassed) {
    console.log('✅ All validation tests passed!');
    console.log('🚀 Auth MCP Server is working correctly');
  } else {
    console.log('❌ Some validation tests failed');
    console.log('🔧 Please check the server configuration and try again');
  }
  
  process.exit(allPassed ? 0 : 1);
}

main().catch(error => {
  console.error('💥 Validation script failed:', error);
  process.exit(1);
});

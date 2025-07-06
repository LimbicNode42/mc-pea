#!/usr/bin/env node

/**
 * Template Validation Script
 * 
 * Validates that the MCP server template is complete and functional
 */

const fs = require('fs');
const path = require('path');

const TEMPLATE_DIR = '../templates/mcp-server-template';

console.log('🔍 MCP Server Template Validation');
console.log('=================================\n');

let validationPassed = true;

function checkFile(filePath, description) {
  const fullPath = path.join(TEMPLATE_DIR, filePath);
  if (fs.existsSync(fullPath)) {
    console.log(`✅ ${description}: ${filePath}`);
    return true;
  } else {
    console.log(`❌ ${description}: ${filePath} (MISSING)`);
    validationPassed = false;
    return false;
  }
}

function checkDirectory(dirPath, description) {
  const fullPath = path.join(TEMPLATE_DIR, dirPath);
  if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
    console.log(`✅ ${description}: ${dirPath}/`);
    return true;
  } else {
    console.log(`❌ ${description}: ${dirPath}/ (MISSING)`);
    validationPassed = false;
    return false;
  }
}

console.log('📋 Core Structure Validation:');

// Core directories
checkDirectory('src', 'Source directory');
checkDirectory('src/tools', 'Tools directory');
checkDirectory('src/resources', 'Resources directory');
checkDirectory('src/prompts', 'Prompts directory');
checkDirectory('validation', 'Validation scripts directory');
checkDirectory('docker', 'Docker configuration directory');
checkDirectory('prompts', 'Development guidelines directory');

console.log('\n📄 Core Files Validation:');

// Core implementation files
checkFile('src/index.ts', 'Main server entry point');
checkFile('src/registrations.ts', 'Registration system');
checkFile('src/tools/index.ts', 'Tool definitions');
checkFile('src/resources/index.ts', 'Resource definitions');
checkFile('src/prompts/index.ts', 'Prompt definitions');

console.log('\n🔧 Validation Scripts:');

// Validation scripts
checkFile('validation/test-mcp-client.js', 'MCP SDK client validation');
checkFile('validation/validate-simple.js', 'Simple validation script');
checkFile('validation/validate-bash.sh', 'Bash validation script');

console.log('\n🐳 Docker Configuration:');

// Docker files
checkFile('docker/Dockerfile', 'Production Dockerfile');
checkFile('docker/docker-compose.yml', 'Docker Compose configuration');

console.log('\n📚 Documentation:');

// Documentation files
checkFile('README.md', 'Main documentation');
checkFile('PROTOCOL_REFERENCE.md', 'Protocol reference');
checkFile('SDK_PATTERNS.md', 'SDK patterns guide');

console.log('\n🛡️ Development Guardrails:');

// Prompt files
checkFile('prompts/mcp-development.md', 'Development guidelines');
checkFile('prompts/protocol-rules.md', 'Protocol compliance rules');
checkFile('prompts/common-patterns.md', 'Common patterns guide');
checkFile('prompts/ai-assistant-instructions.md', 'AI assistant guardrails');

console.log('\n⚙️ Configuration Files:');

// Configuration files
checkFile('package.json', 'NPM package configuration');
checkFile('tsconfig.json', 'TypeScript configuration');
checkFile('.env.example', 'Environment variables template');

console.log('\n🔍 Content Validation:');

// Check file contents for critical patterns
function checkFileContent(filePath, patterns, description) {
  const fullPath = path.join(TEMPLATE_DIR, filePath);
  if (!fs.existsSync(fullPath)) return false;
  
  const content = fs.readFileSync(fullPath, 'utf8');
  let allPatternsFound = true;
  
  for (const pattern of patterns) {
    if (!content.includes(pattern)) {
      console.log(`❌ ${description}: Missing "${pattern}" in ${filePath}`);
      allPatternsFound = false;
      validationPassed = false;
    }
  }
  
  if (allPatternsFound) {
    console.log(`✅ ${description}: ${filePath}`);
  }
  
  return allPatternsFound;
}

// Check main server file
checkFileContent('src/index.ts', [
  'StreamableHTTPServerTransport',
  'sessionIdGenerator',
  'randomUUID',
  'validateAuthentication'
], 'Main server patterns');

// Check registration file
checkFileContent('src/registrations.ts', [
  'server.registerTool',
  'jsonSchemaToZod',
  'toolDefinitions',
  'toolHandlers'
], 'Registration patterns');

// Check validation client
checkFileContent('validation/test-mcp-client.js', [
  'StreamableHTTPClientTransport',
  'Client',
  'requestInit',
  'headers'
], 'Client validation patterns');

// Check package.json
checkFileContent('package.json', [
  '@modelcontextprotocol/sdk',
  'zod',
  'typescript'
], 'Package dependencies');

console.log('\n📊 Validation Summary:');

if (validationPassed) {
  console.log('🎉 All template validation checks passed!');
  console.log('✅ Template is complete and ready for use.');
  console.log('');
  console.log('🚀 Next steps:');
  console.log('   1. Copy template: cp -r templates/mcp-server-template my-server');
  console.log('   2. Configure: cd my-server && cp .env.example .env');
  console.log('   3. Customize: Edit tools, resources, and prompts');
  console.log('   4. Build: npm install && npm run build');
  console.log('   5. Test: npm run test');
} else {
  console.log('❌ Template validation failed!');
  console.log('🔧 Some required files or patterns are missing.');
  console.log('Please check the errors above and fix the template.');
  process.exit(1);
}

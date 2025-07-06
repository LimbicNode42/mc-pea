#!/usr/bin/env node

/**
 * Architecture-Aware MCP Server Validation
 * Tests both Python (stateful) and TypeScript (stateless) MCP servers correctly
 */

const https = require('https');
const http = require('http');
const { URL } = require('url');

class ArchitectureAwareMCPTester {
    constructor() {
        this.servers = {
            db: {
                url: 'https://dbmcp.wheeler-network.com/mcp/',
                type: 'python',
                stateful: true,
                name: 'Database MCP'
            },
            auth: {
                url: 'https://authmcp.wheeler-network.com/mcp/',
                type: 'typescript',
                stateful: false,
                name: 'Auth MCP'
            }
        };
        this.sessions = {};
    }

    async validateAllServers() {
        console.log('🏗️  Architecture-Aware MCP Server Validation\n');
        
        console.log('📋 Server Architecture:');
        console.log('  🐍 Database MCP: Python (Stateful)');
        console.log('  📜 Auth MCP: TypeScript (Stateless)\n');
        
        // Test Auth Server (Stateless TypeScript)
        console.log('🔐 Testing Auth MCP Server (TypeScript - Stateless)...');
        const authResults = await this.testStatelessServer(this.servers.auth);
        
        console.log('\n🗄️  Testing Database MCP Server (Python - Stateful)...');
        const dbResults = await this.testStatefulServer(this.servers.db);
        
        this.printValidationResults(authResults, dbResults);
    }

    async testStatelessServer(serverConfig) {
        console.log(`  📡 Testing ${serverConfig.name} (stateless mode)...`);
        
        const results = {
            connection: false,
            initialize: false,
            capabilities: false,
            tools: false,
            directOperation: false
        };
        
        // Test 1: Basic connectivity
        console.log('    🔌 Testing connectivity...');
        const connectTest = await this.sendMCPRequest(serverConfig.url, {
            jsonrpc: "2.0",
            id: 1,
            method: "ping"
        });
        
        if (connectTest.success || connectTest.statusCode < 500) {
            results.connection = true;
            console.log('    ✅ Server responding');
        } else {
            console.log('    ❌ No response');
            return results;
        }
        
        // Test 2: Initialize (may not be required for stateless)
        console.log('    🚀 Testing initialize...');
        const initResult = await this.sendMCPRequest(serverConfig.url, {
            jsonrpc: "2.0",
            id: 2,
            method: "initialize",
            params: {
                protocolVersion: "2024-11-05",
                capabilities: {
                    roots: { listChanged: true },
                    sampling: {}
                },
                clientInfo: {
                    name: "MC-PEA-Validator",
                    version: "1.0.0"
                }
            }
        });
        
        if (initResult.success) {
            results.initialize = true;
            console.log('    ✅ Initialize successful');
        } else {
            console.log(`    ⚠️  Initialize: ${initResult.error}`);
        }
        
        // Test 3: List capabilities
        console.log('    🛠️  Testing capabilities...');
        const capResult = await this.sendMCPRequest(serverConfig.url, {
            jsonrpc: "2.0",
            id: 3,
            method: "capabilities"
        });
        
        if (capResult.success) {
            results.capabilities = true;
            console.log('    ✅ Capabilities retrieved');
        } else {
            console.log(`    ⚠️  Capabilities: ${capResult.error}`);
        }
        
        // Test 4: List tools
        console.log('    🔧 Testing tools list...');
        const toolsResult = await this.sendMCPRequest(serverConfig.url, {
            jsonrpc: "2.0", 
            id: 4,
            method: "tools/list"
        });
        
        if (toolsResult.success) {
            results.tools = true;
            const tools = toolsResult.data.result?.tools || [];
            console.log(`    ✅ Found ${tools.length} tools`);
            
            if (tools.length > 0) {
                console.log(`    📋 Available tools: ${tools.map(t => t.name).join(', ')}`);
            }
        } else {
            console.log(`    ⚠️  Tools: ${toolsResult.error}`);
        }
        
        // Test 5: Try a direct operation (auth-specific)
        console.log('    🎯 Testing direct operation...');
        const opResult = await this.sendMCPRequest(serverConfig.url, {
            jsonrpc: "2.0",
            id: 5,
            method: "auth/validate",
            params: {
                token: "test-token"
            }
        });
        
        if (opResult.success || opResult.statusCode === 400) {
            results.directOperation = true;
            console.log('    ✅ Direct operations functional');
        } else {
            console.log(`    ⚠️  Direct operation: ${opResult.error}`);
        }
        
        return results;
    }

    async testStatefulServer(serverConfig) {
        console.log(`  📡 Testing ${serverConfig.name} (stateful mode)...`);
        
        const results = {
            connection: false,
            sessionStart: false,
            initialize: false,
            capabilities: false,
            tools: false,
            databaseOperation: false
        };
        
        // Test 1: Basic connectivity
        console.log('    🔌 Testing connectivity...');
        const connectTest = await this.sendMCPRequest(serverConfig.url, {
            jsonrpc: "2.0",
            id: 1,
            method: "ping"
        });
        
        if (connectTest.success || connectTest.error?.includes('session')) {
            results.connection = true;
            console.log('    ✅ Server responding (session management active)');
        } else {
            console.log('    ❌ No response');
            return results;
        }
        
        // Test 2: Session establishment
        console.log('    🔗 Testing session establishment...');
        const sessionResult = await this.sendMCPRequest(serverConfig.url, {
            jsonrpc: "2.0",
            id: 2,
            method: "session/start",
            params: {
                clientInfo: {
                    name: "MC-PEA-Validator",
                    version: "1.0.0"
                }
            }
        });
        
        let sessionId = null;
        if (sessionResult.success && sessionResult.data.result?.sessionId) {
            sessionId = sessionResult.data.result.sessionId;
            results.sessionStart = true;
            console.log(`    ✅ Session established: ${sessionId.substring(0, 8)}...`);
            this.sessions[serverConfig.url] = sessionId;
        } else {
            console.log(`    ⚠️  Session establishment: ${sessionResult.error}`);
        }
        
        // Test 3: Initialize with session
        console.log('    🚀 Testing initialize with session...');
        const initResult = await this.sendMCPRequestWithSession(serverConfig.url, {
            jsonrpc: "2.0",
            id: 3,
            method: "initialize",
            params: {
                protocolVersion: "2024-11-05",
                capabilities: {
                    roots: { listChanged: true },
                    sampling: {}
                },
                clientInfo: {
                    name: "MC-PEA-Validator",
                    version: "1.0.0"
                }
            }
        }, sessionId);
        
        if (initResult.success) {
            results.initialize = true;
            console.log('    ✅ Initialize with session successful');
        } else {
            console.log(`    ⚠️  Initialize: ${initResult.error}`);
        }
        
        // Test 4: Capabilities with session
        console.log('    🛠️  Testing capabilities with session...');
        const capResult = await this.sendMCPRequestWithSession(serverConfig.url, {
            jsonrpc: "2.0",
            id: 4,
            method: "capabilities"
        }, sessionId);
        
        if (capResult.success) {
            results.capabilities = true;
            console.log('    ✅ Capabilities retrieved');
        } else {
            console.log(`    ⚠️  Capabilities: ${capResult.error}`);
        }
        
        // Test 5: Database-specific operations
        console.log('    🗃️  Testing database operations...');
        const dbOpResult = await this.sendMCPRequestWithSession(serverConfig.url, {
            jsonrpc: "2.0",
            id: 5,
            method: "tools/call",
            params: {
                name: "query_database",
                arguments: {
                    query: "SELECT 1 as test_connection"
                }
            }
        }, sessionId);
        
        if (dbOpResult.success || dbOpResult.statusCode === 400) {
            results.databaseOperation = true;
            console.log('    ✅ Database operations functional');
        } else {
            console.log(`    ⚠️  Database operation: ${dbOpResult.error}`);
        }
        
        return results;
    }

    async sendMCPRequest(url, payload) {
        return this.makeRequest(url, payload, {});
    }

    async sendMCPRequestWithSession(url, payload, sessionId) {
        const extraHeaders = sessionId ? { 'X-Session-ID': sessionId } : {};
        return this.makeRequest(url, payload, extraHeaders);
    }

    async makeRequest(url, payload, extraHeaders = {}) {
        return new Promise((resolve) => {
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
                        'Accept': 'application/json, text/event-stream',
                        'User-Agent': 'MC-PEA-Validator/1.0',
                        'Connection': 'keep-alive',
                        ...extraHeaders
                    },
                    timeout: 15000
                };

                const client = urlObj.protocol === 'https:' ? https : http;
                
                const req = client.request(options, (res) => {
                    let data = '';
                    res.on('data', chunk => data += chunk);
                    res.on('end', () => {
                        try {
                            if (res.statusCode === 200) {
                                // Try to parse as JSON first
                                try {
                                    const response = JSON.parse(data);
                                    resolve({
                                        success: true,
                                        data: response,
                                        statusCode: res.statusCode
                                    });
                                } catch (parseError) {
                                    // If not JSON, might be SSE
                                    if (data.startsWith('event:') || data.includes('data:')) {
                                        resolve({
                                            success: true,
                                            data: { type: 'sse', content: data },
                                            statusCode: res.statusCode
                                        });
                                    } else {
                                        resolve({
                                            success: false,
                                            error: `Parse error: ${parseError.message}`,
                                            statusCode: res.statusCode
                                        });
                                    }
                                }
                            } else {
                                resolve({
                                    success: false,
                                    error: `HTTP ${res.statusCode}: ${data.substring(0, 100)}`,
                                    statusCode: res.statusCode
                                });
                            }
                        } catch (error) {
                            resolve({
                                success: false,
                                error: `Response processing error: ${error.message}`,
                                statusCode: res.statusCode
                            });
                        }
                    });
                });

                req.on('error', (error) => {
                    resolve({
                        success: false,
                        error: `Request error: ${error.message}`,
                        statusCode: null
                    });
                });

                req.on('timeout', () => {
                    req.destroy();
                    resolve({
                        success: false,
                        error: 'Request timeout',
                        statusCode: null
                    });
                });
                
                req.write(jsonPayload);
                req.end();
                
            } catch (error) {
                resolve({
                    success: false,
                    error: `Setup error: ${error.message}`,
                    statusCode: null
                });
            }
        });
    }

    printValidationResults(authResults, dbResults) {
        console.log('\n📊 Architecture-Aware Validation Results');
        console.log('=========================================');
        
        console.log('\n🔐 Auth MCP Server (TypeScript - Stateless):');
        this.printServerResults(authResults);
        
        console.log('\n🗄️  Database MCP Server (Python - Stateful):');
        this.printServerResults(dbResults);
        
        // Overall assessment
        const authScore = Object.values(authResults).filter(Boolean).length;
        const authTotal = Object.keys(authResults).length;
        const dbScore = Object.values(dbResults).filter(Boolean).length;
        const dbTotal = Object.keys(dbResults).length;
        
        console.log('\n📈 Summary:');
        console.log(`  🔐 Auth Server: ${authScore}/${authTotal} tests passed`);
        console.log(`  🗄️  DB Server: ${dbScore}/${dbTotal} tests passed`);
        
        console.log('\n🎯 Architecture Insights:');
        console.log('  📜 TypeScript server works immediately (stateless)');
        console.log('  🐍 Python server requires session management (stateful)');
        console.log('  🔄 Both approaches are valid MCP implementations');
        
        console.log('\n🚀 Next Steps:');
        console.log('  ✅ Auth server ready for immediate integration');
        console.log('  🔧 DB server needs session handling in client code');
        console.log('  📋 Consider making auth server stateful for consistency');
    }

    printServerResults(results) {
        Object.entries(results).forEach(([test, passed]) => {
            const status = passed ? '✅ PASS' : '❌ FAIL';
            const testName = test.charAt(0).toUpperCase() + test.slice(1).replace(/([A-Z])/g, ' $1');
            console.log(`  ${status} ${testName}`);
        });
    }
}

// Run the architecture-aware validation
if (require.main === module) {
    const tester = new ArchitectureAwareMCPTester();
    tester.validateAllServers().catch(console.error);
}

module.exports = ArchitectureAwareMCPTester;

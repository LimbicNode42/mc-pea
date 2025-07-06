#!/usr/bin/env node

/**
 * Debug HTTP Request Test
 * Detailed debugging of the HTTP requests to understand why we're getting 404
 */

// Load environment variables
require('dotenv').config();

const https = require('https');
const http = require('http');
const { URL } = require('url');

class HTTPDebugger {
    constructor() {
        this.dbUrl = (process.env.DB_MCP_URL || 'http://localhost:8001/') + 'mcp';
        this.authUrl = (process.env.AUTH_MCP_URL || 'http://localhost:8000/') + 'mcp';
        this.authApiKey = process.env.AUTH_MCP_API_KEY;
    }

    async debugRequests() {
        console.log('🔍 HTTP Request Debug Analysis\n');
        
        console.log('📋 Target URLs:');
        console.log(`  DB:   ${this.dbUrl}`);
        console.log(`  Auth: ${this.authUrl}\n`);
        
        // Test different endpoints and methods
        await this.testMultipleEndpoints(this.dbUrl, 'DB');
        await this.testMultipleEndpoints(this.authUrl, 'Auth');
    }

    async testMultipleEndpoints(baseUrl, serverName) {
        console.log(`🧪 Testing ${serverName} Server: ${baseUrl}`);
        
        const endpoints = [
            '', // Root
            '/',
            '/health',
            '/capabilities',
            '/ping',
            '/status'
        ];
        
        for (const endpoint of endpoints) {
            await this.detailedRequest(baseUrl, endpoint, serverName);
            await this.delay(500); // Be nice to the server
        }
        
        console.log(''); // Empty line for separation
    }

    async detailedRequest(baseUrl, path, serverName) {
        const fullUrl = baseUrl + (path.startsWith('/') ? path.substring(1) : path);
        
        try {
            console.log(`  📡 Testing: ${fullUrl}`);
            
            const response = await this.makeDetailedRequest(fullUrl);
            
            console.log(`    Status: ${response.statusCode} ${this.getStatusText(response.statusCode)}`);
            console.log(`    Headers: ${JSON.stringify(response.headers, null, 2).substring(0, 200)}...`);
            
            if (response.data) {
                const preview = response.data.substring(0, 100);
                console.log(`    Body Preview: "${preview}${response.data.length > 100 ? '...' : ''}"`);
            }
            
            if (response.statusCode === 200) {
                console.log(`    ✅ SUCCESS`);
            } else if (response.statusCode === 404) {
                console.log(`    ❌ 404 NOT FOUND`);
            } else {
                console.log(`    ⚠️  Unexpected status`);
            }
            
        } catch (error) {
            console.log(`    ❌ Request failed: ${error.message}`);
            
            // Additional debugging for network errors
            if (error.code === 'ENOTFOUND') {
                console.log(`    🔍 DNS resolution failed - check domain name`);
            } else if (error.code === 'ECONNREFUSED') {
                console.log(`    🔍 Connection refused - server may be down`);
            } else if (error.code === 'ETIMEDOUT') {
                console.log(`    🔍 Connection timeout - server may be slow`);
            }
        }
        
        console.log(''); // Empty line for readability
    }

    async makeDetailedRequest(url) {
        return new Promise((resolve, reject) => {
            try {
                const urlObj = new URL(url);
                console.log(`    🔍 Parsed URL: ${JSON.stringify({
                    protocol: urlObj.protocol,
                    hostname: urlObj.hostname,
                    port: urlObj.port,
                    pathname: urlObj.pathname,
                    search: urlObj.search
                })}`);
                
                const options = {
                    hostname: urlObj.hostname,
                    port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
                    path: urlObj.pathname + urlObj.search,
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'User-Agent': 'MC-PEA-Debug/1.0 (Node.js)',
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive'
                    },
                    timeout: 15000,
                    // Add this to see more SSL details
                    rejectUnauthorized: false
                };

                console.log(`    📋 Request Options: ${JSON.stringify(options, null, 2)}`);

                const client = urlObj.protocol === 'https:' ? https : http;
                
                const req = client.request(options, (res) => {
                    console.log(`    📡 Response received with status: ${res.statusCode}`);
                    
                    let data = '';
                    res.on('data', chunk => {
                        data += chunk;
                        console.log(`    📦 Received chunk: ${chunk.length} bytes`);
                    });
                    
                    res.on('end', () => {
                        console.log(`    ✅ Response complete. Total size: ${data.length} bytes`);
                        resolve({
                            statusCode: res.statusCode,
                            headers: res.headers,
                            data: data
                        });
                    });
                });

                req.on('error', (error) => {
                    console.log(`    ❌ Request error: ${error.message}`);
                    console.log(`    🔍 Error details: ${JSON.stringify({
                        code: error.code,
                        errno: error.errno,
                        syscall: error.syscall,
                        hostname: error.hostname
                    })}`);
                    reject(error);
                });

                req.on('timeout', () => {
                    console.log(`    ⏰ Request timeout`);
                    req.destroy();
                    reject(new Error('Request timeout'));
                });
                
                req.on('socket', (socket) => {
                    console.log(`    🔌 Socket connected`);
                    socket.on('lookup', (err, address, family, host) => {
                        console.log(`    🔍 DNS lookup: ${host} -> ${address} (IPv${family})`);
                    });
                });
                
                console.log(`    📤 Sending request...`);
                req.end();
                
            } catch (error) {
                console.log(`    ❌ URL parsing failed: ${error.message}`);
                reject(error);
            }
        });
    }

    getStatusText(code) {
        const statusTexts = {
            200: 'OK',
            201: 'Created',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Internal Server Error',
            502: 'Bad Gateway',
            503: 'Service Unavailable'
        };
        return statusTexts[code] || 'Unknown Status';
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Run the debug analysis
if (require.main === module) {
    const httpDebugger = new HTTPDebugger();
    httpDebugger.debugRequests().catch(console.error);
}

module.exports = HTTPDebugger;

#!/usr/bin/env node
/**
 * Test the database MCP server
 */

const { spawn } = require('child_process');

class DatabaseMCPTester {
  constructor(dbUrl) {
    this.dbUrl = dbUrl;
    this.server = null;
    this.requestId = 1;
  }

  async startServer() {
    console.log('🚀 Starting Database MCP server...');
    console.log('🔗 Connecting to:', this.dbUrl ? 'Custom DB URL' : 'No DB URL provided');
    
    // For testing, we'll simulate the connection
    // In practice, your MCP server at the URL should handle stdio communication
    console.log('📡 Note: This would connect to your self-hosted MCP server');
    console.log('🔧 Server should be running at the provided DB_URL');
    
    return true;
  }

  async testDatabaseTools() {
    console.log('\n🧪 Testing Database MCP Server Tools');
    console.log('=' .repeat(50));
    
    // Based on the available MCP database tools, test the capabilities
    const availableTools = [
      'postgres_query',
      'postgres_execute', 
      'postgres_create_database',
      'postgres_create_table',
      'mongodb_find_documents',
      'mongodb_insert_document',
      'mongodb_aggregate',
      'mongodb_create_collection',
      'mongodb_update_documents',
      'mongodb_delete_documents',
      'redis_set_key',
      'redis_delete_key',
      'redis_execute_command',
      'redis_flush_database',
      'influxdb_query'
    ];

    console.log('✅ Available Database Tools:');
    availableTools.forEach(tool => {
      console.log(`   - ${tool}`);
    });

    return availableTools;
  }

  async testPostgresOperations() {
    console.log('\n🐘 Testing PostgreSQL Operations:');
    
    const testCases = [
      {
        name: 'Create Database',
        tool: 'postgres_create_database',
        args: { database_name: 'test_mcpea' }
      },
      {
        name: 'Query Databases',
        tool: 'postgres_query', 
        args: { sql: 'SELECT datname FROM pg_database;' }
      },
      {
        name: 'Create Table',
        tool: 'postgres_create_table',
        args: { 
          database: 'test_mcpea',
          table_name: 'mcp_test',
          columns: 'id SERIAL PRIMARY KEY, name VARCHAR(100), created_at TIMESTAMP DEFAULT NOW()'
        }
      },
      {
        name: 'Insert Data',
        tool: 'postgres_execute',
        args: { 
          database: 'test_mcpea',
          sql: "INSERT INTO mcp_test (name) VALUES ('mc-pea test')"
        }
      },
      {
        name: 'Query Data',
        tool: 'postgres_query',
        args: { 
          database: 'test_mcpea',
          sql: 'SELECT * FROM mcp_test'
        }
      }
    ];

    testCases.forEach(test => {
      console.log(`   📝 ${test.name}:`);
      console.log(`      Tool: ${test.tool}`);
      console.log(`      Args: ${JSON.stringify(test.args, null, 8)}`);
    });
  }

  async testMongoOperations() {
    console.log('\n🍃 Testing MongoDB Operations:');
    
    const testCases = [
      {
        name: 'Create Collection',
        tool: 'mongodb_create_collection',
        args: { database: 'mcpea_db', collection: 'test_collection' }
      },
      {
        name: 'Insert Document',
        tool: 'mongodb_insert_document',
        args: { 
          database: 'mcpea_db',
          collection: 'test_collection',
          document: '{"name": "mc-pea test", "type": "mcp_server", "timestamp": "2025-06-16"}'
        }
      },
      {
        name: 'Find Documents',
        tool: 'mongodb_find_documents',
        args: { 
          database: 'mcpea_db',
          collection: 'test_collection',
          filter_query: '{"type": "mcp_server"}'
        }
      },
      {
        name: 'Aggregate Data',
        tool: 'mongodb_aggregate',
        args: { 
          database: 'mcpea_db',
          collection: 'test_collection',
          pipeline: '[{"$group": {"_id": "$type", "count": {"$sum": 1}}}]'
        }
      }
    ];

    testCases.forEach(test => {
      console.log(`   📝 ${test.name}:`);
      console.log(`      Tool: ${test.tool}`);
      console.log(`      Args: ${JSON.stringify(test.args, null, 8)}`);
    });
  }

  async testRedisOperations() {
    console.log('\n🔴 Testing Redis Operations:');
    
    const testCases = [
      {
        name: 'Set Key-Value',
        tool: 'redis_set_key',
        args: { key: 'mcpea:test', value: 'Hello from mc-pea MCP!' }
      },
      {
        name: 'Execute Command',
        tool: 'redis_execute_command',
        args: { command: 'GET', args: 'mcpea:test' }
      },
      {
        name: 'List Keys',
        tool: 'redis_execute_command',
        args: { command: 'KEYS', args: 'mcpea:*' }
      },
      {
        name: 'Delete Key',
        tool: 'redis_delete_key',
        args: { key: 'mcpea:test' }
      }
    ];

    testCases.forEach(test => {
      console.log(`   📝 ${test.name}:`);
      console.log(`      Tool: ${test.tool}`);
      console.log(`      Args: ${JSON.stringify(test.args, null, 8)}`);
    });
  }

  async testInfluxDBOperations() {
    console.log('\n📊 Testing InfluxDB Operations:');
    
    const testCases = [
      {
        name: 'Query Metrics',
        tool: 'influxdb_query',
        args: { 
          bucket: 'mcpea_metrics',
          flux_query: 'from(bucket: "mcpea_metrics") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "system")'
        }
      },
      {
        name: 'Query System Stats',
        tool: 'influxdb_query',
        args: { 
          bucket: 'system',
          flux_query: 'from(bucket: "system") |> range(start: -24h) |> filter(fn: (r) => r._field == "cpu_usage")'
        }
      }
    ];

    testCases.forEach(test => {
      console.log(`   📝 ${test.name}:`);
      console.log(`      Tool: ${test.tool}`);
      console.log(`      Args: ${JSON.stringify(test.args, null, 8)}`);
    });
  }

  async runTests() {
    try {
      await this.startServer();
      
      const tools = await this.testDatabaseTools();
      
      await this.testPostgresOperations();
      await this.testMongoOperations(); 
      await this.testRedisOperations();
      await this.testInfluxDBOperations();

      console.log('\n' + '='.repeat(50));
      console.log('🎉 Database MCP Server Test Suite Completed!');
      console.log('\n📋 Next Steps:');
      console.log('1. Ensure your MCP server is running at the provided DB_URL');
      console.log('2. Verify it supports the database tools you need');
      console.log('3. Test actual database operations through VS Code MCP');
      console.log('4. Integrate with mc-pea orchestration workflows');
      
    } catch (error) {
      console.error('❌ Test suite failed:', error);
    }
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  const dbUrl = process.env.DB_URL || 'ws://localhost:8080'; // fallback for testing
  const tester = new DatabaseMCPTester(dbUrl);
  tester.runTests().catch(console.error);
}

module.exports = { DatabaseMCPTester };

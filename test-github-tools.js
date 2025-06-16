#!/usr/bin/env node
/**
 * Test various GitHub MCP server tools
 */

const { spawn } = require('child_process');

class GitHubMCPTester {
  constructor() {
    this.server = null;
    this.requestId = 1;
  }

  async startServer() {
    console.log('🚀 Starting GitHub MCP server...');
    
    this.server = spawn('./github-mcp-server.exe', ['stdio'], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_PERSONAL_ACCESS_TOKEN || 'test_token'
      }
    });

    this.server.stderr.on('data', (data) => {
      console.log('Server log:', data.toString());
    });

    // Wait a moment for server to start
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  async sendRequest(method, params = {}) {
    return new Promise((resolve, reject) => {
      const request = {
        jsonrpc: '2.0',
        id: this.requestId++,
        method,
        params
      };

      console.log(`\n📤 Sending: ${method}`);
      console.log(`   Params:`, JSON.stringify(params, null, 2));

      let response = '';
      const timeout = setTimeout(() => {
        reject(new Error('Request timeout'));
      }, 10000);

      const onData = (data) => {
        response += data.toString();
        
        // Try to parse complete JSON response
        const lines = response.split('\n');
        for (const line of lines) {
          if (line.trim().startsWith('{')) {
            try {
              const parsed = JSON.parse(line);
              if (parsed.id === request.id) {
                clearTimeout(timeout);
                this.server.stdout.off('data', onData);
                resolve(parsed);
                return;
              }
            } catch (e) {
              // Continue trying to parse
            }
          }
        }
      };

      this.server.stdout.on('data', onData);
      this.server.stdin.write(JSON.stringify(request) + '\n');
    });
  }

  async testGetMe() {
    try {
      const response = await this.sendRequest('tools/call', {
        name: 'get_me',
        arguments: { reason: 'Testing MCP server functionality' }
      });
      
      console.log('✅ get_me result:');
      if (response.result?.content?.[0]?.text) {
        const userData = JSON.parse(response.result.content[0].text);
        console.log(`   User: ${userData.login} (${userData.name})`);
        console.log(`   Company: ${userData.company || 'N/A'}`);
        console.log(`   Public repos: ${userData.public_repos}`);
        console.log(`   Followers: ${userData.followers}`);
      } else {
        console.log('   Response:', JSON.stringify(response, null, 2));
      }
    } catch (error) {
      console.log('❌ get_me failed:', error.message);
    }
  }

  async testSearchRepositories() {
    try {
      const response = await this.sendRequest('tools/call', {
        name: 'search_repositories',
        arguments: { 
          query: 'owner:LimbicNode42 mc-pea',
          perPage: 5
        }
      });
      
      console.log('✅ search_repositories result:');
      if (response.result?.content?.[0]?.text) {
        const searchData = JSON.parse(response.result.content[0].text);
        console.log(`   Found ${searchData.total_count} repositories`);
        searchData.items?.slice(0, 3).forEach(repo => {
          console.log(`   - ${repo.full_name}: ${repo.description || 'No description'}`);
        });
      } else {
        console.log('   Response:', JSON.stringify(response, null, 2));
      }
    } catch (error) {
      console.log('❌ search_repositories failed:', error.message);
    }
  }

  async testListNotifications() {
    try {
      const response = await this.sendRequest('tools/call', {
        name: 'list_notifications',
        arguments: { 
          perPage: 3,
          filter: 'default'
        }
      });
      
      console.log('✅ list_notifications result:');
      if (response.result?.content?.[0]?.text) {
        const notifications = JSON.parse(response.result.content[0].text);
        console.log(`   Found ${notifications.length} notifications`);
        notifications.slice(0, 3).forEach(notif => {
          console.log(`   - ${notif.subject?.title} (${notif.reason})`);
          console.log(`     Repo: ${notif.repository?.full_name}`);
        });
      } else {
        console.log('   Response:', JSON.stringify(response, null, 2));
      }
    } catch (error) {
      console.log('❌ list_notifications failed:', error.message);
    }
  }

  async testGetFileContents() {
    try {
      const response = await this.sendRequest('tools/call', {
        name: 'get_file_contents',
        arguments: { 
          owner: 'LimbicNode42',
          repo: 'mc-pea',
          path: 'README.md'
        }
      });
      
      console.log('✅ get_file_contents result:');
      if (response.result?.content?.[0]?.text) {
        const fileData = JSON.parse(response.result.content[0].text);
        const content = Buffer.from(fileData.content, 'base64').toString('utf-8');
        console.log(`   File: ${fileData.name} (${fileData.size} bytes)`);
        console.log(`   First 100 chars: ${content.substring(0, 100)}...`);
      } else {
        console.log('   Response:', JSON.stringify(response, null, 2));
      }
    } catch (error) {
      console.log('❌ get_file_contents failed:', error.message);
    }
  }

  async testListIssues() {
    try {
      const response = await this.sendRequest('tools/call', {
        name: 'list_issues',
        arguments: { 
          owner: 'LimbicNode42',
          repo: 'mc-pea',
          state: 'all',
          perPage: 3
        }
      });
      
      console.log('✅ list_issues result:');
      if (response.result?.content?.[0]?.text) {
        const issues = JSON.parse(response.result.content[0].text);
        console.log(`   Found ${issues.length} issues`);
        issues.slice(0, 3).forEach(issue => {
          console.log(`   - #${issue.number}: ${issue.title} (${issue.state})`);
        });
      } else {
        console.log('   Response:', JSON.stringify(response, null, 2));
      }
    } catch (error) {
      console.log('❌ list_issues failed:', error.message);
    }
  }

  async runTests() {
    try {
      await this.startServer();
      
      console.log('\n🧪 Testing GitHub MCP Server Tools\n');
      console.log('=' .repeat(50));

      await this.testGetMe();
      await this.testSearchRepositories();
      await this.testListNotifications();
      await this.testGetFileContents();
      await this.testListIssues();

      console.log('\n' + '='.repeat(50));
      console.log('🎉 Tool testing completed!');
      
    } catch (error) {
      console.error('❌ Test suite failed:', error);
    } finally {
      if (this.server) {
        this.server.kill();
      }
    }
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  const tester = new GitHubMCPTester();
  tester.runTests().catch(console.error);
}

module.exports = { GitHubMCPTester };

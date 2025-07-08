# AI Orchestration Integration for MC-PEA

## Overview
This document outlines how to integrate Claude Sonnet 4 in agentic mode for programmatic MCP server generation, moving from manual GitHub Copilot assistance to automated AI orchestration.

## Option 1: Anthropic API Direct Integration (Recommended)

### Setup
```typescript
// src/services/anthropic-client.ts
import Anthropic from '@anthropic-ai/sdk';

export class AnthropicOrchestrator {
  private client: Anthropic;

  constructor(apiKey: string) {
    this.client = new Anthropic({
      apiKey: apiKey,
    });
  }

  async generateMCPServer(specification: MCPServerSpec): Promise<GeneratedServer> {
    const messages = this.buildAgenticPrompt(specification);
    
    const response = await this.client.messages.create({
      model: "claude-3-5-sonnet-20241022",
      max_tokens: 8000,
      messages: messages,
      tools: this.getAgenticTools(),
      tool_choice: { type: "auto" }
    });

    return this.processAgenticResponse(response);
  }

  private buildAgenticPrompt(spec: MCPServerSpec): Anthropic.MessageParam[] {
    return [
      {
        role: "user",
        content: `Generate a complete MCP server based on this specification:

## Server Specification
- Name: ${spec.name}
- Description: ${spec.description}
- Target API: ${spec.targetAPI}
- Authentication: ${spec.authentication}
- Tools Required: ${spec.tools.join(', ')}
- Resources Required: ${spec.resources.join(', ')}

## Requirements
1. Follow MC-PEA template structure from templates/mcp-server-template/
2. Use TypeScript with strict mode
3. Implement proper error handling and validation
4. Include comprehensive JSDoc documentation
5. Generate complete test suite
6. Follow MCP SDK patterns exactly

## Actions Required
1. Analyze the target API documentation
2. Design the MCP server architecture
3. Generate all source files (tools, resources, types)
4. Create comprehensive tests
5. Generate documentation
6. Create Docker configuration

Please work through this systematically, using the available tools to create files and validate the implementation.`
      }
    ];
  }

  private getAgenticTools(): Anthropic.Tool[] {
    return [
      {
        name: "create_file",
        description: "Create a new file with specified content",
        input_schema: {
          type: "object",
          properties: {
            path: { type: "string", description: "File path relative to server root" },
            content: { type: "string", description: "File content" }
          },
          required: ["path", "content"]
        }
      },
      {
        name: "analyze_api_documentation",
        description: "Analyze external API documentation to understand endpoints and schemas",
        input_schema: {
          type: "object",
          properties: {
            apiUrl: { type: "string", description: "API documentation URL" },
            apiType: { type: "string", enum: ["rest", "graphql", "grpc"] }
          },
          required: ["apiUrl", "apiType"]
        }
      },
      {
        name: "validate_mcp_compliance",
        description: "Validate generated code against MCP protocol requirements",
        input_schema: {
          type: "object",
          properties: {
            serverPath: { type: "string", description: "Path to generated server" }
          },
          required: ["serverPath"]
        }
      },
      {
        name: "run_tests",
        description: "Execute test suite for generated MCP server",
        input_schema: {
          type: "object",
          properties: {
            serverPath: { type: "string", description: "Path to server root" },
            testType: { type: "string", enum: ["unit", "integration", "mcp-client"] }
          },
          required: ["serverPath", "testType"]
        }
      }
    ];
  }

  private async processAgenticResponse(response: Anthropic.Message): Promise<GeneratedServer> {
    const result: GeneratedServer = {
      files: new Map(),
      tests: new Map(),
      documentation: "",
      errors: [],
      warnings: []
    };

    // Process tool calls from Claude's response
    for (const content of response.content) {
      if (content.type === "tool_use") {
        await this.executeToolCall(content, result);
      }
    }

    return result;
  }

  private async executeToolCall(toolCall: any, result: GeneratedServer): Promise<void> {
    switch (toolCall.name) {
      case "create_file":
        result.files.set(toolCall.input.path, toolCall.input.content);
        break;
      
      case "analyze_api_documentation":
        const apiAnalysis = await this.analyzeAPI(toolCall.input);
        // Store analysis for use in generation
        break;
      
      case "validate_mcp_compliance":
        const validation = await this.validateCompliance(toolCall.input.serverPath);
        if (!validation.isCompliant) {
          result.errors.push(...validation.errors);
        }
        break;
      
      case "run_tests":
        const testResults = await this.runTests(toolCall.input);
        if (!testResults.passed) {
          result.errors.push(...testResults.failures);
        }
        break;
    }
  }
}
```

### Integration with MC-PEA MCP Server
```typescript
// src/tools/generate-mcp-server.ts
import { AnthropicOrchestrator } from '../services/anthropic-client.js';

export const generateMCPServerTool = {
  name: "generate_mcp_server",
  description: "Generate a complete MCP server using AI orchestration",
  inputSchema: {
    type: "object",
    properties: {
      specification: {
        type: "object",
        properties: {
          name: { type: "string", description: "Server name (kebab-case)" },
          description: { type: "string", description: "Server description" },
          targetAPI: { type: "string", description: "Target API base URL or service" },
          authentication: { 
            type: "string", 
            enum: ["none", "api-key", "oauth2", "basic", "bearer"],
            description: "Authentication method required"
          },
          tools: {
            type: "array",
            items: { type: "string" },
            description: "List of tools/operations to implement"
          },
          resources: {
            type: "array", 
            items: { type: "string" },
            description: "List of resources to expose"
          }
        },
        required: ["name", "description", "targetAPI", "tools", "resources"]
      }
    },
    required: ["specification"]
  }
};

export async function generateMCPServer(args: { specification: MCPServerSpec }) {
  const orchestrator = new AnthropicOrchestrator(process.env.ANTHROPIC_API_KEY!);
  
  try {
    // Generate server using AI orchestration
    const generatedServer = await orchestrator.generateMCPServer(args.specification);
    
    // Create server directory
    const serverPath = `mcp-servers/${args.specification.name}`;
    await fs.mkdir(serverPath, { recursive: true });
    
    // Write all generated files
    for (const [filePath, content] of generatedServer.files) {
      const fullPath = path.join(serverPath, filePath);
      await fs.mkdir(path.dirname(fullPath), { recursive: true });
      await fs.writeFile(fullPath, content, 'utf8');
    }
    
    // Run initial validation
    const validation = await validateGeneratedServer(serverPath);
    
    return {
      content: [
        {
          type: "text",
          text: `Successfully generated MCP server: ${args.specification.name}
          
## Generated Files:
${Array.from(generatedServer.files.keys()).map(f => `- ${f}`).join('\n')}

## Validation Results:
- Files created: ${generatedServer.files.size}
- Errors: ${generatedServer.errors.length}
- Warnings: ${generatedServer.warnings.length}

## Next Steps:
1. Review generated code in ${serverPath}
2. Run tests: npm test
3. Build server: npm run build
4. Validate MCP compliance: npm run validate-mcp

${generatedServer.errors.length > 0 ? `\n## Errors to Address:\n${generatedServer.errors.join('\n')}` : ''}
${generatedServer.warnings.length > 0 ? `\n## Warnings:\n${generatedServer.warnings.join('\n')}` : ''}`
        }
      ]
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text", 
          text: `Error generating MCP server: ${error.message}`
        }
      ]
    };
  }
}
```

## Option 2: OpenAI API with Function Calling

### Alternative using OpenAI GPT-4
```typescript
// src/services/openai-orchestrator.ts
import OpenAI from 'openai';

export class OpenAIOrchestrator {
  private client: OpenAI;

  constructor(apiKey: string) {
    this.client = new OpenAI({ apiKey });
  }

  async generateMCPServer(specification: MCPServerSpec): Promise<GeneratedServer> {
    const completion = await this.client.chat.completions.create({
      model: "gpt-4-0125-preview",
      messages: [
        {
          role: "system",
          content: "You are an expert MCP server generator. Use the provided tools to create complete, production-ready MCP servers following MC-PEA standards."
        },
        {
          role: "user", 
          content: this.buildPrompt(specification)
        }
      ],
      functions: this.getFunctions(),
      function_call: "auto",
      max_tokens: 8000
    });

    return this.processResponse(completion);
  }
}
```

## Option 3: Local AI Models (Ollama/LM Studio)

### Self-hosted approach for data privacy
```typescript
// src/services/local-ai-orchestrator.ts
export class LocalAIOrchestrator {
  private baseUrl: string;

  constructor(baseUrl = "http://localhost:11434") {
    this.baseUrl = baseUrl;
  }

  async generateMCPServer(specification: MCPServerSpec): Promise<GeneratedServer> {
    // Use Ollama API to run Codestral, DeepSeek Coder, or Code Llama locally
    const response = await fetch(`${this.baseUrl}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: "codestral:latest", // or "deepseek-coder:6.7b"
        prompt: this.buildPrompt(specification),
        stream: false
      })
    });

    return this.processLocalResponse(response);
  }
}
```

## Option 4: Multi-Model Orchestration

### Use different models for different tasks
```typescript
// src/services/multi-model-orchestrator.ts
export class MultiModelOrchestrator {
  private anthropic: AnthropicOrchestrator;
  private openai: OpenAIOrchestrator;

  async generateMCPServer(specification: MCPServerSpec): Promise<GeneratedServer> {
    // Use Claude for architecture and design
    const architecture = await this.anthropic.designArchitecture(specification);
    
    // Use GPT-4 for code generation
    const implementation = await this.openai.generateImplementation(architecture);
    
    // Use Claude for testing and validation
    const tests = await this.anthropic.generateTests(implementation);
    
    return this.combineResults(architecture, implementation, tests);
  }
}
```

## UI Integration

### React form for MCP server specification
```typescript
// src/components/MCPServerGenerator.tsx
import React, { useState } from 'react';

interface MCPServerSpec {
  name: string;
  description: string;
  targetAPI: string;
  authentication: string;
  tools: string[];
  resources: string[];
}

export function MCPServerGenerator() {
  const [spec, setSpec] = useState<MCPServerSpec>({
    name: '',
    description: '',
    targetAPI: '',
    authentication: 'none',
    tools: [''],
    resources: ['']
  });
  
  const [generating, setGenerating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);

    try {
      // Call MC-PEA MCP server to generate new server
      const response = await fetch('/api/mcp/generate-server', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ specification: spec })
      });

      const result = await response.json();
      console.log('Generated server:', result);
    } catch (error) {
      console.error('Generation failed:', error);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium">Server Name</label>
        <input
          type="text"
          value={spec.name}
          onChange={(e) => setSpec({ ...spec, name: e.target.value })}
          placeholder="my-api-mcp-server"
          className="mt-1 block w-full rounded-md border-gray-300"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium">Description</label>
        <textarea
          value={spec.description}
          onChange={(e) => setSpec({ ...spec, description: e.target.value })}
          placeholder="MCP server for integrating with My API service"
          className="mt-1 block w-full rounded-md border-gray-300"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium">Target API</label>
        <input
          type="url"
          value={spec.targetAPI}
          onChange={(e) => setSpec({ ...spec, targetAPI: e.target.value })}
          placeholder="https://api.example.com/v1"
          className="mt-1 block w-full rounded-md border-gray-300"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium">Authentication</label>
        <select
          value={spec.authentication}
          onChange={(e) => setSpec({ ...spec, authentication: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300"
        >
          <option value="none">None</option>
          <option value="api-key">API Key</option>
          <option value="oauth2">OAuth 2.0</option>
          <option value="basic">Basic Auth</option>
          <option value="bearer">Bearer Token</option>
        </select>
      </div>

      {/* Dynamic tool and resource inputs */}
      <div>
        <label className="block text-sm font-medium">Tools</label>
        {spec.tools.map((tool, index) => (
          <input
            key={index}
            type="text"
            value={tool}
            onChange={(e) => {
              const newTools = [...spec.tools];
              newTools[index] = e.target.value;
              setSpec({ ...spec, tools: newTools });
            }}
            placeholder="get_user, create_post, delete_comment"
            className="mt-1 block w-full rounded-md border-gray-300"
          />
        ))}
        <button
          type="button"
          onClick={() => setSpec({ ...spec, tools: [...spec.tools, ''] })}
          className="mt-2 text-sm text-blue-600"
        >
          Add Tool
        </button>
      </div>

      <button
        type="submit"
        disabled={generating}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md disabled:opacity-50"
      >
        {generating ? 'Generating...' : 'Generate MCP Server'}
      </button>
    </form>
  );
}
```

## Recommended Approach

**Start with Option 1 (Anthropic API)** because:

1. **Claude Sonnet 4 excels at code generation** and architectural thinking
2. **Function calling support** allows true agentic behavior  
3. **Large context window** can handle entire MCP server specifications
4. **Strong instruction following** for complex multi-step tasks
5. **JSON mode support** for structured outputs

**Environment Setup:**
```bash
npm install @anthropic-ai/sdk
export ANTHROPIC_API_KEY="your-api-key"
```

**Next Steps:**
1. Implement the `AnthropicOrchestrator` class
2. Add the MCP server generation tool to MC-PEA
3. Build the React UI for specifications
4. Test with a simple API integration (like JSONPlaceholder)
5. Iterate and improve based on results

This approach gives you programmatic AI orchestration while maintaining the quality and consistency you've achieved with manual Copilot assistance.

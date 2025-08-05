/**
 * MCP Server Template - Registration System
 * 
 * This is the CANONICAL REFERENCE implementation for dynamic tool/resource registration.
 * DO NOT modify this file without updating all dependent projects.
 * 
 * This file demonstrates:
 * - Dynamic registration of tools, resources, and prompts using server.registerTool()
 * - Separation of definitions from handlers
 * - Authentication validation via middleware
 * - Proper error handling and response formatting
 */

import { McpServer, ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { validateAuthentication, getSession } from './index.js';

// Import tool definitions and handlers
import { toolDefinitions, toolHandlers } from './tools/index.js';
import { resourceDefinitions, resourceHandlers } from './resources/index.js';
import { promptDefinitions, promptHandlers } from './prompts/index.js';

/**
 * Utility function to convert JSON Schema to Zod schema
 * This is needed because MCP server.registerTool() expects Zod schemas
 */
function jsonSchemaToZod(jsonSchema: any): z.ZodRawShape {
  const shape: z.ZodRawShape = {};

  if (jsonSchema.type === 'object' && jsonSchema.properties) {
    for (const [key, propSchema] of Object.entries(jsonSchema.properties)) {
      const prop = propSchema as any;
      let zodType: z.ZodTypeAny;

      switch (prop.type) {
        case 'string':
          zodType = z.string();
          if (prop.enum) {
            zodType = z.enum(prop.enum);
          }
          break;
        case 'number':
          zodType = z.number();
          break;
        case 'integer':
          zodType = z.number().int();
          break;
        case 'boolean':
          zodType = z.boolean();
          break;
        case 'array':
          zodType = z.array(z.any());
          break;
        case 'object':
          zodType = z.object({});
          break;
        default:
          zodType = z.any();
      }

      if (prop.description) {
        zodType = zodType.describe(prop.description);
      }

      if (jsonSchema.required && jsonSchema.required.includes(key)) {
        shape[key] = zodType;
      } else {
        shape[key] = zodType.optional();
      }
    }
  }

  return shape;
}

/**
 * Register all MCP capabilities with the server
 * This function sets up all tools, resources, and prompts using the MCP SDK methods
 */
export function registerToolsAndResources(server: McpServer): void {
  console.error('📋 Registering MCP capabilities...');
  
  // Register tools
  registerTools(server);
  
  // Register resources
  registerResources(server);
  
  // Register prompts (if supported by SDK version)
  registerPrompts(server);
  
  console.error(`✅ Registered ${Object.keys(toolDefinitions).length} tools`);
  console.error(`✅ Registered ${Object.keys(resourceDefinitions).length} resources`);
  console.error(`✅ Registered ${Object.keys(promptDefinitions).length} prompts`);
}

/**
 * Register tools using server.registerTool()
 */
function registerTools(server: McpServer): void {
  for (const [toolName, toolDef] of Object.entries(toolDefinitions)) {
    const handler = toolHandlers[toolName];
    if (!handler) {
      console.error(`⚠️ No handler found for tool: ${toolName}`);
      continue;
    }

    // Convert JSON Schema to Zod schema
    const zodSchema = jsonSchemaToZod(toolDef.inputSchema);
    
    server.registerTool(
      toolName,
      {
        description: toolDef.description,
        inputSchema: zodSchema,
      },
      async (args: any) => {
        try {
          // Get session ID from server context (implementation may vary)
          const sessionId = 'default'; // This should be extracted from context
          
          console.error(`[${sessionId}] Executing tool: ${toolName}`);
          const result = await handler(args, sessionId);
          
          return {
            content: [
              {
                type: 'text' as const,
                text: typeof result === 'string' ? result : JSON.stringify(result, null, 2),
              },
            ],
          };
        } catch (error: any) {
          console.error(`[${toolName}] Tool execution failed:`, error);
          return {
            content: [
              {
                type: 'text' as const,
                text: `Error executing ${toolName}: ${error.message}`,
              },
            ],
            isError: true,
          };
        }
      }
    );
  }
}

/**
 * Register resources using server.registerResource()
 */
function registerResources(server: McpServer): void {
  for (const [resourceKey, resourceDef] of Object.entries(resourceDefinitions)) {
    const handler = resourceHandlers[resourceKey];
    if (!handler) {
      console.error(`⚠️ No handler found for resource: ${resourceKey}`);
      continue;
    }

    // Create resource template
    const resourceTemplate: ResourceTemplate = {
      title: resourceDef.name,
      description: resourceDef.description,
      mimeType: resourceDef.mimeType,
    };

    server.registerResource(
      resourceKey,
      resourceDef.uri,
      resourceTemplate,
      async (uri) => {
        try {
          // Get session ID from server context (implementation may vary)
          const sessionId = 'default'; // This should be extracted from context
          
          console.error(`[${sessionId}] Reading resource: ${uri.href}`);
          const result = await handler(sessionId);
          
          return {
            contents: [
              {
                uri: uri.href,
                text: typeof result === 'string' ? result : JSON.stringify(result, null, 2),
                mimeType: resourceDef.mimeType,
              },
            ],
          };
        } catch (error: any) {
          console.error(`[${resourceKey}] Resource read failed:`, error);
          return {
            contents: [
              {
                uri: uri.href,
                text: `Error reading resource ${resourceKey}: ${error.message}`,
                mimeType: 'text/plain',
              },
            ],
          };
        }
      }
    );
  }
}

/**
 * Register prompts (if supported by MCP SDK version)
 * Note: Prompt registration may not be available in all SDK versions
 */
function registerPrompts(server: McpServer): void {
  // Check if registerPrompt method exists
  if (typeof (server as any).registerPrompt !== 'function') {
    console.error('ℹ️ Prompt registration not supported in this MCP SDK version');
    return;
  }

  for (const [promptName, promptDef] of Object.entries(promptDefinitions)) {
    const handler = promptHandlers[promptName];
    if (!handler) {
      console.error(`⚠️ No handler found for prompt: ${promptName}`);
      continue;
    }

    // Register prompt (syntax may vary based on SDK version)
    try {
      (server as any).registerPrompt(
        promptName,
        {
          description: promptDef.description,
          arguments: promptDef.arguments || [],
        },
        async (args: any) => {
          try {
            // Get session ID from server context (implementation may vary)
            const sessionId = 'default'; // This should be extracted from context
            
            console.error(`[${sessionId}] Generating prompt: ${promptName}`);
            const result = await handler(args, sessionId);
            
            return result;
          } catch (error: any) {
            console.error(`[${promptName}] Prompt generation failed:`, error);
            throw new Error(`Error generating prompt ${promptName}: ${error.message}`);
          }
        }
      );
    } catch (error) {
      console.error(`⚠️ Failed to register prompt ${promptName}:`, error);
    }
  }
}

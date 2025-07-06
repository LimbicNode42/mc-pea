/**
 * Prompt Definitions and Handlers
 * 
 * This file contains example prompt definitions and their corresponding handlers.
 * This is a template - replace with your actual prompt implementations.
 */

// Prompt Definitions
export const promptDefinitions = {
  system_analysis: {
    name: 'system_analysis',
    description: 'Generate system analysis prompt with current metrics',
    arguments: [
      {
        name: 'analysis_type',
        description: 'Type of analysis to perform',
        required: false
      }
    ]
  },
  
  task_instructions: {
    name: 'task_instructions',
    description: 'Generate task-specific instructions',
    arguments: [
      {
        name: 'task_name',
        description: 'Name of the task',
        required: true
      },
      {
        name: 'complexity',
        description: 'Task complexity level',
        required: false
      }
    ]
  }
};

// Prompt Handlers
export const promptHandlers = {
  system_analysis: async (args: any, sessionId: string) => {
    const analysisType = args.analysis_type || 'general';
    
    return {
      description: `System analysis prompt for ${analysisType} analysis`,
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: `Please analyze the current system status.
            
Analysis Type: ${analysisType}
Session ID: ${sessionId}
Timestamp: ${new Date().toISOString()}

Please provide insights on:
1. System performance
2. Resource utilization
3. Recommendations for optimization`
          }
        }
      ]
    };
  },
  
  task_instructions: async (args: any, sessionId: string) => {
    const taskName = args.task_name;
    const complexity = args.complexity || 'medium';
    
    return {
      description: `Task instructions for ${taskName}`,
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: `Task: ${taskName}
Complexity: ${complexity}
Session: ${sessionId}

Please provide detailed instructions for completing this task, considering the ${complexity} complexity level.`
          }
        }
      ]
    };
  }
};

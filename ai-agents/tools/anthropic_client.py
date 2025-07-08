"""Anthropic client wrapper for AI agents."""

import logging
from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from pydantic import BaseModel


class AnthropicConfig(BaseModel):
    """Configuration for Anthropic client."""
    
    api_key: str
    model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 4000
    temperature: float = 0.7


class AnthropicClientWrapper:
    """Wrapper for Anthropic client with additional utilities."""
    
    def __init__(
        self,
        config: AnthropicConfig,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize Anthropic client wrapper.
        
        Args:
            config: Client configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger("anthropic_client")
        
        # Initialize Anthropic client
        self.client = Anthropic(api_key=config.api_key)
        
        self.logger.info("Anthropic client initialized")
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using Claude.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
            
        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.config.model,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
            "messages": messages,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        try:
            response = await self.client.messages.create(**kwargs)
            
            generated_text = response.content[0].text
            
            self.logger.debug(f"Generated {len(generated_text)} characters")
            
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Failed to generate text: {e}")
            raise
    
    async def generate_code(
        self,
        prompt: str,
        language: str = "typescript",
        context: Optional[str] = None,
    ) -> str:
        """Generate code using Claude.
        
        Args:
            prompt: Code generation prompt
            language: Programming language
            context: Additional context
            
        Returns:
            Generated code
        """
        system_prompt = f"""You are an expert {language} developer. Generate clean, well-documented, 
production-ready code that follows best practices and industry standards.

Always include:
- Proper type annotations
- Error handling
- Documentation comments
- Clear variable names
- Modular structure
"""
        
        if context:
            full_prompt = f"Context:\n{context}\n\nRequest:\n{prompt}"
        else:
            full_prompt = prompt
        
        return await self.generate_text(
            prompt=full_prompt,
            system_prompt=system_prompt,
        )
    
    async def analyze_api(
        self,
        api_documentation: str,
        api_type: str = "REST",
    ) -> Dict[str, Any]:
        """Analyze API documentation to extract structure.
        
        Args:
            api_documentation: API documentation text
            api_type: Type of API (REST, GraphQL, etc.)
            
        Returns:
            Analyzed API structure
        """
        prompt = f"""Analyze the following {api_type} API documentation and extract:

1. Available endpoints/operations
2. Request/response schemas
3. Authentication requirements
4. Required parameters
5. Optional parameters
6. Error handling patterns

API Documentation:
{api_documentation}

Return the analysis as a structured summary with clear sections for each component.
"""
        
        analysis = await self.generate_text(prompt)
        
        # Parse the analysis (in a real implementation, you might use structured output)
        return {
            "analysis": analysis,
            "api_type": api_type,
            "parsed_endpoints": [],  # Would extract from analysis
            "authentication": {},  # Would extract from analysis
        }
    
    async def create_mcp_tool(
        self,
        tool_name: str,
        tool_description: str,
        api_context: Dict[str, Any],
        parameters: List[Dict[str, Any]],
    ) -> str:
        """Generate MCP tool implementation.
        
        Args:
            tool_name: Name of the tool
            tool_description: Description of what the tool does
            api_context: API context information
            parameters: Tool parameters
            
        Returns:
            Generated tool code
        """
        prompt = f"""Generate a TypeScript implementation for an MCP tool with the following specification:

Tool Name: {tool_name}
Description: {tool_description}

Parameters:
{chr(10).join(f"- {param['name']}: {param.get('type', 'string')} - {param.get('description', 'No description')}" for param in parameters)}

API Context:
{api_context}

The implementation should:
1. Use proper MCP SDK patterns
2. Include input validation
3. Handle errors gracefully
4. Return properly formatted responses
5. Include JSDoc documentation
6. Follow TypeScript best practices

Generate only the tool implementation function.
"""
        
        return await self.generate_code(prompt, "typescript")
    
    async def create_mcp_resource(
        self,
        resource_name: str,
        resource_description: str,
        data_schema: Dict[str, Any],
    ) -> str:
        """Generate MCP resource implementation.
        
        Args:
            resource_name: Name of the resource
            resource_description: Description of the resource
            data_schema: Schema for the resource data
            
        Returns:
            Generated resource code
        """
        prompt = f"""Generate a TypeScript implementation for an MCP resource with the following specification:

Resource Name: {resource_name}
Description: {resource_description}

Data Schema:
{data_schema}

The implementation should:
1. Use proper MCP SDK resource patterns
2. Support listing and individual resource retrieval
3. Include proper URI handling
4. Handle errors gracefully
5. Include JSDoc documentation
6. Follow TypeScript best practices

Generate only the resource implementation.
"""
        
        return await self.generate_code(prompt, "typescript")
    
    async def validate_generated_code(
        self,
        code: str,
        language: str = "typescript",
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate generated code for quality and correctness.
        
        Args:
            code: Code to validate
            language: Programming language
            context: Additional context
            
        Returns:
            Validation results
        """
        prompt = f"""Review the following {language} code for:

1. Syntax correctness
2. Best practices adherence
3. Error handling
4. Type safety
5. Documentation quality
6. Performance considerations
7. Security issues

Code to review:
```{language}
{code}
```

{f"Context: {context}" if context else ""}

Provide a detailed analysis with specific suggestions for improvement.
"""
        
        analysis = await self.generate_text(prompt)
        
        return {
            "analysis": analysis,
            "language": language,
            "issues_found": [],  # Would parse from analysis
            "suggestions": [],  # Would parse from analysis
            "overall_quality": "unknown",  # Would determine from analysis
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics.
        
        Returns:
            Client statistics
        """
        return {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

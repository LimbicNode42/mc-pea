"""
Anthropic Claude API client for intelligent content analysis.
"""

import os
import json
from typing import Dict, Any, List, Optional
import logging
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AnthropicClient:
    """Client for interacting with Anthropic's Claude API."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the Anthropic client.
        
        Args:
            logger: Logger instance for debugging
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Get API key from environment
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        # Initialize Anthropic client
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Use the latest model
        
        self.logger.info(f"Initialized Anthropic client with model: {self.model}")
    
    def analyze_content_for_endpoints(self, content: str, source_url: str = None) -> Dict[str, Any]:
        """Use Claude to intelligently analyze content for API endpoints.
        
        Args:
            content: Web page content to analyze
            source_url: URL where content was found (for context)
            
        Returns:
            Dictionary with extracted endpoints and metadata
        """
        try:
            # Create the prompt for Claude
            prompt = self._create_endpoint_analysis_prompt(content, source_url)
            
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,  # Lower temperature for more consistent extraction
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse Claude's response
            response_text = response.content[0].text
            self.logger.debug(f"Claude response: {response_text[:500]}...")
            
            # Try to parse as JSON
            try:
                result = json.loads(response_text)
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from the response
                result = self._extract_json_from_response(response_text)
                if result:
                    return result
            
            # Fallback: create structured response from text
            return self._parse_text_response(response_text, source_url)
            
        except Exception as e:
            self.logger.error(f"Error analyzing content with Claude: {e}")
            return {
                "endpoints": [],
                "parameters": [],
                "analysis_error": str(e),
                "extraction_method": "claude_api_error"
            }
    
    def _create_endpoint_analysis_prompt(self, content: str, source_url: str = None) -> str:
        """Create a prompt for Claude to analyze content for API endpoints.
        
        Args:
            content: Content to analyze
            source_url: Source URL for context
            
        Returns:
            Formatted prompt string
        """
        # Truncate content if too long (Claude has token limits)
        max_content_length = 50000  # Approximate token limit consideration
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n[Content truncated...]"
        
        prompt = f"""You are an expert API documentation analyzer. Please analyze the following web content and extract all API endpoints, methods, and parameters.

Source URL: {source_url or 'Not provided'}

Content to analyze:
{content}

Please provide your analysis in the following JSON format:
{{
    "endpoints": [
        {{
            "method": "GET|POST|PUT|DELETE|PATCH|etc",
            "path": "/api/path",
            "description": "Brief description of what this endpoint does",
            "parameters": [
                {{
                    "name": "parameter_name",
                    "type": "string|integer|boolean|etc",
                    "required": true/false,
                    "description": "Parameter description",
                    "location": "query|path|header|body"
                }}
            ],
            "source_section": "Section or heading where this endpoint was found",
            "confidence": 0.0-1.0
        }}
    ],
    "parameters": [
        {{
            "name": "parameter_name",
            "type": "string|integer|boolean|etc",
            "required": true/false,
            "description": "Parameter description",
            "used_in_endpoints": ["list of endpoint paths"],
            "confidence": 0.0-1.0
        }}
    ],
    "analysis_metadata": {{
        "total_endpoints_found": 0,
        "total_parameters_found": 0,
        "content_type": "github_docs|openapi|swagger|custom",
        "extraction_method": "claude_intelligent_analysis",
        "confidence_score": 0.0-1.0
    }}
}}

Focus on:
1. REST API endpoints (GET, POST, PUT, DELETE, PATCH, etc.)
2. GraphQL endpoints and mutations
3. WebSocket endpoints
4. Authentication endpoints
5. Query parameters, path parameters, request body parameters
6. Response formats and status codes

Look for patterns like:
- HTTP method + path combinations
- API documentation sections
- Code examples showing endpoint usage
- Parameter tables or lists
- Request/response examples

Be thorough but accurate. If you're not confident about an endpoint, set a lower confidence score.
"""
        
        return prompt
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Try to extract JSON from Claude's response text.
        
        Args:
            response_text: Raw response from Claude
            
        Returns:
            Parsed JSON dict or None
        """
        try:
            # Look for JSON blocks in the response
            import re
            
            # Try to find JSON between ```json and ``` or ```
            json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
            
            # Try to find JSON that starts with { and ends with }
            brace_pattern = r'\{.*\}'
            match = re.search(brace_pattern, response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting JSON from response: {e}")
            return None
    
    def _parse_text_response(self, response_text: str, source_url: str = None) -> Dict[str, Any]:
        """Parse Claude's text response when JSON parsing fails.
        
        Args:
            response_text: Raw text response from Claude
            source_url: Source URL for context
            
        Returns:
            Structured dictionary with extracted data
        """
        # This is a fallback parser for when Claude doesn't return valid JSON
        # We'll try to extract endpoints using basic text parsing
        
        endpoints = []
        parameters = []
        
        # Look for HTTP method + path patterns in the response
        import re
        
        # Pattern to find HTTP methods and paths in text
        endpoint_pattern = r'(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+([/\w\-\{\}:]+)'
        matches = re.findall(endpoint_pattern, response_text, re.IGNORECASE)
        
        for method, path in matches:
            endpoint = {
                "method": method.upper(),
                "path": path,
                "description": "Extracted from Claude text analysis",
                "source_url": source_url,
                "extraction_method": "claude_text_fallback",
                "confidence": 0.7
            }
            endpoints.append(endpoint)
        
        return {
            "endpoints": endpoints,
            "parameters": parameters,
            "analysis_metadata": {
                "total_endpoints_found": len(endpoints),
                "total_parameters_found": len(parameters),
                "extraction_method": "claude_text_fallback",
                "confidence_score": 0.7
            }
        }
    
    def analyze_content_for_parameters(self, content: str, endpoint_path: str = None) -> Dict[str, Any]:
        """Use Claude to intelligently analyze content for API parameters.
        
        Args:
            content: Web page content to analyze
            endpoint_path: Specific endpoint path to focus on
            
        Returns:
            Dictionary with extracted parameters and metadata
        """
        try:
            # Create the prompt for Claude
            prompt = self._create_parameter_analysis_prompt(content, endpoint_path)
            
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = response.content[0].text
            self.logger.debug(f"Claude parameter analysis response: {response_text[:500]}...")
            
            # Try to parse JSON response
            parsed_response = self._extract_json_from_response(response_text)
            
            if parsed_response:
                return parsed_response
            else:
                # Fallback to text parsing
                return self._parse_text_response_for_parameters(response_text, endpoint_path)
                
        except Exception as e:
            self.logger.error(f"Error in Claude parameter analysis: {e}")
            raise
    
    def _create_parameter_analysis_prompt(self, content: str, endpoint_path: str = None) -> str:
        """Create a prompt for Claude to analyze API parameters.
        
        Args:
            content: Content to analyze
            endpoint_path: Specific endpoint path to focus on
            
        Returns:
            Formatted prompt string
        """
        focus_text = f" Focus specifically on the endpoint '{endpoint_path}'." if endpoint_path else ""
        
        prompt = f"""Analyze the following API documentation content and extract all API parameters.{focus_text}

Content to analyze:
{content[:8000]}  # Limit content to prevent token overflow

Please identify and extract:
1. Parameter names
2. Parameter types (string, integer, boolean, array, object, etc.)
3. Whether each parameter is required or optional
4. Parameter descriptions
5. Where the parameter is used (path, query, body, header)
6. Default values if specified
7. Valid values or constraints if specified

Return your analysis as a JSON object with this structure:
{{
    "parameters": [
        {{
            "name": "parameter_name",
            "type": "string|integer|boolean|array|object",
            "required": true|false,
            "location": "path|query|body|header",
            "description": "Description of what this parameter does",
            "default_value": "default if specified",
            "constraints": "valid values or constraints",
            "example": "example value if provided"
        }}
    ],
    "analysis_metadata": {{
        "total_parameters_found": 0,
        "endpoint_specific": "{endpoint_path if endpoint_path else 'all'}",
        "confidence_score": 0.0,
        "extraction_method": "claude_parameter_analysis"
    }}
}}

Focus on extracting accurate parameter information. If you're unsure about a parameter, include it but mark the confidence lower."""
        
        return prompt
    
    def _parse_text_response_for_parameters(self, response_text: str, endpoint_path: str = None) -> Dict[str, Any]:
        """Parse Claude's text response for parameters when JSON parsing fails.
        
        Args:
            response_text: Raw text response from Claude
            endpoint_path: Endpoint path for context
            
        Returns:
            Structured dictionary with extracted parameters
        """
        parameters = []
        
        # Look for parameter patterns in the response
        import re
        
        # Pattern to find parameter definitions in text
        param_patterns = [
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(string|integer|boolean|array|object)',
            r'parameter\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}',  # Path parameters
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^,\s]+)',  # Parameters with defaults
        ]
        
        for pattern in param_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 1:
                    param_name = match[0]
                    param_type = match[1] if len(match) > 1 else "string"
                    
                    parameter = {
                        "name": param_name,
                        "type": param_type,
                        "required": False,  # Default to optional
                        "location": "query",  # Default location
                        "description": "Extracted from Claude text analysis",
                        "endpoint_path": endpoint_path,
                        "extraction_method": "claude_text_fallback",
                        "confidence": 0.6
                    }
                    parameters.append(parameter)
        
        return {
            "parameters": parameters,
            "analysis_metadata": {
                "total_parameters_found": len(parameters),
                "endpoint_specific": endpoint_path if endpoint_path else "all",
                "confidence_score": 0.6,
                "extraction_method": "claude_parameter_text_fallback"
            }
        }

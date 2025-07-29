import agentops
from crewai import Task, TaskOutput
from typing import Tuple, Any
from core.task_config_loader import TaskConfigLoader
from models.api_content_extractor_output import ApiLinkContentExtractorOutput
from models.api_flow_models import ChunkData

# @agentops.task(name="api_content_extractor_task")
class ApiLinkContentExtractorTask(Task):
  def __init__(self, context: ChunkData):
    # Load configuration from centralized config file
    task_loader = TaskConfigLoader()
    config_data = task_loader.get_task_config("api_content_extraction")

    # Initialize the CrewAI Task with the loaded configuration
    description_template = config_data.get("description")
    if not description_template:
        raise ValueError("No description found in task configuration")

    # Format the description template with context output
    formatted_description = description_template.format(
        chunk=context.endpoints
    )
    
    super().__init__(
        description=formatted_description,
        expected_output=config_data.get("expected_output"),
        guardrail=validate_api_content_extraction,
        async_execution=config_data.get("async_execution"),
        output_json=ApiLinkContentExtractorOutput,
        markdown=config_data.get("markdown"),
    )

    # Store config data for later use
    self._config_data = config_data

# @agentops.guardrail(name="api_content_extractor_task")
def validate_api_content_extraction(result: TaskOutput) -> Tuple[bool, Any]:
    """Validate the output of the ApiLinkContentExtractorTask to ensure it meets expectations.
    
    Validates JSON structure and content for API content extraction output.
    """
    
    # Debug: Log what we're actually receiving with more detail
    print(f"🔍 DEBUG - Result type: {type(result)}")
    print(f"🔍 DEBUG - Result dir: {dir(result)}")
    print(f"🔍 DEBUG - Result repr: {repr(result)}")
    print(f"🔍 DEBUG - Result content (first 1000 chars): {str(result)[:1000]}")
    
    # Try to access the actual data - CrewAI may wrap the result differently
    data = None
    categories = None
    
    # Method 1: Direct dictionary access
    if isinstance(result, dict):
        print(f"🔍 DEBUG - Result is dict, keys: {list(result.keys())}")
        if 'ocs' in result:
            categories = result['ocs']
            data = result
            print(f"🔍 DEBUG - Found categories via dict['ocs']")
    
    # Method 2: TaskOutput attributes
    if not categories and hasattr(result, '__dict__'):
        print(f"🔍 DEBUG - Result.__dict__: {result.__dict__}")
        
    # Method 3: Common TaskOutput patterns
    if not categories:
        for attr_name in ['raw', 'output', 'json_dict', 'data', 'result']:
            if hasattr(result, attr_name):
                attr_value = getattr(result, attr_name)
                print(f"🔍 DEBUG - Found {attr_name}: {type(attr_value)} - {str(attr_value)[:200]}")
                
                if isinstance(attr_value, dict):
                    if 'ocs' in attr_value:
                        categories = attr_value['ocs']
                        data = attr_value
                        print(f"🔍 DEBUG - Found categories via {attr_name}['ocs']")
                        break
    
    # Method 4: Direct attribute access
    if not categories:
        if hasattr(result, 'ocs'):
            categories = result.ocs
            data = result
            print(f"🔍 DEBUG - Found categories via result.ocs")
    
    # Method 5: Try to parse if result is a string
    if not categories and isinstance(result, str):
        try:
            import json
            parsed = json.loads(result)
            print(f"🔍 DEBUG - Parsed string result: {type(parsed)} - {str(parsed)[:200]}")
            if isinstance(parsed, dict):
                if 'ocs' in parsed:
                    categories = parsed['ocs']
                    data = parsed
                    print(f"🔍 DEBUG - Found categories via parsed string['ocs']")
        except:
            print(f"🔍 DEBUG - Failed to parse result as JSON")
    
    if not categories:
        print(f"🔍 DEBUG - Could not find categories field anywhere")
        return False, "Output missing 'ocs' field - not a complete JSON object"

    if not categories or not isinstance(categories, list):
        return False, "Categories field (ocs) is empty or not a list"

    # Check that the JSON object contains actual data (not just empty structures)
    if len(categories) == 0:
        return False, "JSON object contains no categories - empty data structure"
    
    total_endpoints = 0
    for category in categories:
        # Handle both dict and object access for counting
        if hasattr(category, 'ces'):  # Category endpoints
            endpoints = category.ces
        elif isinstance(category, dict):
            endpoints = category.get('ces', [])
        else:
            continue
        
        if isinstance(endpoints, list):
            total_endpoints += len(endpoints)
    
    if total_endpoints == 0:
        return False, "JSON object contains no endpoints - empty data structure"
    
    print(f"🔍 DEBUG - Found {len(categories)} categories with {total_endpoints} total endpoints")

    # Validate category structure and content
    for i, category in enumerate(categories):
        if not isinstance(category, dict):
            return False, f"Category {i} is not a dictionary structure"
        
        # Check required fields exist
        if 'cn' not in category:
            return False, f"Category {i} missing name field (cn)"
        
        if 'cd' not in category:
            return False, f"Category {i} missing description field (cd)"
        
        if 'ces' not in category:
            return False, f"Category {i} missing endpoints field (ces)"
        
        endpoints = category['ces']
        if not isinstance(endpoints, list):
            return False, f"Category {i} endpoints field (ces) is not a list"
        
        # Validate endpoint structure
        for j, endpoint in enumerate(endpoints):
            if not isinstance(endpoint, dict):
                return False, f"Endpoint {j} in category {i} is not a dictionary"
            
            # Check required endpoint fields
            required_endpoint_fields = ['en', 'ed', 'em', 'ep']
            for field in required_endpoint_fields:
                if field not in endpoint:
                    return False, f"Endpoint {j} in category {i} missing required field '{field}'"
            
            # Validate HTTP method
            http_method = endpoint.get('em', '').upper()
            valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
            if http_method not in valid_methods:
                return False, f"Endpoint {j} in category {i} has invalid HTTP method: {http_method}"
            
            # Validate endpoint path
            endpoint_path = endpoint.get('ep', '')
            if not endpoint_path or not isinstance(endpoint_path, str):
                return False, f"Endpoint {j} in category {i} has invalid or missing path"
            
            # Validate parameter lists (if present)
            param_fields = ['eh', 'epp', 'eqp', 'ebp']  # headers, path params, query params, body params
            for param_field in param_fields:
                if param_field in endpoint:
                    params = endpoint[param_field]
                    if not isinstance(params, list):
                        return False, f"Endpoint {j} in category {i} field '{param_field}' is not a list"
                    
                    # Validate parameter structure
                    for k, param in enumerate(params):
                        if not isinstance(param, dict):
                            return False, f"Parameter {k} in {param_field} of endpoint {j} (category {i}) is not a dictionary"
                        
                        # Check required parameter fields
                        required_param_fields = ['pn', 'pd', 'pt']  # param name, description, type
                        for pfield in required_param_fields:
                            if pfield not in param:
                                return False, f"Parameter {k} in {param_field} of endpoint {j} (category {i}) missing field '{pfield}'"
            
            # Validate response structures (if present)
            if 'erc' in endpoint and not isinstance(endpoint['erc'], dict):
                return False, f"Endpoint {j} in category {i} response codes (erc) is not a dictionary"
            
            if 'ere' in endpoint and not isinstance(endpoint['ere'], dict):
                return False, f"Endpoint {j} in category {i} response fields (ere) is not a dictionary"

    # Return the actual parsed data instead of just a message
    return True, data
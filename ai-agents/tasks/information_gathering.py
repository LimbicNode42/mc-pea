"""
Information Gathering Tasks

This module contains task definitions that use the centralized task configuration
from configs/tasks.yaml, similar to how agents load their configuration.
"""

from crewai import Task, TaskOutput
from typing import Tuple, Any
from core.task_config_loader import TaskConfigLoader
from models.link_discovery_output import ApiLinkDiscoveryOutput
from models.link_content_extractor_output import ApiLinkContentExtractorOutput

class ApiLinkDiscoveryTask(Task):
  def __init__(self, website_url: str, depth: int = 3):
    # Load configuration from centralized config file
    task_loader = TaskConfigLoader()
    config_data = task_loader.get_task_config("api_link_discovery")
      
    # Initialize the CrewAI Task with the loaded configuration
    # Format description and expected_output with provided parameters
    description_template = config_data.get("description", "")
    if not description_template:
        raise ValueError("No description found in task configuration")
    
    description = description_template.format(
        website_url=website_url, 
        depth=depth
    )
    
    super().__init__(
        description=description, 
        expected_output=config_data.get("expected_output"),
        output_json=ApiLinkDiscoveryOutput,
        guardrail=validate_blog_content,
        markdown=config_data.get("markdown"),
        output_file=config_data.get("output_file"),
    )
    
    # Store config data for later use
    self._config_data = config_data

def validate_blog_content(result: TaskOutput) -> Tuple[bool, Any]:
    """Validate the output of the ApiLinkDiscoveryTask to ensure it meets expectations.
    
    Updated for output_json strategy - validates JSON structure and content.
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
        if 'cs' in result:
            categories = result['cs']
            data = result
            print(f"🔍 DEBUG - Found categories via dict['cs']")
        elif 'categories' in result:
            categories = result['categories']
            data = result
            print(f"🔍 DEBUG - Found categories via dict['categories']")
    
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
                    if 'cs' in attr_value:
                        categories = attr_value['cs']
                        data = attr_value
                        print(f"🔍 DEBUG - Found categories via {attr_name}['cs']")
                        break
                    elif 'categories' in attr_value:
                        categories = attr_value['categories']
                        data = attr_value
                        print(f"🔍 DEBUG - Found categories via {attr_name}['categories']")
                        break
    
    # Method 4: Direct attribute access
    if not categories:
        if hasattr(result, 'cs'):
            categories = result.cs
            data = result
            print(f"🔍 DEBUG - Found categories via result.cs")
        elif hasattr(result, 'categories'):
            categories = result.categories
            data = result
            print(f"🔍 DEBUG - Found categories via result.categories")
    
    # Method 5: Try to parse if result is a string
    if not categories and isinstance(result, str):
        try:
            import json
            parsed = json.loads(result)
            print(f"🔍 DEBUG - Parsed string result: {type(parsed)} - {str(parsed)[:200]}")
            if isinstance(parsed, dict):
                if 'cs' in parsed:
                    categories = parsed['cs']
                    data = parsed
                    print(f"🔍 DEBUG - Found categories via parsed string['cs']")
                elif 'categories' in parsed:
                    categories = parsed['categories']
                    data = parsed
                    print(f"🔍 DEBUG - Found categories via parsed string['categories']")
        except:
            print(f"🔍 DEBUG - Failed to parse result as JSON")
    
    if not categories:
        print(f"🔍 DEBUG - Could not find categories field anywhere")
        return False, "Output missing 'cs' or 'categories' field - not a complete JSON object"

    if not categories or not isinstance(categories, list):
        return False, "Categories field is empty or not a list"

    # 1.5. Check that the JSON object contains actual data (not just empty structures)
    if len(categories) == 0:
        return False, "JSON object contains no categories - empty data structure"
    
    total_links = 0
    for category in categories:
        # Handle both dict and object access for counting (new and old field names)
        if hasattr(category, 'ls'):  # New field name
            links = category.ls
        elif hasattr(category, 'links'):  # Old field name
            links = category.links
        elif isinstance(category, dict):
            links = category.get('ls', category.get('links', []))
        else:
            continue
        
        if isinstance(links, list):
            total_links += len(links)
    
    if total_links == 0:
        return False, "JSON object contains no links - empty data structure"
    
    print(f"🔍 DEBUG - Found {len(categories)} categories with {total_links} total links")

    # 2. Check the link fields contain URL formatted text
    import re
    url_found = False
    # Updated regex to accept both full URLs and paths
    url_regex = re.compile(
        r"^(https?:\/\/[\w\-]+\.[\w\-]+([\w\-\.~:\/?#\[\]@!$&'()*+,;=]*)|\/[\w\-\.~:\/?#\[\]@!$&'()*+,;=]*)$", 
        re.IGNORECASE
    )
    
    for category in categories:
        # Handle both dict and object access (new and old field names)
        if hasattr(category, 'n'):  # New field names
            category_name = category.n
            links = category.ls
        elif hasattr(category, 'category_name'):  # Old field names
            category_name = category.category_name
            links = category.links
        elif isinstance(category, dict):
            category_name = category.get('n', category.get('category_name', 'unknown'))
            links = category.get('ls', category.get('links', []))
        else:
            return False, f"Category object is malformed"

        if not links or not isinstance(links, list):
            return False, f"Category '{category_name}' has no links or links is not a list"
        
        for link in links:
            # Handle both dict and object access (new and old field names)
            if hasattr(link, 't') and hasattr(link, 'l'):  # New field names
                title = link.t
                link_url = link.l
            elif hasattr(link, 'title') and hasattr(link, 'link'):  # Old field names
                title = link.title
                link_url = link.link
            elif isinstance(link, dict):
                title = link.get('t', link.get('title'))
                link_url = link.get('l', link.get('link'))
            else:
                return False, f"Link object in category '{category_name}' is malformed"
            
            if not title or not link_url:
                return False, f"Link in category '{category_name}' is missing title or URL"
            
            # Check if link_url is a valid URL format (now accepts paths)
            if isinstance(link_url, str) and url_regex.match(link_url):
                url_found = True
            else:
                return False, f"Link '{link_url}' in category '{category_name}' is not a valid URL or path format"

    if not url_found:
        return False, "No valid URL links found in any category"

    # 3. Validate JSON structure compliance (removed Pydantic type check)
    # With output_json, we focus on structure validation rather than type checking
    if not isinstance(categories, list):
        return False, "Categories should be a list structure"
    
    # Additional structural validation
    for i, category in enumerate(categories):
        if not isinstance(category, dict):
            return False, f"Category {i} is not a dictionary structure"
        
        # Check required fields exist
        category_name_field = 'n' if 'n' in category else 'category_name'
        links_field = 'ls' if 'ls' in category else 'links'
        
        if category_name_field not in category:
            return False, f"Category {i} missing name field"
        
        if links_field not in category:
            return False, f"Category {i} missing links field"
        
        links = category[links_field]
        if not isinstance(links, list):
            return False, f"Category {i} links field is not a list"
        
        # Validate link structure
        for j, link in enumerate(links):
            if not isinstance(link, dict):
                return False, f"Link {j} in category {i} is not a dictionary"
            
            title_field = 't' if 't' in link else 'title'
            link_field = 'l' if 'l' in link else 'link'
            
            if title_field not in link or link_field not in link:
                return False, f"Link {j} in category {i} missing required fields"

    return True, f"Output is valid JSON: {len(categories)} categories with {total_links} total links"

class ApiLinkContentExtractorTask(Task):
  def __init__(self):
    # Load configuration from centralized config file
    task_loader = TaskConfigLoader()
    config_data = task_loader.get_task_config("api_link_content_extractor")

    # Initialize the CrewAI Task with the loaded configuration
    description_template = config_data.get("description")
    if not description_template:
        raise ValueError("No description found in task configuration")
    
    # For the content extractor, the description doesn't need formatting
    # since it will receive context from the previous task
    description = description_template.replace("{website_urls}", "the discovered links from the previous task")
    
    super().__init__(
        description=description,
        expected_output=config_data.get("expected_output"),
        output_json=ApiLinkContentExtractorOutput,
        markdown=config_data.get("markdown"),
        output_file=config_data.get("output_file"),
    )
    
    # Store config data for later use
    self._config_data = config_data

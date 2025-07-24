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
    """Validate the output of the ApiLinkDiscoveryTask to ensure it meets expectations."""
    
    # Debug: Log what we're actually receiving
    print(f"🔍 DEBUG - Result type: {type(result)}")
    print(f"🔍 DEBUG - Result dir: {dir(result)}")
    print(f"🔍 DEBUG - Result content (first 500 chars): {str(result)[:500]}")
    
    # 1. Check the output is a complete JSON object
    # First handle if result is a dict/raw JSON and try to access its structure
    if hasattr(result, 'categories'):
        categories = result.categories
        print(f"🔍 DEBUG - Found categories via hasattr")
    elif isinstance(result, dict) and 'categories' in result:
        categories = result['categories']
        print(f"🔍 DEBUG - Found categories via dict access")
    elif hasattr(result, 'raw') and hasattr(result.raw, 'categories'):
        categories = result.raw.categories
        print(f"🔍 DEBUG - Found categories via result.raw")
    elif hasattr(result, 'output') and isinstance(result.output, dict) and 'categories' in result.output:
        categories = result.output['categories']
        print(f"🔍 DEBUG - Found categories via result.output")
    else:
        print(f"🔍 DEBUG - Could not find categories field anywhere")
        return False, "Output missing 'categories' field - not a complete JSON object"

    if not categories or not isinstance(categories, list):
        return False, "Categories field is empty or not a list"

    # 1.5. Check that the JSON object contains actual data (not just empty structures)
    if len(categories) == 0:
        return False, "JSON object contains no categories - empty data structure"
    
    total_links = 0
    for category in categories:
        # Handle both dict and object access for counting
        if hasattr(category, 'links'):
            links = category.links
        elif isinstance(category, dict):
            links = category.get('links', [])
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
    url_regex = re.compile(
        r"^(https?:\/\/)?"  # http:// or https://
        r"([\w\-]+\.)+[\w\-]+"  # domain
        r"([\w\-\.~:\/?#\[\]@!$&'()*+,;=]*)$", re.IGNORECASE
    )
    
    for category in categories:
        # Handle both dict and object access
        if hasattr(category, 'category_name'):
            category_name = category.category_name
            links = category.links
        elif isinstance(category, dict):
            category_name = category.get('category_name', 'unknown')
            links = category.get('links', [])
        else:
            return False, f"Category object is malformed"

        if not links or not isinstance(links, list):
            return False, f"Category '{category_name}' has no links or links is not a list"
        
        for link in links:
            # Handle both dict and object access
            if hasattr(link, 'title') and hasattr(link, 'link'):
                title = link.title
                link_url = link.link
            elif isinstance(link, dict):
                title = link.get('title')
                link_url = link.get('link')
            else:
                return False, f"Link object in category '{category_name}' is malformed"
            
            if not title or not link_url:
                return False, f"Link in category '{category_name}' is missing title or URL"
            
            # Check if link_url is a valid URL format
            if isinstance(link_url, str) and url_regex.match(link_url):
                url_found = True
            else:
                return False, f"Link '{link_url}' in category '{category_name}' is not a valid URL format"

    if not url_found:
        return False, "No valid URL links found in any category"

    # 3. Check if it is an instance of ApiLinkDiscoveryOutput
    if not isinstance(result, ApiLinkDiscoveryOutput):
        print(f"🔍 DEBUG - Not an ApiLinkDiscoveryOutput instance, type is: {type(result)}")
        return False, "Invalid output type: not ApiLinkDiscoveryOutput"

    return True, "Output is valid: contains complete JSON object, valid URLs, and correct type"

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

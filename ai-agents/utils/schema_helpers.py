"""
Schema examples and validation helpers for API content extraction.
"""

# Clear example of expected output structure
EXAMPLE_OUTPUT = {
    "ocs": [
        {
            "cn": "Repository Management",
            "cd": "APIs for managing GitHub repositories",
            "ces": [
                {
                    "en": "Get Repository",
                    "ed": "Retrieve repository information",
                    "em": "GET",
                    "ep": "/repos/{owner}/{repo}",
                    "eh": [
                        {
                            "pn": "Accept",
                            "pd": "Media type for response",
                            "pr": False,
                            "pt": "string",
                            "pv": "application/vnd.github+json"
                        }
                    ],
                    "epp": [
                        {
                            "pn": "owner",
                            "pd": "Repository owner username",
                            "pr": True,
                            "pt": "string"
                        },
                        {
                            "pn": "repo",
                            "pd": "Repository name",
                            "pr": True,
                            "pt": "string"
                        }
                    ],
                    "eqp": [],
                    "ebp": [],
                    "erc": {
                        "200": "Success - Repository object returned",
                        "404": "Repository not found"
                    },
                    "ere": {
                        "id": "Repository ID",
                        "name": "Repository name",
                        "full_name": "Full repository name"
                    }
                }
            ]
        }
    ]
}

def get_schema_prompt():
    """Generate a schema instruction prompt for the LLM."""
    return """
CRITICAL: Output must be valid JSON matching this EXACT structure:

{"ocs": [
  {
    "cn": "Category Name",
    "cd": "Category description", 
    "ces": [
      {
        "en": "Endpoint Name",
        "ed": "Endpoint description",
        "em": "HTTP_METHOD",
        "ep": "/api/path",
        "eh": [],
        "epp": [],
        "eqp": [],
        "ebp": [],
        "erc": {},
        "ere": {}
      }
    ]
  }
]}

Field meanings:
- ocs: Output categories (main array)
- cn: Category name, cd: Category description, ces: Category endpoints
- en: Endpoint name, ed: Endpoint description, em: HTTP method, ep: Endpoint path
- eh: Headers, epp: Path params, eqp: Query params, ebp: Body params
- erc: Response codes, ere: Response examples

IMPORTANT: Always include ALL fields, use empty arrays/objects if no data found.
"""

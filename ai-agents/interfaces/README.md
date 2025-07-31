# Endpoint Discovery Interface

A simple Streamlit interface for discovering API endpoints and allowing human selection for further processing.

## Features

- 🔍 **URL Input**: Enter any API documentation URL
- 📊 **Progress Tracking**: Real-time progress of discovery flow execution
- 📁 **Categorized Display**: Endpoints grouped by categories for easy browsing
- ✅ **Interactive Selection**: Checkboxes to select specific endpoints
- 💾 **Save Selection**: Export selected endpoints to JSON file
- 🎯 **Human-in-the-loop**: Let users choose what's important instead of processing everything

## Architecture

This interface demonstrates the value of human input in AI workflows:

1. **Discovery Phase**: AI agents discover all available endpoints
2. **Organization Phase**: Endpoints are grouped by category and chunked
3. **Human Selection**: Users review and select endpoints they care about
4. **Future: Targeted Extraction**: Only selected endpoints will be processed for API usage examples

## Usage

### Quick Start

```bash
# From the ai-agents directory
python launch_discovery_ui.py
```

### Manual Launch

```bash
# From the ai-agents directory
streamlit run interfaces/endpoint_discovery_ui.py
```

### Prerequisites

1. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="your_api_key_here"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Interface Flow

### 1. URL Input
- Enter the API documentation URL (e.g., `https://docs.github.com/en/rest`)
- URL validation ensures proper format

### 2. Discovery Progress
- **Phase 1**: AI agents analyze the website and discover endpoints
- **Phase 2**: Endpoints are organized into categories and chunks
- Real-time status updates with expandable details

### 3. Endpoint Selection
- Endpoints displayed by category in expandable sections
- Individual checkboxes for each endpoint
- Bulk selection controls (Select All, Clear All, Select All in Category)
- Live counter of selected endpoints

### 4. Review & Export
- Summary of selected endpoints by category
- Save selection to JSON file for later processing
- Preparation for future API usage extraction

## Output Files

The interface generates several files:

- `chunk_XX_endpoints.json`: Raw endpoint data per chunk
- `endpoint_selection_<hostname>.json`: User's endpoint selection
- Future: `chunk_XX_api_usage.json`: API usage examples (when extraction is re-enabled)

## Design Philosophy

This interface embodies the principle that **human input adds value** rather than being a bottleneck:

- **Quality over Quantity**: Process only what matters to the user
- **Interactive Discovery**: Let humans guide the AI's focus
- **Transparent Progress**: Show exactly what the AI agents are doing
- **Flexible Selection**: Easy to adjust choices before committing to processing

## Next Steps

1. **Re-enable Parallel Extraction**: Add back the commented extraction code
2. **Targeted Processing**: Only extract usage for selected endpoints
3. **Progress Persistence**: Save and resume sessions
4. **Advanced Filtering**: Search, filter, and sort endpoints
5. **Batch Operations**: Process multiple API documentations

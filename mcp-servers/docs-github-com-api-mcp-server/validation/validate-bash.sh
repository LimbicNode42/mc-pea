#!/bin/bash

# MCP Server Command-Line Validation
# 
# Quick validation script using curl

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
MCP_SERVER_URL=${MCP_SERVER_URL:-"http://localhost:3000"}
API_KEY=${API_KEY}

if [ -z "$API_KEY" ]; then
    echo "❌ Missing required environment variable: API_KEY"
    exit 1
fi

# Ensure URL has trailing slash
if [[ "$MCP_SERVER_URL" != */ ]]; then
    MCP_SERVER_URL="${MCP_SERVER_URL}/"
fi

MCP_URL="${MCP_SERVER_URL}mcp"

echo "🔍 MCP Server Command-Line Validation"
echo "====================================="
echo ""
echo "🎯 Testing MCP server at: $MCP_URL"
echo "🔐 Using API key: ${API_KEY:0:8}..."
echo ""

# Test 1: Health check
echo "🏥 Testing health endpoint..."
curl -s -f "${MCP_SERVER_URL}health" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Health check passed"
else
    echo "ℹ️  Health endpoint not available"
fi

# Test 2: Initialize
echo "🚀 Testing MCP initialize..."
INIT_RESPONSE=$(curl -s -X POST "$MCP_URL" \
    -H "Content-Type: application/json" \
    -H "x-api-key: $API_KEY" \
    -d '{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": { "listChanged": true },
                "sampling": {}
            },
            "clientInfo": {
                "name": "curl-validator",
                "version": "1.0.0"
            }
        }
    }')

if echo "$INIT_RESPONSE" | grep -q '"result"'; then
    echo "✅ Initialize successful"
else
    echo "⚠️  Initialize failed: $INIT_RESPONSE"
fi

# Test 3: List tools
echo "🔧 Testing tools/list..."
TOOLS_RESPONSE=$(curl -s -X POST "$MCP_URL" \
    -H "Content-Type: application/json" \
    -H "x-api-key: $API_KEY" \
    -d '{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }')

if echo "$TOOLS_RESPONSE" | grep -q '"tools"'; then
    TOOL_COUNT=$(echo "$TOOLS_RESPONSE" | grep -o '"name"' | wc -l)
    echo "✅ Found $TOOL_COUNT tools"
    
    # Extract tool names
    echo "$TOOLS_RESPONSE" | grep -o '"name":"[^"]*"' | sed 's/"name":"/   - /' | sed 's/"$//'
else
    echo "⚠️  Tools list failed: $TOOLS_RESPONSE"
fi

# Test 4: List resources
echo "📚 Testing resources/list..."
RESOURCES_RESPONSE=$(curl -s -X POST "$MCP_URL" \
    -H "Content-Type: application/json" \
    -H "x-api-key: $API_KEY" \
    -d '{
        "jsonrpc": "2.0",
        "id": 3,
        "method": "resources/list"
    }')

if echo "$RESOURCES_RESPONSE" | grep -q '"resources"'; then
    RESOURCE_COUNT=$(echo "$RESOURCES_RESPONSE" | grep -o '"name"' | wc -l)
    echo "✅ Found $RESOURCE_COUNT resources"
    
    # Extract resource names
    echo "$RESOURCES_RESPONSE" | grep -o '"name":"[^"]*"' | sed 's/"name":"/   - /' | sed 's/"$//'
else
    echo "⚠️  Resources list failed: $RESOURCES_RESPONSE"
fi

# Test 5: List prompts
echo "📝 Testing prompts/list..."
PROMPTS_RESPONSE=$(curl -s -X POST "$MCP_URL" \
    -H "Content-Type: application/json" \
    -H "x-api-key: $API_KEY" \
    -d '{
        "jsonrpc": "2.0",
        "id": 4,
        "method": "prompts/list"
    }')

if echo "$PROMPTS_RESPONSE" | grep -q '"prompts"'; then
    PROMPT_COUNT=$(echo "$PROMPTS_RESPONSE" | grep -o '"name"' | wc -l)
    echo "✅ Found $PROMPT_COUNT prompts"
    
    # Extract prompt names
    echo "$PROMPTS_RESPONSE" | grep -o '"name":"[^"]*"' | sed 's/"name":"/   - /' | sed 's/"$//'
else
    echo "ℹ️  Prompts not available: $PROMPTS_RESPONSE"
fi

echo ""
echo "🎉 Command-line validation completed!"

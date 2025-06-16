#!/usr/bin/env bash
# Everything Search Setup Script for MCP

echo "🔍 Setting up Everything Search for MCP integration..."

# Create directory for Everything tools
EVERYTHING_DIR="D:/dev/tools/Everything-SDK"
mkdir -p "$EVERYTHING_DIR"

echo "📥 You'll need to manually download the following:"
echo "1. Everything (main application): https://www.voidtools.com/downloads/"
echo "2. Everything SDK: https://www.voidtools.com/support/everything/sdk/"
echo ""
echo "📁 Recommended setup:"
echo "   - Install Everything to: C:/Program Files/Everything/"
echo "   - Extract SDK to: $EVERYTHING_DIR/"
echo ""
echo "🎯 Expected SDK structure:"
echo "   $EVERYTHING_DIR/"
echo "   ├── dll/"
echo "   │   ├── Everything64.dll"
echo "   │   └── Everything32.dll"
echo "   ├── include/"
echo "   └── lib/"
echo ""
echo "⚙️ Environment variable needed:"
echo "   EVERYTHING_SDK_PATH=$EVERYTHING_DIR/dll/Everything64.dll"

# Check if we can create the directory
if [ -d "D:/dev" ]; then
    echo "✅ D:/dev directory exists"
    mkdir -p "$EVERYTHING_DIR"
    echo "✅ Created $EVERYTHING_DIR"
else
    echo "⚠️  Creating D:/dev/tools/Everything-SDK..."
    mkdir -p "$EVERYTHING_DIR"
    if [ $? -eq 0 ]; then
        echo "✅ Created directory structure"
    else
        echo "❌ Failed to create directory. Please create manually."
    fi
fi

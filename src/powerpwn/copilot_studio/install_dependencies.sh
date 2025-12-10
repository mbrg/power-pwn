#!/bin/bash
# Install dependencies for all Copilot Studio tools

echo "Installing Copilot Studio dependencies..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    echo ""
    echo "Please install Node.js first:"
    echo "  macOS: brew install node"
    echo "  Linux: sudo apt-get install nodejs npm"
    echo "  Or download from: https://nodejs.org/"
    exit 1
fi

echo "✓ Node.js version: $(node --version)"
echo "✓ npm version: $(npm --version)"
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Install dependencies for pup_query_webchat
echo "Installing dependencies for pup_query_webchat..."
cd "$SCRIPT_DIR/tools/pup_query_webchat"
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install pup_query_webchat dependencies!"
    exit 1
fi
echo "✓ pup_query_webchat dependencies installed"
echo ""

# Install dependencies for pup_is_webchat_live
echo "Installing dependencies for pup_is_webchat_live..."
cd "$SCRIPT_DIR/tools/pup_is_webchat_live"
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install pup_is_webchat_live dependencies!"
    exit 1
fi
echo "✓ pup_is_webchat_live dependencies installed"
echo ""

echo "✅ All Copilot Studio dependencies installed successfully!"
echo ""
echo "You can now use Copilot Studio tools."



#!/bin/bash
# Install dependencies for Agent Builder Hunter

echo "Installing Agent Builder Hunter dependencies..."
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
cd "$SCRIPT_DIR"

echo "Installing npm packages in: $SCRIPT_DIR"
echo ""

# Install dependencies
npm install

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation complete!"
    echo ""
    echo "You can now run:"
    echo "  powerpwn agent-builder-hunter scan"
    echo "  powerpwn agent-builder-hunter tools-recon -f urls.txt"
else
    echo ""
    echo "❌ Installation failed!"
    echo "Please check the error messages above."
    exit 1
fi



#!/bin/bash
# Install evdev to bundled lib directory
# Based on decktation's approach

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing python-evdev to bundled lib directory..."
echo ""

# Find or create pip
if [ -f "$SCRIPT_DIR/../.venv/bin/pip" ]; then
    PIP="$SCRIPT_DIR/../.venv/bin/pip"
    echo "Using existing venv pip"
elif command -v pip3 &> /dev/null; then
    PIP="pip3"
    echo "Using system pip3"
elif command -v pip &> /dev/null; then
    PIP="pip"
    echo "Using system pip"
else
    echo "No pip found, creating temporary venv..."
    python3 -m venv /tmp/steamdecky_venv
    PIP="/tmp/steamdecky_venv/bin/pip"
    echo "Created temporary venv"
fi

echo "Using pip: $PIP"
echo ""

# Create lib directory
mkdir -p "$SCRIPT_DIR/lib"

# Install evdev-binary (pre-compiled version)
echo "Installing evdev-binary..."
$PIP install --target="$SCRIPT_DIR/lib" evdev-binary

echo ""
echo "✓ evdev-binary installed to ./lib/"
echo ""
echo "Installed modules:"
ls -d "$SCRIPT_DIR/lib"/evdev* 2>/dev/null || echo "evdev modules installed"
echo ""
echo "Next steps:"
echo "1. Run ./deploy.sh to deploy the plugin with bundled evdev"
echo "2. The plugin will use the bundled version automatically"
echo ""

# Cleanup temp venv if created
if [ -d "/tmp/steamdecky_venv" ]; then
    echo "Cleaning up temporary venv..."
    rm -rf /tmp/steamdecky_venv
fi

#!/bin/bash

# Deploy script for DeckController plugin

PLUGIN_DIR=~/homebrew/plugins/steamdecky-controller

echo "Building plugin..."
npm run build

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo "Creating plugin directory: $PLUGIN_DIR"
sudo mkdir -p "$PLUGIN_DIR"

echo "Copying files..."
sudo cp main.py "$PLUGIN_DIR/"
sudo cp controller_forwarder.py "$PLUGIN_DIR/"
sudo cp plugin.json "$PLUGIN_DIR/"
sudo cp package.json "$PLUGIN_DIR/"
sudo cp -r dist "$PLUGIN_DIR/"

# Copy bundled Python dependencies if they exist
if [ -d "lib" ]; then
    echo "Copying bundled Python dependencies..."
    sudo cp -r lib "$PLUGIN_DIR/"
fi

echo "Plugin deployed successfully to $PLUGIN_DIR"
echo "Restart Decky Loader to load the plugin."

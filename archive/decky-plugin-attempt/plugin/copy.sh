#!/bin/bash

# Copy script for SteamDeckyController plugin
# Run with: sudo ./copy.sh

echo "Creating plugin directory: /home/deck/homebrew/plugins/steamdecky-controller"
sudo mkdir -p /home/deck/homebrew/plugins/steamdecky-controller

echo "Copying files..."
sudo cp main.py /home/deck/homebrew/plugins/steamdecky-controller/
sudo cp controller_forwarder.py /home/deck/homebrew/plugins/steamdecky-controller/
sudo cp plugin.json /home/deck/homebrew/plugins/steamdecky-controller/
sudo cp package.json /home/deck/homebrew/plugins/steamdecky-controller/
sudo cp -r dist /home/deck/homebrew/plugins/steamdecky-controller/

echo "Plugin copied successfully to /home/deck/homebrew/plugins/steamdecky-controller"
echo "Restart Decky Loader to load the plugin."

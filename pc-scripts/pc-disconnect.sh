#!/bin/bash
# Disconnect from Steam Deck controller

echo "========================================"
echo "Disconnect Steam Deck Controller"
echo "========================================"
echo

# Check current connections
echo "Current USB/IP connections:"
sudo usbip port
echo

# Find the port number for the Steam Deck controller
PORT=$(sudo usbip port | grep "28de:1205" | grep -oP 'Port \K[0-9]+' | head -1)

if [ -z "$PORT" ]; then
    echo "No Steam Deck controller found via USB/IP"
    exit 1
fi

echo "Detaching controller from port $PORT..."
sudo usbip detach -p "$PORT"

if [ $? -eq 0 ]; then
    echo
    echo "========================================"
    echo "Controller disconnected"
    echo "========================================"
else
    echo "ERROR: Failed to disconnect"
    exit 1
fi

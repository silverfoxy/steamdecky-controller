#!/bin/bash
# Connect to Steam Deck controller via USB/IP from PC

echo "========================================"
echo "Connect to Steam Deck Controller"
echo "========================================"
echo

# Check if usbip is installed
if ! command -v usbip &> /dev/null; then
    echo "ERROR: usbip not installed"
    echo "Install on Ubuntu/Debian: sudo apt install linux-tools-generic"
    echo "Install on Fedora: sudo dnf install usbip"
    echo "Install on Arch: sudo pacman -S usbip"
    exit 1
fi

# Get Deck IP
if [ -z "$1" ]; then
    echo "Usage: $0 <deck-ip> [busid]"
    echo
    echo "Example: $0 192.168.1.206 3-3"
    echo
    echo "To find available devices:"
    echo "  usbip list -r <deck-ip>"
    exit 1
fi

DECK_IP=$1
BUSID=${2:-"3-3"}  # Default busid for Steam Deck controller

echo "Deck IP: $DECK_IP"
echo "Bus ID: $BUSID"
echo

# Load kernel modules
echo "Loading USB/IP kernel modules..."
sudo modprobe vhci-hcd

# List available devices
echo "Available devices on Deck:"
usbip list -r "$DECK_IP"
echo

# Attach the device
echo "Attaching controller..."
sudo usbip attach -r "$DECK_IP" -b "$BUSID"

if [ $? -eq 0 ]; then
    echo
    echo "========================================"
    echo "SUCCESS! Controller connected"
    echo "========================================"
    echo
    echo "Check with: sudo usbip port"
    echo "To disconnect, run: ./pc-disconnect.sh"
else
    echo "ERROR: Failed to attach device"
    exit 1
fi

#!/bin/bash
# PC side: Connect to Deck's USB/IP controller

if [ -z "$1" ]; then
    echo "Usage: $0 <deck-ip> [busid]"
    echo "Example: $0 192.168.1.100"
    exit 1
fi

DECK_IP="$1"

echo "========================================"
echo "Connect to Deck Controller via USB/IP"
echo "========================================"
echo

# Check if usbip is installed
if ! command -v usbip &> /dev/null; then
    echo "ERROR: usbip not installed"
    echo
    echo "Install on Ubuntu/Debian:"
    echo "  sudo apt install linux-tools-generic"
    echo
    echo "Install on Fedora:"
    echo "  sudo dnf install usbip"
    echo
    echo "Install on Arch:"
    echo "  sudo pacman -S usbip"
    exit 1
fi

# Load kernel modules
echo "Loading usbip kernel modules..."
sudo modprobe vhci-hcd

# List available devices
echo
echo "Available devices on Deck ($DECK_IP):"
sudo usbip list -r "$DECK_IP"

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: Cannot connect to Deck"
    echo "Make sure deck-start-usbip.sh is running on the Deck"
    exit 1
fi

echo
# If busid provided, use it; otherwise prompt
if [ -z "$2" ]; then
    echo "Enter the busid to attach (e.g., 3-2):"
    read BUSID
else
    BUSID="$2"
fi

echo
echo "Attaching device $BUSID..."
sudo usbip attach -r "$DECK_IP" -b "$BUSID"

if [ $? -eq 0 ]; then
    echo
    echo "========================================"
    echo "SUCCESS! Steam Deck controller attached"
    echo "========================================"
    echo
    echo "Check with: lsusb | grep Valve"
    echo "The controller should now work in games!"
    echo
    echo "To disconnect, run: ./pc-usbip-disconnect.sh"
else
    echo "ERROR: Failed to attach device"
    exit 1
fi

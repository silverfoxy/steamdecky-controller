#!/bin/bash
# Restore Steam Deck controller functionality

echo "Attempting to restore controller..."

# Try to reprobe the device to rebind driver
echo "3-3" | sudo tee /sys/bus/usb/drivers_probe

# Alternative: unbind and rebind
# Find what driver should be used
echo "Checking USB tree..."
lsusb -t | grep -A2 "Valve"

echo "Done! Check if controller works now."
echo "If not, try rebooting the Steam Deck."

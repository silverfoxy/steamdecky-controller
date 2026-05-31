#!/bin/bash
# Manually fix permissions for the Steam Deck controller

echo "Finding Steam Deck controller device path..."
DEVICE_PATH=$(find /sys/bus/usb/devices -name "3-3" -type l 2>/dev/null | head -1)

if [ -z "$DEVICE_PATH" ]; then
    echo "Controller not found at busid 3-3"
    exit 1
fi

echo "Found device at: $DEVICE_PATH"

# Find the driver directory
DRIVER_PATH="$DEVICE_PATH/driver"

if [ -d "$DRIVER_PATH" ]; then
    echo "Setting permissions on bind/unbind files..."
    sudo chmod 666 "$DRIVER_PATH/unbind" "$DRIVER_PATH/bind" 2>/dev/null
    ls -l "$DRIVER_PATH/unbind" "$DRIVER_PATH/bind"
    echo "Permissions set!"
else
    echo "Driver path not found: $DRIVER_PATH"
fi

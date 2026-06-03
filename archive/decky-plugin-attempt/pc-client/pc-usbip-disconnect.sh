#!/bin/bash
# PC side: Disconnect USB/IP controller

echo "========================================"
echo "Disconnect USB/IP Controller"
echo "========================================"
echo

# Find attached ports
PORTS=$(sudo usbip port 2>/dev/null | grep "Port" | awk '{print $1}' | sed 's/://')

if [ -z "$PORTS" ]; then
    echo "No USB/IP devices attached"
    exit 0
fi

echo "Attached ports:"
sudo usbip port
echo

# Detach all
for PORT in $PORTS; do
    echo "Detaching port $PORT..."
    sudo usbip detach -p "$PORT"
done

echo
echo "========================================"
echo "Disconnected"
echo "========================================"

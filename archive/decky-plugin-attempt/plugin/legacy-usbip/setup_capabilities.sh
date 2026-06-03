#!/bin/bash
# Give usbip binaries the necessary capabilities to run without sudo

PLUGIN_BIN="/home/deck/homebrew/plugins/steamdecky-controller/bin"

echo "Setting capabilities on usbip binaries..."

# CAP_NET_ADMIN is needed for USB/IP operations
sudo setcap cap_net_admin,cap_sys_admin+eip "$PLUGIN_BIN/usbip" 2>/dev/null || echo "Failed to set caps on usbip"
sudo setcap cap_net_admin,cap_sys_admin+eip "$PLUGIN_BIN/usbipd" 2>/dev/null || echo "Failed to set caps on usbipd"

echo "Capabilities set!"
getcap "$PLUGIN_BIN/usbip" "$PLUGIN_BIN/usbipd"

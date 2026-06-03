#!/bin/bash
# Setup passwordless sudo for usbip commands

SUDOERS_FILE="/etc/sudoers.d/steamdecky-controller"

echo "Creating sudoers rule for usbip commands..."

sudo tee "$SUDOERS_FILE" > /dev/null << 'SUDOERS'
# Allow deck user to run usbip commands without password
deck ALL=(ALL) NOPASSWD: /usr/bin/usbip, /usr/sbin/usbip, /usr/bin/usbipd, /usr/sbin/usbipd
deck ALL=(ALL) NOPASSWD: /home/deck/homebrew/plugins/steamdecky-controller/bin/usbip
deck ALL=(ALL) NOPASSWD: /home/deck/homebrew/plugins/steamdecky-controller/bin/usbipd
deck ALL=(ALL) NOPASSWD: /sbin/modprobe usbip-core
deck ALL=(ALL) NOPASSWD: /sbin/modprobe usbip_core
deck ALL=(ALL) NOPASSWD: /sbin/modprobe usbip-host
deck ALL=(ALL) NOPASSWD: /sbin/modprobe usbip_host
deck ALL=(ALL) NOPASSWD: /usr/bin/modprobe usbip-core
deck ALL=(ALL) NOPASSWD: /usr/bin/modprobe usbip_core
deck ALL=(ALL) NOPASSWD: /usr/bin/modprobe usbip-host
deck ALL=(ALL) NOPASSWD: /usr/bin/modprobe usbip_host
SUDOERS

sudo chmod 0440 "$SUDOERS_FILE"

echo "Sudoers configuration created successfully!"
echo "The plugin can now run usbip commands with sudo."

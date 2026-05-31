#!/bin/bash
# Create udev rule to allow deck user to bind/unbind USB devices

UDEV_RULE="/etc/udev/rules.d/99-steamdecky-controller.rules"

echo "Creating udev rule for USB device access..."

sudo tee "$UDEV_RULE" > /dev/null << 'RULE'
# Allow deck user to bind/unbind Valve Steam Deck Controller
# Valve vendor ID: 28de
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="28de", RUN+="/bin/chmod 666 /sys$devpath/driver/unbind /sys$devpath/driver/bind"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="28de", RUN+="/bin/chgrp deck /sys$devpath/driver/unbind /sys$devpath/driver/bind"
RULE

sudo chmod 644 "$UDEV_RULE"

echo "Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "Done! Unplug and replug the controller or reboot for changes to take effect."
echo "Or run: sudo udevadm trigger --action=add"

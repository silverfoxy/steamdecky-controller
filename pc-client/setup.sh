#!/usr/bin/env bash
# Setup script for Steam Deck Controller Client (PC side)

set -e

echo "=========================================="
echo "Steam Deck Controller Client Setup"
echo "=========================================="
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Error: This script is for Linux only"
    exit 1
fi

# Install python3-uinput
echo "[1/3] Installing python3-uinput..."
if command -v apt &>/dev/null; then
    sudo apt update
    sudo apt install -y python3-uinput
elif command -v dnf &>/dev/null; then
    sudo dnf install -y python3-uinput
elif command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm python-uinput
else
    echo "Warning: Could not detect package manager. Please install python3-uinput manually."
fi

# Load uinput module
echo "[2/3] Loading uinput kernel module..."
sudo modprobe uinput

# Make uinput load on boot
echo "[3/3] Configuring uinput to load on boot..."
if [[ ! -f /etc/modules-load.d/uinput.conf ]]; then
    echo "uinput" | sudo tee /etc/modules-load.d/uinput.conf > /dev/null
    echo "Created /etc/modules-load.d/uinput.conf"
fi

# Optional: Add user to input group
echo ""
read -p "Add current user to 'input' group? (allows running without sudo) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo usermod -a -G input "$USER"
    echo "Added $USER to input group. You'll need to log out and back in for this to take effect."
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To use:"
echo "  python3 pc_client.py -p 9090"
echo ""
echo "Then on your Steam Deck:"
echo "  1. Open Decky plugin"
echo "  2. Enter this PC's IP address"
echo "  3. Click 'Start Sharing'"
echo ""

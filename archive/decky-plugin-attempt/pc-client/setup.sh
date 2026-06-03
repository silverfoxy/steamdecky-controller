#!/bin/bash
# Setup script for Steam Deck Controller PC Client

set -e

echo "========================================="
echo "Steam Deck Controller - PC Client Setup"
echo "========================================="
echo ""

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS. Please install python3-uinput manually."
    exit 1
fi

echo "Detected OS: $OS"
echo ""

# Install python-uinput based on OS
case "$OS" in
    ubuntu|debian|pop|linuxmint)
        echo "Installing python3-uinput via apt..."
        sudo apt update
        sudo apt install -y python3-uinput
        ;;
    arch|manjaro)
        echo "Installing python-evdev via pacman..."
        sudo pacman -S --noconfirm python-evdev
        ;;
    fedora)
        echo "Installing python3-uinput via dnf..."
        sudo dnf install -y python3-uinput
        ;;
    *)
        echo "Unsupported OS: $OS"
        echo "Please install python-uinput manually:"
        echo "  pip install python-uinput"
        exit 1
        ;;
esac

echo ""
echo "✓ Dependencies installed successfully!"
echo ""
echo "Usage:"
echo "  python3 pc_client.py <steam_deck_ip> [-p port]"
echo ""
echo "Example:"
echo "  python3 pc_client.py 192.168.1.206 -p 9090"
echo ""

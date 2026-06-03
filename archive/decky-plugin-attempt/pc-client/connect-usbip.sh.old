#!/usr/bin/env bash
# connect.sh — attach Steam Deck controller via USB/IP
set -euo pipefail

DECK_IP="${1:-}"

usage() {
    echo "Usage: $0 <steam-deck-ip>"
    echo "Example: $0 192.168.1.42"
    echo ""
    echo "Find the Deck's IP in the DeckController plugin panel."
    exit 1
}

[[ -z "$DECK_IP" ]] && usage

# Check for usbip
if ! command -v usbip &>/dev/null; then
    echo "usbip not found. Install it:"
    echo "  Arch/SteamOS: sudo pacman -S usbip"
    echo "  Ubuntu/Debian: sudo apt install linux-tools-generic"
    exit 1
fi

echo "Loading vhci-hcd kernel module..."
sudo modprobe vhci-hcd

echo ""
echo "Devices available on $DECK_IP:"
usbip list -r "$DECK_IP"
echo ""

# Auto-detect Valve controller busid
BUSID=$(usbip list -r "$DECK_IP" 2>/dev/null \
    | grep -i "28de" \
    | grep -oP '^\s+\K[0-9]+-[0-9.]+(?=:)' \
    | head -1 || true)

if [[ -z "$BUSID" ]]; then
    read -rp "Valve controller not auto-detected. Enter bus ID from the list above: " BUSID
fi

echo "Attaching busid $BUSID from $DECK_IP..."
sudo usbip attach -r "$DECK_IP" -b "$BUSID"

echo ""
echo "Controller attached. To disconnect:"
echo "  ./disconnect.sh"

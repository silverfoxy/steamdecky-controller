#!/usr/bin/env bash
# disconnect.sh — detach the Steam Deck controller USB/IP port
set -euo pipefail

PORT="${1:-}"

if [[ -z "$PORT" ]]; then
    echo "Attached USB/IP ports:"
    sudo usbip port || true
    echo ""
    read -rp "Enter port number to detach (e.g. 00): " PORT
fi

sudo usbip detach -p "$PORT"
echo "Detached port $PORT."

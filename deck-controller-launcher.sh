#!/bin/bash
# Launcher wrapper for Steam Non-Game shortcut
# This ensures the script runs in a terminal window

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use Konsole (default terminal on Steam Deck)
konsole --hold -e "$SCRIPT_DIR/deck-start-usbip.sh"

#!/bin/bash
# Add Deck Controller Forwarder to Steam as non-Steam game

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCHER="$SCRIPT_DIR/launch-terminal.sh"

# Find Steam userdata directory
STEAM_DIR="$HOME/.local/share/Steam"
USERDATA_DIR="$STEAM_DIR/userdata"

if [ ! -d "$USERDATA_DIR" ]; then
    echo "Error: Steam userdata directory not found at $USERDATA_DIR"
    exit 1
fi

# Find the user ID (usually there's only one)
USER_ID=$(ls -1 "$USERDATA_DIR" | grep -E '^[0-9]+$' | head -1)

if [ -z "$USER_ID" ]; then
    echo "Error: Could not find Steam user ID"
    exit 1
fi

SHORTCUTS_VDF="$USERDATA_DIR/$USER_ID/config/shortcuts.vdf"

echo "Steam User ID: $USER_ID"
echo "Shortcuts file: $SHORTCUTS_VDF"
echo ""

# Create a .desktop file (alternative method that works better)
DESKTOP_FILE="$HOME/.local/share/applications/deck-controller-forwarder.desktop"

mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Deck Controller Forwarder
Comment=Forward Steam Deck controller to PC over network
Exec=$LAUNCHER
Icon=input-gaming
Terminal=false
Type=Application
Categories=Game;
EOF

echo "✓ Created desktop entry: $DESKTOP_FILE"
echo ""
echo "Now you can add it to Steam:"
echo "1. Open Steam in Desktop Mode"
echo "2. Go to Games → Add a Non-Steam Game"
echo "3. Click 'Browse' and navigate to:"
echo "   $HOME/.local/share/applications/"
echo "4. Select 'deck-controller-forwarder.desktop'"
echo ""
echo "OR just browse directly to:"
echo "   $LAUNCHER"
echo ""
echo "The desktop file makes it easier to find in the file picker."

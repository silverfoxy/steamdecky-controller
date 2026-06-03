#!/bin/bash
# Launch controller forwarder in a terminal window
# This allows it to work as a non-Steam game

# Clear Steam runtime environment variables to avoid LD_PRELOAD warnings
unset LD_PRELOAD
unset LD_LIBRARY_PATH
unset STEAM_RUNTIME

cd "$(dirname "$0")"

# Try different terminal emulators
if command -v ghostty &> /dev/null; then
    ghostty --fullscreen -e /usr/bin/python3 deck_controller_simple.py
elif command -v konsole &> /dev/null; then
    konsole --fullscreen -e /usr/bin/python3 deck_controller_simple.py
elif command -v gnome-terminal &> /dev/null; then
    gnome-terminal --full-screen -- /usr/bin/python3 deck_controller_simple.py
elif command -v xterm &> /dev/null; then
    xterm -fullscreen -e /usr/bin/python3 deck_controller_simple.py
else
    # Fallback: just run it (will work but no visible output)
    /usr/bin/python3 deck_controller_simple.py
fi

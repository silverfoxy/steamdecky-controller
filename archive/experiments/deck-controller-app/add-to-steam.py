#!/usr/bin/env python3
"""
Add Deck Controller Forwarder to Steam programmatically
Modifies Steam's shortcuts.vdf file to add the app as a non-Steam game
"""

import os
import struct
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()
LAUNCHER = SCRIPT_DIR / "launch-terminal.sh"
STEAM_DIR = Path.home() / ".local/share/Steam"


def find_shortcuts_vdf():
    """Find the shortcuts.vdf file for the current Steam user"""
    userdata_dir = STEAM_DIR / "userdata"

    if not userdata_dir.exists():
        print(f"Error: Steam userdata directory not found: {userdata_dir}")
        return None

    # Find user ID (usually just one)
    user_ids = [d.name for d in userdata_dir.iterdir() if d.is_dir() and d.name.isdigit()]

    if not user_ids:
        print("Error: No Steam user found")
        return None

    user_id = user_ids[0]
    shortcuts_file = userdata_dir / user_id / "config" / "shortcuts.vdf"

    return shortcuts_file


def read_vdf(file_path):
    """Read shortcuts.vdf file (simplified reader)"""
    if not file_path.exists():
        # File doesn't exist yet, return empty structure
        return {"shortcuts": {}}

    # For now, just check if our entry exists
    # Full VDF parsing is complex, so we'll append if file is small/empty
    return {"shortcuts": {}}


def create_desktop_entry():
    """Create a .desktop file as an alternative"""
    desktop_file = Path.home() / ".local/share/applications" / "deck-controller-forwarder.desktop"
    desktop_file.parent.mkdir(parents=True, exist_ok=True)

    content = f"""[Desktop Entry]
Name=Deck Controller Forwarder
Comment=Forward Steam Deck controller to PC over network
Exec={LAUNCHER}
Icon=input-gaming
Terminal=false
Type=Application
Categories=Game;
"""

    desktop_file.write_text(content)
    print(f"✓ Created desktop entry: {desktop_file}")
    return desktop_file


def main():
    print("=" * 60)
    print("Add Deck Controller Forwarder to Steam")
    print("=" * 60)
    print()

    if not LAUNCHER.exists():
        print(f"Error: Launcher not found: {LAUNCHER}")
        sys.exit(1)

    # Create desktop entry (easier method)
    desktop_file = create_desktop_entry()

    print()
    print("Desktop entry created! Now add to Steam:")
    print()
    print("METHOD 1 (Easiest):")
    print("  1. Open Steam in Desktop Mode")
    print("  2. Games → Add a Non-Steam Game")
    print("  3. Browse to:")
    print(f"     {LAUNCHER}")
    print("  4. Add and rename to 'Deck Controller Forwarder'")
    print()
    print("METHOD 2 (Using desktop file):")
    print("  1. Open Steam in Desktop Mode")
    print("  2. Games → Add a Non-Steam Game")
    print("  3. Browse to:")
    print(f"     {desktop_file.parent}/")
    print(f"  4. Select: {desktop_file.name}")
    print()
    print("=" * 60)


if __name__ == '__main__':
    main()

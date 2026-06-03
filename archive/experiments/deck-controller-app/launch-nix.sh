#!/bin/bash
# Launcher using Nix for dependencies

cd "$(dirname "$0")"

# Launch app in Nix shell with pygame available
nix-shell -p python3 python3Packages.pygame python3Packages.evdev --run "python3 deck_controller_app.py"

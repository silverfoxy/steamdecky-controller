#!/bin/bash
# Connect to Steam Deck controller via USB/IP from PC

echo "========================================"
echo "Connect to Steam Deck Controller"
echo "========================================"
echo

# Check if usbip is installed
if ! command -v usbip &> /dev/null; then
    echo "ERROR: usbip not installed"
    echo "Install on Ubuntu/Debian: sudo apt install linux-tools-generic"
    echo "Install on Fedora: sudo dnf install usbip"
    echo "Install on Arch: sudo pacman -S usbip"
    exit 1
fi

# Without arguments discover the actively sharing Deck via mDNS/Avahi.
# Explicit IP and bus ID remain available if multicast discovery is blocked.
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [ "$#" -eq 0 ]; then
    if ! command -v python3 >/dev/null 2>&1; then
        echo "ERROR: python3 is required for automatic discovery" >&2
        exit 1
    fi
    DISCOVERY=$(python3 "$SCRIPT_DIR/discover_deck.py") || exit 1
    IFS=$'\t' read -r DECK_IP BUSID <<< "$DISCOVERY"
else
    DECK_IP=$1
    BUSID=${2:-"3-3"}  # Legacy manual default; pass the Deck's displayed bus ID if different.
fi

if [[ ! $BUSID =~ ^[0-9]+-[0-9]+(\.[0-9]+)*$ ]]; then
    echo "ERROR: Invalid USB bus ID: $BUSID" >&2
    exit 1
fi

echo "Deck IP: $DECK_IP"
echo "Bus ID: $BUSID"
echo

# Steam must be running on the PC for full controller support.
#
# Without Steam, the controller stays in "lizard mode" — a built-in fallback
# where it acts as a generic keyboard + mouse so it remains usable on any
# desktop. In lizard mode the hid-steam kernel driver only creates two input
# devices: a keyboard (interfaces 0) and a mouse (interface 1). Interface 2,
# which carries the touchpad touch data, paddle buttons (L4/L5/R4/R5), gyro,
# and analog stick data, never gets an input node at all.
#
# When Steam starts it opens /dev/hidraw* for the controller exclusively and
# sends a HID feature report that disables lizard mode. The controller then
# switches to its custom protocol and hid-steam exposes everything through a
# virtual Xbox 360 compatible gamepad that games can use via Steam Input.
#
# TL;DR: start Steam on this PC before (or after) running this script,
# otherwise only basic keyboard/mouse emulation will work.

# Waybar must fail with a useful error instead of opening a password dialog.
privilege=(sudo)
if [[ ${STEAM_DECK_NONINTERACTIVE:-0} == 1 ]]; then
    privilege+=(-n)
fi

# Load kernel modules
echo "Loading USB/IP kernel modules..."
"${privilege[@]}" modprobe vhci-hcd || exit 1

# Confirm that the selected bus ID is actually the Steam Deck controller.
# An mDNS TXT record is not proof; do not attach an unrelated USB device.
if ! REMOTE_DEVICES=$(usbip list -r "$DECK_IP"); then
    echo "ERROR: Could not list USB/IP devices on $DECK_IP" >&2
    exit 1
fi
printf '%s\n' "$REMOTE_DEVICES"
if ! printf '%s\n' "$REMOTE_DEVICES" | awk -v busid="$BUSID" '
    { line = $0; sub(/^[[:space:]]*-?[[:space:]]*/, "", line) }
    index(line, busid ":") == 1 && tolower(line) ~ /\(28de:1205\)/ { found = 1 }
    END { exit !found }
'; then
    echo "ERROR: $BUSID on $DECK_IP is not an exported Steam Deck controller" >&2
    exit 1
fi

# Attach the device
echo "Attaching controller..."
"${privilege[@]}" usbip attach -r "$DECK_IP" -b "$BUSID"

if [ $? -eq 0 ]; then
    echo
    echo "========================================"
    echo "SUCCESS! Controller connected"
    echo "========================================"
    echo
    echo "Check with: sudo usbip port"
    echo "To disconnect, run: ./pc-disconnect.sh"
else
    echo "ERROR: Failed to attach device"
    exit 1
fi

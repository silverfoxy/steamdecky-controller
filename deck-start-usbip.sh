#!/bin/bash
# Start USB/IP sharing of Steam Deck controller

# Clear Steam environment variables that interfere with Nix
unset LD_PRELOAD
unset LD_LIBRARY_PATH

# Log file
LOGFILE="/tmp/steamdecky-controller.log"

# Clear previous log
> "$LOGFILE"

# Logging function with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $@" | tee -a "$LOGFILE"
}

log "========================================"
log "Steam Deck Controller USB/IP - START"
log "$(date)"
log "========================================"
log ""

# Find usbip (check Nix profile first, then system)
if [ -f "$HOME/.nix-profile/bin/usbip" ]; then
    USBIP="$HOME/.nix-profile/bin/usbip"
    USBIPD="$HOME/.nix-profile/bin/usbipd"
elif command -v usbip &> /dev/null; then
    USBIP=$(command -v usbip)
    USBIPD=$(command -v usbipd)
else
    log "ERROR: usbip not installed"
    log "Install with: nix profile install nixpkgs#linuxPackages.usbip"
    exit 1
fi

log "Using usbip: $USBIP"
log ""

# Find the Steam Deck controller USB device
log "Finding Steam Deck controller..."

# Use usbip list to get correct busid format
DEVICE_INFO=$("$USBIP" list -l 2>>"$LOGFILE" | grep -i "28de:1205\|valve")

if [ -z "$DEVICE_INFO" ]; then
    log "ERROR: Steam Deck controller not found"
    log ""
    log "All USB devices:"
    "$USBIP" list -l 2>>"$LOGFILE" | tee -a "$LOGFILE"
    exit 1
fi

log "Found: $DEVICE_INFO"

# Extract busid (format: busid 3-3)
BUSID=$(echo "$DEVICE_INFO" | grep -oP 'busid \K[0-9]+-[0-9]+' | head -1)

if [ -z "$BUSID" ]; then
    log "ERROR: Could not parse busid"
    exit 1
fi

log "Bus ID: $BUSID"
log ""

# Load usbip modules
log "Loading usbip kernel modules..."
sudo modprobe usbip-core 2>>"$LOGFILE"
sudo modprobe usbip-host 2>>"$LOGFILE"

# Start usbipd daemon
log "Starting usbip daemon..."
sudo "$USBIPD" -D 2>>"$LOGFILE"

# Bind the device
log "Binding controller device..."
sudo "$USBIP" bind -b "$BUSID" 2>>"$LOGFILE"

if [ $? -eq 0 ]; then
    log ""
    log "========================================"
    log "SUCCESS! Controller exported via USB/IP"
    log "========================================"
    log ""
    log "On your PC, run:"
    log "  sudo usbip attach -r <deck-ip> -b $BUSID"
    log ""
    log "Or for LOCAL TEST MODE on Deck:"
    log "  sudo $USBIP attach -r 127.0.0.1 -b $BUSID"
    log ""
    log "Your Deck IP: $(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1 | head -1)"
    log ""
    log "To stop sharing, run: ./deck-stop-usbip.sh"
else
    log "ERROR: Failed to bind device"
    exit 1
fi

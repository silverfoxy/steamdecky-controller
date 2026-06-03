#!/bin/bash
# Stop USB/IP sharing and restore controller

# Clear Steam environment variables
unset LD_PRELOAD
unset LD_LIBRARY_PATH

# Log file
LOGFILE="/tmp/steamdecky-controller.log"

# Logging function with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $@" | tee -a "$LOGFILE"
}

log "========================================"
log "Steam Deck Controller USB/IP - STOP"
log "$(date)"
log "========================================"
log ""

# Use full Nix path for usbip
USBIP="$HOME/.nix-profile/bin/usbip"

# Stop daemon first
log "Stopping usbip daemon..."
sudo killall usbipd 2>>"$LOGFILE"

# Find devices bound to usbip-host driver
log "Finding devices bound to usbip-host..."
BOUND_DEVICES=$(ls /sys/bus/usb/drivers/usbip-host/ 2>/dev/null | grep -E '^[0-9]+-[0-9]+')

if [ -z "$BOUND_DEVICES" ]; then
    log "No devices currently bound to usbip-host"
else
    log "Found: $BOUND_DEVICES"
    log ""

    # Unbind from usbip-host
    for BUSID in $BOUND_DEVICES; do
        log "Unbinding $BUSID from usbip-host..."
        echo "$BUSID" | sudo tee /sys/bus/usb/drivers/usbip-host/unbind > /dev/null 2>>"$LOGFILE"

        # Rebind to original driver (xpad for Steam Deck controller)
        log "Rebinding $BUSID to system..."
        echo "$BUSID" | sudo tee /sys/bus/usb/drivers_probe > /dev/null 2>>"$LOGFILE"
    done
fi

log ""
log "========================================"
log "Controller restored to Deck"
log "========================================"

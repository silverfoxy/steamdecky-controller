#!/usr/bin/env python3
"""
Controller Event Forwarder (Steam Deck Side)
Reads events from Steam Deck controller and forwards to PC
"""

import os
import socket
import struct
import sys
import time
from pathlib import Path

# Add bundled dependencies to path if running from plugin
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_PATH = os.path.join(SCRIPT_DIR, "lib")
if os.path.exists(LIB_PATH):
    sys.path.insert(0, LIB_PATH)

try:
    from evdev import InputDevice, categorize, ecodes, list_devices
except ImportError:
    print("Error: python-evdev not installed")
    print("This should be available on Steam Deck by default")
    sys.exit(1)

# Event format matching PC client
EVENT_FORMAT = "HHi"

def find_steam_deck_controller():
    """Find the Steam Deck controller device"""
    devices = [InputDevice(path) for path in list_devices()]
    
    for device in devices:
        # Look for Valve vendor ID (0x28de)
        if device.info.vendor == 0x28de and device.info.product == 0x1205:
            return device
        # Also check by name
        if "Steam" in device.name and "Deck" in device.name:
            return device
    
    return None

def forward_events_server(port=9090):
    """Run UDP server to forward controller events to connected clients"""

    # Find controller
    print("Finding Steam Deck controller...")
    controller = find_steam_deck_controller()

    if not controller:
        print("Error: Steam Deck controller not found!")
        print("\nAvailable devices:")
        for device in [InputDevice(path) for path in list_devices()]:
            print(f"  {device.name} - {device.path}")
        return False

    print(f"Found controller: {controller.name}")
    print(f"Device: {controller.path}")
    print(f"Starting UDP server on port {port}")
    print("Waiting for PC client to connect...")

    # Create UDP socket and bind to port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))
    sock.settimeout(0.1)  # Non-blocking with timeout

    client_addr = None
    event_count = 0

    try:
        # Read events from controller
        for event in controller.read_loop():
            # Pack event data
            data = struct.pack(EVENT_FORMAT, event.type, event.code, event.value)

            # Check for client registration (PC sends any packet to register)
            try:
                msg, addr = sock.recvfrom(1024)
                if client_addr != addr:
                    client_addr = addr
                    print(f"PC client connected from {addr[0]}:{addr[1]}")
            except socket.timeout:
                pass

            # Send to connected client
            if client_addr:
                sock.sendto(data, client_addr)
                event_count += 1

    except KeyboardInterrupt:
        print(f"\nStopped. Total events: {event_count}")
    except Exception as e:
        print(f"\nError: {e}")
        return False
    finally:
        sock.close()

    return True

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Steam Deck Controller Forwarder Server')
    parser.add_argument('-p', '--port', type=int, default=9090, help='Port to listen on (default: 9090)')

    args = parser.parse_args()

    print("=" * 60)
    print("Steam Deck Controller Forwarder Server")
    print("=" * 60)

    success = forward_events_server(args.port)
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Controller Event Forwarder (Steam Deck Side)
Reads events from Steam Deck controller and forwards to PC
"""

import os
import select
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
MOUSE_PACKET_FORMAT = "cff"

# Mouse control options
MOUSE_FROM_RIGHT_STICK = False  # Set to True to use right stick as mouse
MOUSE_SENSITIVITY = 2.0

def find_steam_deck_controller():
    """Find gamepad device with actual gamepad buttons (same logic as decktation)"""
    for path in list_devices():
        try:
            device = InputDevice(path)
            name_lower = device.name.lower()

            # Check if device has gamepad capabilities (BTN_SOUTH, BTN_NORTH, etc.)
            caps = device.capabilities()
            has_gamepad_buttons = False
            if 1 in caps:  # EV_KEY
                key_codes = caps[1]
                # Check for gamepad buttons (304-307 are SOUTH/EAST/NORTH/WEST, 310-311 are TL/TR)
                has_gamepad_buttons = any(code in key_codes for code in [304, 305, 307, 308, 310, 311])

            # Only match devices that have actual gamepad buttons
            if has_gamepad_buttons and any(keyword in name_lower for keyword in ["x-box 360", "xbox 360", "gamepad", "steam deck controller", "valve"]):
                return device
        except:
            pass

    return None

def forward_events_server(port=9090):
    """Run UDP server to forward controller events to connected clients"""

    # Status file for tracking client connections
    status_file = Path("/tmp/deck_controller_status.txt")

    def update_status(client_ip=None):
        """Write connection status to file"""
        if client_ip:
            status_file.write_text(f"connected:{client_ip}")
        else:
            status_file.write_text("waiting")

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
    if MOUSE_FROM_RIGHT_STICK:
        print("Right stick → Mouse cursor")
    print("Waiting for PC client to connect...")

    # Create UDP socket and bind to port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))
    sock.settimeout(0.1)  # Non-blocking with timeout

    client_addr = None
    event_count = 0
    mouse_count = 0

    # Track right stick position for mouse conversion
    last_rx = 0
    last_ry = 0

    # Initial status
    update_status()

    try:
        # Event loop - check both controller and network socket
        while True:
            # Check for client registration packets (non-blocking)
            try:
                msg, addr = sock.recvfrom(1024)
                if client_addr != addr:
                    client_addr = addr
                    print(f"PC client connected from {addr[0]}:{addr[1]}")
                    update_status(addr[0])
            except socket.timeout:
                pass

            # Check for controller events with timeout
            r, w, x = select.select([controller.fd], [], [], 0.01)
            if r:
                # Read available events
                events = controller.read()
                for event in events:
                    # Optionally convert right stick to mouse
                    if MOUSE_FROM_RIGHT_STICK and event.type == ecodes.EV_ABS:
                        if event.code == ecodes.ABS_RX:  # Right stick X
                            last_rx = event.value
                            # Convert stick position to mouse movement
                            # Deadzone: ignore small movements
                            if abs(last_rx) > 3000:
                                rel_x = (last_rx / 32768.0) * MOUSE_SENSITIVITY
                                if client_addr:
                                    mouse_data = struct.pack(MOUSE_PACKET_FORMAT, b'M', rel_x, 0.0)
                                    sock.sendto(mouse_data, client_addr)
                                    mouse_count += 1
                            continue  # Don't send as gamepad event

                        elif event.code == ecodes.ABS_RY:  # Right stick Y
                            last_ry = event.value
                            # Convert stick position to mouse movement
                            if abs(last_ry) > 3000:
                                rel_y = (last_ry / 32768.0) * MOUSE_SENSITIVITY
                                if client_addr:
                                    mouse_data = struct.pack(MOUSE_PACKET_FORMAT, b'M', 0.0, rel_y)
                                    sock.sendto(mouse_data, client_addr)
                                    mouse_count += 1
                            continue  # Don't send as gamepad event

                    # Regular gamepad event - pack and send
                    data = struct.pack(EVENT_FORMAT, event.type, event.code, event.value)

                    # Send to connected client
                    if client_addr:
                        sock.sendto(data, client_addr)
                        event_count += 1
                        if (event_count + mouse_count) % 100 == 0:
                            print(f"Forwarded {event_count} gamepad, {mouse_count} mouse", flush=True)

    except KeyboardInterrupt:
        print(f"\nStopped. Total: {event_count} gamepad, {mouse_count} mouse")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        sock.close()
        # Clean up status file
        if status_file.exists():
            status_file.unlink()

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

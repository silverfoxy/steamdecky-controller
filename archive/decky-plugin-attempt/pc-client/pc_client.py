#!/usr/bin/env python3
"""
Steam Deck Controller Client (PC Side)
Receives controller events from Steam Deck and creates virtual controller + mouse
"""

import socket
import struct
import sys
import argparse

try:
    import uinput
except ImportError:
    print("Error: python-uinput not installed")
    print("Install with: sudo apt install python3-uinput")
    sys.exit(1)

# Event structure from evdev
# Format: unsigned short (type), unsigned short (code), int (value)
EVENT_SIZE = 8
EVENT_FORMAT = "HHi"

# Special packet type for mouse movement
# Format: 'M', float (rel_x), float (rel_y)
MOUSE_PACKET_SIZE = 9
MOUSE_PACKET_FORMAT = "cff"

# Steam Deck controller capabilities
# Based on Xbox 360 emulation that Steam provides
BUTTONS = [
    uinput.BTN_SOUTH,    # A
    uinput.BTN_EAST,     # B
    uinput.BTN_NORTH,    # X
    uinput.BTN_WEST,     # Y
    uinput.BTN_TL,       # L1
    uinput.BTN_TR,       # R1
    uinput.BTN_TL2,      # L2
    uinput.BTN_TR2,      # R2
    uinput.BTN_SELECT,   # View/Back
    uinput.BTN_START,    # Menu
    uinput.BTN_MODE,     # Steam button
    uinput.BTN_THUMBL,   # L3
    uinput.BTN_THUMBR,   # R3
]

# Xbox 360 ranges (Steam sends these ranges)
# Sticks: -32768 to +32767
# Triggers: 0 to 255
# D-pad: -1, 0, +1
AXES = [
    uinput.ABS_X + (-32768, 32767, 16, 128),      # Left stick X
    uinput.ABS_Y + (-32768, 32767, 16, 128),      # Left stick Y
    uinput.ABS_RX + (-32768, 32767, 16, 128),     # Right stick X
    uinput.ABS_RY + (-32768, 32767, 16, 128),     # Right stick Y
    uinput.ABS_Z + (0, 255, 0, 0),                # L2 trigger
    uinput.ABS_RZ + (0, 255, 0, 0),               # R2 trigger
    uinput.ABS_HAT0X + (-1, 1, 0, 0),             # D-pad X
    uinput.ABS_HAT0Y + (-1, 1, 0, 0),             # D-pad Y
]

def create_virtual_controller():
    """Create virtual controller that matches Steam Deck controller"""
    print("Creating virtual Steam Deck controller...")

    device = uinput.Device(
        BUTTONS + AXES,
        name="Steam Deck Controller (Network)",
        bustype=uinput.BUS_USB,
        vendor=0x28de,  # Valve
        product=0x1205, # Steam Deck Controller
        version=0x0200
    )

    print(f"Virtual controller created: {device.device}")
    return device

def create_virtual_mouse():
    """Create virtual mouse for trackpad input"""
    print("Creating virtual mouse...")

    mouse = uinput.Device([
        uinput.REL_X,
        uinput.REL_Y,
        uinput.BTN_LEFT,
        uinput.BTN_RIGHT,
        uinput.BTN_MIDDLE,
    ], name="Steam Deck Mouse (Network)")

    print(f"Virtual mouse created: {mouse.device}")
    return mouse

def receive_events(deck_ip, port=9090, debug=False):
    """Receive events from Steam Deck and inject into virtual controller + mouse"""

    if not deck_ip:
        print("Error: Steam Deck IP address required")
        print("Usage: python3 pc_client.py <deck_ip> [-p port]")
        sys.exit(1)

    # Create virtual controller and mouse
    virtual = create_virtual_controller()
    mouse = create_virtual_mouse()

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))

    # Send registration packet to Steam Deck
    print(f"Registering with Steam Deck at {deck_ip}:{port}...")
    sock.sendto(b"REGISTER", (deck_ip, port))

    print(f"Listening for events from Steam Deck...")
    print("Right trackpad will control mouse cursor")
    print("Press Ctrl+C to stop")
    if debug:
        print("\nDebug output enabled - showing all events:")

    event_count = 0
    mouse_count = 0

    try:
        while True:
            # Receive packet (could be gamepad event or mouse movement)
            data, addr = sock.recvfrom(max(EVENT_SIZE, MOUSE_PACKET_SIZE))

            if len(data) == MOUSE_PACKET_SIZE and data[0:1] == b'M':
                # Mouse movement packet
                _, rel_x, rel_y = struct.unpack(MOUSE_PACKET_FORMAT, data)
                if debug:
                    print(f"MOUSE: x={rel_x:.1f}, y={rel_y:.1f}")
                mouse.emit(uinput.REL_X, int(rel_x))
                mouse.emit(uinput.REL_Y, int(rel_y))
                mouse_count += 1
                if not debug and mouse_count % 100 == 0:
                    print(f"Events: {event_count} gamepad, {mouse_count} mouse", end='\r')
            elif len(data) == EVENT_SIZE:
                # Gamepad event
                ev_type, ev_code, ev_value = struct.unpack(EVENT_FORMAT, data)
                if debug:
                    print(f"GAMEPAD: type={ev_type}, code={ev_code}, value={ev_value}")
                virtual.emit(ev_type, ev_code, ev_value, syn=False)
                event_count += 1
                if not debug and event_count % 100 == 0:
                    print(f"Events: {event_count} gamepad, {mouse_count} mouse", end='\r')

    except KeyboardInterrupt:
        print(f"\nStopped. Total events: {event_count} gamepad, {mouse_count} mouse")
    finally:
        sock.close()

def main():
    parser = argparse.ArgumentParser(description='Steam Deck Controller Client')
    parser.add_argument('deck_ip', help='Steam Deck IP address')
    parser.add_argument('-p', '--port', type=int, default=9090, help='Port to connect to (default: 9090)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')

    args = parser.parse_args()

    print("=" * 60)
    print("Steam Deck Controller Client")
    print("=" * 60)
    print(f"Connecting to Steam Deck at {args.deck_ip}:{args.port}")
    if args.debug:
        print("Debug mode: ON")
    print()

    receive_events(args.deck_ip, args.port, debug=args.debug)

if __name__ == '__main__':
    main()

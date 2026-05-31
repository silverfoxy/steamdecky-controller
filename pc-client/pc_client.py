#!/usr/bin/env python3
"""
Steam Deck Controller Client (PC Side)
Receives controller events from Steam Deck and creates virtual controller
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

# Steam Deck controller capabilities
# Based on evdev capabilities for Valve Steam Deck Controller
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

AXES = [
    uinput.ABS_X + (0, 65535, 0, 0),      # Left stick X
    uinput.ABS_Y + (0, 65535, 0, 0),      # Left stick Y
    uinput.ABS_RX + (0, 65535, 0, 0),     # Right stick X
    uinput.ABS_RY + (0, 65535, 0, 0),     # Right stick Y
    uinput.ABS_Z + (0, 255, 0, 0),        # L2 trigger
    uinput.ABS_RZ + (0, 255, 0, 0),       # R2 trigger
    uinput.ABS_HAT0X + (-1, 1, 0, 0),     # D-pad X
    uinput.ABS_HAT0Y + (-1, 1, 0, 0),     # D-pad Y
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

def receive_events(deck_ip, port=9090):
    """Receive events from Steam Deck and inject into virtual controller"""
    
    # Create virtual controller
    virtual = create_virtual_controller()
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))
    
    print(f"Listening for events from Steam Deck on port {port}...")
    print("Press Ctrl+C to stop")
    
    event_count = 0
    
    try:
        while True:
            # Receive event packet
            data, addr = sock.recvfrom(EVENT_SIZE)
            
            if len(data) != EVENT_SIZE:
                continue
                
            # Unpack event
            ev_type, ev_code, ev_value = struct.unpack(EVENT_FORMAT, data)
            
            # Inject into virtual controller
            virtual.emit(ev_type, ev_code, ev_value, syn=False)
            
            event_count += 1
            if event_count % 100 == 0:
                print(f"Events received: {event_count}", end='\r')
                
    except KeyboardInterrupt:
        print(f"\nStopped. Total events: {event_count}")
    finally:
        sock.close()

def main():
    parser = argparse.ArgumentParser(description='Steam Deck Controller Client')
    parser.add_argument('deck_ip', nargs='?', help='Steam Deck IP address (optional, receives from any)')
    parser.add_argument('-p', '--port', type=int, default=9090, help='Port to listen on (default: 9090)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Steam Deck Controller Client")
    print("=" * 60)
    
    receive_events(args.deck_ip, args.port)

if __name__ == '__main__':
    main()

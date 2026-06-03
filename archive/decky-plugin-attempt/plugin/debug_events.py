#!/usr/bin/env python3
"""
Debug script to identify Steam Deck trackpad event codes
Run this and touch the RIGHT trackpad to see which events are generated
"""

import sys
from evdev import InputDevice, categorize, ecodes, list_devices

def find_steam_deck_controller():
    """Find gamepad device"""
    for path in list_devices():
        try:
            device = InputDevice(path)
            name_lower = device.name.lower()
            caps = device.capabilities()
            has_gamepad_buttons = False
            if 1 in caps:
                key_codes = caps[1]
                has_gamepad_buttons = any(code in key_codes for code in [304, 305, 307, 308, 310, 311])

            if has_gamepad_buttons and any(keyword in name_lower for keyword in ["x-box 360", "xbox 360", "gamepad", "steam deck controller", "valve"]):
                return device
        except:
            pass
    return None

def main():
    print("Finding Steam Deck controller...")
    controller = find_steam_deck_controller()

    if not controller:
        print("Error: Controller not found!")
        return

    print(f"Found: {controller.name}")
    print(f"Device: {controller.path}")
    print("\n" + "=" * 60)
    print("Touch the RIGHT TRACKPAD and watch for events")
    print("We're looking for ABS (absolute) events with changing values")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    try:
        for event in controller.read_loop():
            if event.type == ecodes.EV_ABS:
                # Only show absolute events (axes, trackpad)
                code_name = ecodes.ABS[event.code] if event.code in ecodes.ABS else f"UNKNOWN({event.code})"
                print(f"ABS: {code_name:20s} (code={event.code:3d}) value={event.value:6d}")
    except KeyboardInterrupt:
        print("\nStopped")

if __name__ == '__main__':
    main()

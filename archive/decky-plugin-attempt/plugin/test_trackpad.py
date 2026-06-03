#!/usr/bin/env python3
"""Test if right trackpad generates mouse events"""

from evdev import InputDevice, ecodes

device = InputDevice('/dev/input/event14')
print(f"Monitoring: {device.name}")
print(f"Path: {device.path}")
print("\n" + "="*60)
print("Touch and move the RIGHT TRACKPAD")
print("You should see REL_X and REL_Y events")
print("Press Ctrl+C to stop")
print("="*60 + "\n")

try:
    for event in device.read_loop():
        if event.type == ecodes.EV_REL:
            type_name = ecodes.EV[event.type]
            code_name = ecodes.REL[event.code] if event.code in ecodes.REL else f"REL_{event.code}"
            print(f"{type_name:10s} {code_name:15s} value={event.value:6d}")
except KeyboardInterrupt:
    print("\nStopped")

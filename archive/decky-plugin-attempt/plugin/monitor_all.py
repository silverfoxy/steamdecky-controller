#!/usr/bin/env python3
"""Monitor ALL input devices simultaneously to find trackpad"""

import select
from evdev import InputDevice, list_devices, ecodes

# Open all devices EXCEPT Xbox 360 (too noisy)
devices = {}
for path in list_devices():
    try:
        dev = InputDevice(path)
        # Skip Xbox 360 pad - it's too noisy
        if 'x-box 360' in dev.name.lower() or 'xbox 360' in dev.name.lower():
            print(f"Skipping (noisy): {dev.name} ({dev.path})")
            continue
        devices[dev.fd] = dev
        print(f"Monitoring: {dev.name} ({dev.path})")
    except:
        pass

print("\n" + "="*80)
print("Touch and move the RIGHT TRACKPAD")
print("Any device that responds will be shown below")
print("Press Ctrl+C to stop")
print("="*80 + "\n")

try:
    while True:
        r, w, x = select.select(devices, [], [], 0.1)
        for fd in r:
            device = devices[fd]
            for event in device.read():
                # Only show potentially trackpad-related events
                if event.type in [ecodes.EV_REL, ecodes.EV_ABS, ecodes.EV_KEY]:
                    type_name = ecodes.EV[event.type] if event.type in ecodes.EV else f"EV_{event.type}"

                    code_name = "?"
                    if event.type == ecodes.EV_REL and event.code in ecodes.REL:
                        code_name = ecodes.REL[event.code]
                    elif event.type == ecodes.EV_ABS and event.code in ecodes.ABS:
                        code_name = ecodes.ABS[event.code]
                    elif event.type == ecodes.EV_KEY:
                        if event.code in ecodes.BTN:
                            code_name = ecodes.BTN[event.code]
                        elif event.code in ecodes.KEY:
                            code_name = ecodes.KEY[event.code]

                    print(f"[{device.name[:30]:30s}] {type_name:10s} {code_name:20s} = {event.value}")

except KeyboardInterrupt:
    print("\nStopped")

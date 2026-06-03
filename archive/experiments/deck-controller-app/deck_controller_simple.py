#!/usr/bin/env python3
"""
Steam Deck Controller Forwarder - Terminal Version
No dependencies needed (uses only standard library + evdev which is already on Steam Deck)
"""

import os
import sys
import socket
import struct
import select
import threading
import time
import signal
from pathlib import Path

try:
    from evdev import InputDevice, list_devices
except ImportError:
    print("Error: python-evdev not installed")
    print("This should be available on Steam Deck by default")
    sys.exit(1)

# Configuration
CONFIG_FILE = Path.home() / ".config" / "deck-controller-forwarder.conf"
DEFAULT_PORT = 9090

# Event format
EVENT_FORMAT = "HHi"


def load_config():
    """Load configuration from file"""
    config = {"port": DEFAULT_PORT}
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        if key == 'port':
                            config['port'] = int(value)
    except Exception as e:
        print(f"Error loading config: {e}, using defaults")
    return config


def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def find_steam_deck_controller():
    """Find gamepad device with actual gamepad buttons"""
    for path in list_devices():
        try:
            device = InputDevice(path)
            name_lower = device.name.lower()

            # Check if device has gamepad capabilities
            caps = device.capabilities()
            has_gamepad_buttons = False
            if 1 in caps:  # EV_KEY
                key_codes = caps[1]
                has_gamepad_buttons = any(code in key_codes for code in [304, 305, 307, 308, 310, 311])

            if has_gamepad_buttons and any(keyword in name_lower for keyword in ["x-box 360", "xbox 360", "gamepad", "steam deck controller", "valve"]):
                return device
        except:
            pass
    return None


class ControllerForwarder(threading.Thread):
    """Background thread that forwards controller events"""

    def __init__(self, controller, port):
        super().__init__(daemon=True)
        self.controller = controller
        self.port = port
        self.running = True
        self.client_ip = None
        self.event_count = 0
        self.grabbed = False

    def run(self):
        """Main forwarder loop"""
        try:
            # Grab controller for exclusive access
            self.controller.grab()
            self.grabbed = True
            print("🔒 Controller grabbed (Deck controls disabled)")

            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('0.0.0.0', self.port))
            sock.settimeout(0.1)

            print(f"👂 Listening on port {self.port}")

            while self.running:
                # Check for client registration
                try:
                    msg, addr = sock.recvfrom(1024)
                    if self.client_ip != addr[0]:
                        self.client_ip = addr[0]
                        print(f"✓ PC client connected: {addr[0]}")
                except socket.timeout:
                    pass

                # Check for controller events
                r, w, x = select.select([self.controller.fd], [], [], 0.01)
                if r:
                    events = self.controller.read()
                    for event in events:
                        # Pack and send event data
                        data = struct.pack(EVENT_FORMAT, event.type, event.code, event.value)
                        if self.client_ip:
                            sock.sendto(data, (self.client_ip, self.port))
                            self.event_count += 1

            sock.close()

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            try:
                if self.grabbed:
                    self.controller.ungrab()
                    print("🔓 Controller released")
            except:
                pass

    def stop(self):
        """Stop the forwarder"""
        self.running = False


def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_status(deck_ip, port, forwarder):
    """Print current status"""
    clear_screen()
    print("=" * 60)
    print("🎮  STEAM DECK CONTROLLER FORWARDER")
    print("=" * 60)
    print()

    if forwarder.client_ip:
        print(f"Status: ✓ CONNECTED TO PC")
        print(f"PC IP:  {forwarder.client_ip}")
    elif forwarder.grabbed:
        print(f"Status: ⏳ WAITING FOR PC CLIENT")
    else:
        print(f"Status: 🔄 STARTING...")

    print()
    print(f"Deck IP: {deck_ip}:{port}")
    print(f"Events:  {forwarder.event_count} forwarded")
    print()
    print("-" * 60)
    print("PC Client Command:")
    print(f"  python3 pc_client.py {deck_ip} -p {port}")
    print()
    print("-" * 60)
    print()
    print("Press Ctrl+C to stop and release controller")
    print("=" * 60)


def main():
    """Entry point"""
    print("=" * 60)
    print("Steam Deck Controller Forwarder - Terminal Version")
    print("=" * 60)
    print()

    config = load_config()
    deck_ip = get_local_ip()

    # Find controller
    print("🔍 Finding controller...")
    controller = find_steam_deck_controller()

    if not controller:
        print("❌ Controller not found!")
        print("\nMake sure you're in Gaming Mode (not Desktop Mode)")
        sys.exit(1)

    print(f"✓ Found: {controller.name}")
    print()

    # Start forwarder thread
    forwarder = ControllerForwarder(controller, config['port'])
    forwarder.start()

    # Give it a moment to start
    time.sleep(0.5)

    # Status update loop
    try:
        last_client = None
        last_events = 0

        while True:
            # Update display when something changes
            if (forwarder.client_ip != last_client or
                forwarder.event_count != last_events):
                print_status(deck_ip, config['port'], forwarder)
                last_client = forwarder.client_ip
                last_events = forwarder.event_count

            time.sleep(0.5)

    except KeyboardInterrupt:
        print()
        print("Stopping...")
        forwarder.stop()
        forwarder.join(timeout=2)
        print("✓ Stopped. Controller released.")


if __name__ == '__main__':
    main()

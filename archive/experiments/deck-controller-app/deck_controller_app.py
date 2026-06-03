#!/usr/bin/env python3
"""
Steam Deck Controller Forwarder App
A fullscreen app that forwards controller input to PC over network.
Launch from Steam, exit to stop forwarding.
"""

import os
import sys
import socket
import struct
import select
import threading
import time
from pathlib import Path

# Try to import pygame for GUI
try:
    import pygame
except ImportError:
    print("Error: pygame not installed")
    print("Install with: pip install pygame")
    sys.exit(1)

# Try to import evdev
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

# Colors
BG_COLOR = (20, 20, 30)
TEXT_COLOR = (220, 220, 220)
HIGHLIGHT_COLOR = (100, 150, 255)
SUCCESS_COLOR = (100, 255, 100)
WARNING_COLOR = (255, 200, 100)


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


def save_config(config):
    """Save configuration to file"""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            f.write(f"# Steam Deck Controller Forwarder Configuration\n")
            f.write(f"port={config['port']}\n")
    except Exception as e:
        print(f"Error saving config: {e}")


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
    """Find gamepad device with actual gamepad buttons (same logic as decktation)"""
    for path in list_devices():
        try:
            device = InputDevice(path)
            name_lower = device.name.lower()

            # Check if device has gamepad capabilities
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


class ControllerForwarder(threading.Thread):
    """Background thread that forwards controller events"""

    def __init__(self, controller, port, status_callback):
        super().__init__(daemon=True)
        self.controller = controller
        self.port = port
        self.status_callback = status_callback
        self.running = True
        self.client_ip = None
        self.event_count = 0

    def run(self):
        """Main forwarder loop"""
        try:
            # Grab controller for exclusive access
            self.controller.grab()
            self.status_callback("grabbed", True)

            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('0.0.0.0', self.port))
            sock.settimeout(0.1)

            self.status_callback("listening", self.port)

            while self.running:
                # Check for client registration
                try:
                    msg, addr = sock.recvfrom(1024)
                    if self.client_ip != addr[0]:
                        self.client_ip = addr[0]
                        self.status_callback("connected", addr[0])
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
                            if self.event_count % 100 == 0:
                                self.status_callback("events", self.event_count)

            sock.close()

        except Exception as e:
            self.status_callback("error", str(e))
        finally:
            try:
                self.controller.ungrab()
                self.status_callback("grabbed", False)
            except:
                pass

    def stop(self):
        """Stop the forwarder"""
        self.running = False


class ControllerApp:
    """Main application with GUI"""

    def __init__(self):
        self.config = load_config()
        self.running = True
        self.status_messages = []
        self.client_ip = None
        self.grabbed = False
        self.event_count = 0
        self.deck_ip = get_local_ip()
        self.forwarder = None

        # Initialize pygame
        pygame.init()

        # Get display info for proper fullscreen
        display_info = pygame.display.Info()
        self.screen = pygame.display.set_mode(
            (display_info.current_w, display_info.current_h),
            pygame.FULLSCREEN
        )
        pygame.display.set_caption("Steam Deck Controller Forwarder")

        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.header_font = pygame.font.Font(None, 48)
        self.normal_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)

        # Clock for FPS
        self.clock = pygame.time.Clock()

    def add_status(self, message):
        """Add a status message"""
        self.status_messages.append((time.time(), message))
        # Keep only last 10 messages
        if len(self.status_messages) > 10:
            self.status_messages.pop(0)

    def status_callback(self, event_type, data):
        """Callback from forwarder thread"""
        if event_type == "grabbed":
            self.grabbed = data
            if data:
                self.add_status("🔒 Controller grabbed (Deck controls disabled)")
        elif event_type == "listening":
            self.add_status(f"👂 Listening on port {data}")
        elif event_type == "connected":
            self.client_ip = data
            self.add_status(f"✓ PC client connected: {data}")
        elif event_type == "events":
            self.event_count = data
        elif event_type == "error":
            self.add_status(f"❌ Error: {data}")

    def start_forwarder(self):
        """Start the controller forwarder"""
        # Find controller
        self.add_status("🔍 Finding controller...")
        controller = find_steam_deck_controller()

        if not controller:
            self.add_status("❌ Controller not found!")
            return False

        self.add_status(f"✓ Found: {controller.name}")

        # Start forwarder thread
        self.forwarder = ControllerForwarder(
            controller,
            self.config['port'],
            self.status_callback
        )
        self.forwarder.start()

        return True

    def draw(self):
        """Draw the UI"""
        self.screen.fill(BG_COLOR)

        y = 50

        # Title
        title = self.title_font.render("🎮 Controller Forwarder", True, HIGHLIGHT_COLOR)
        title_rect = title.get_rect(centerx=self.screen.get_width() // 2, y=y)
        self.screen.blit(title, title_rect)
        y += 100

        # Connection status
        if self.client_ip:
            status_text = f"Connected to PC: {self.client_ip}"
            status_color = SUCCESS_COLOR
        elif self.grabbed:
            status_text = "Waiting for PC client..."
            status_color = WARNING_COLOR
        else:
            status_text = "Starting..."
            status_color = TEXT_COLOR

        status = self.header_font.render(status_text, True, status_color)
        status_rect = status.get_rect(centerx=self.screen.get_width() // 2, y=y)
        self.screen.blit(status, status_rect)
        y += 80

        # Deck IP
        deck_ip_text = self.normal_font.render(f"Steam Deck IP: {self.deck_ip}:{self.config['port']}", True, TEXT_COLOR)
        deck_ip_rect = deck_ip_text.get_rect(centerx=self.screen.get_width() // 2, y=y)
        self.screen.blit(deck_ip_text, deck_ip_rect)
        y += 60

        # Event counter
        if self.event_count > 0:
            events_text = self.normal_font.render(f"Events forwarded: {self.event_count}", True, TEXT_COLOR)
            events_rect = events_text.get_rect(centerx=self.screen.get_width() // 2, y=y)
            self.screen.blit(events_text, events_rect)
            y += 60

        # Instructions
        y += 40
        instructions = [
            "Press Steam Button → Quit to stop forwarding",
            "",
            f"PC client command:",
            f"  python3 pc_client.py {self.deck_ip} -p {self.config['port']}",
        ]

        for line in instructions:
            text = self.small_font.render(line, True, TEXT_COLOR)
            text_rect = text.get_rect(centerx=self.screen.get_width() // 2, y=y)
            self.screen.blit(text, text_rect)
            y += 35

        # Status messages at bottom
        y = self.screen.get_height() - 250
        status_header = self.normal_font.render("Status Log:", True, HIGHLIGHT_COLOR)
        self.screen.blit(status_header, (50, y))
        y += 40

        for timestamp, message in self.status_messages[-6:]:
            text = self.small_font.render(message, True, TEXT_COLOR)
            self.screen.blit(text, (50, y))
            y += 30

        pygame.display.flip()

    def run(self):
        """Main application loop"""
        # Start the forwarder
        if not self.start_forwarder():
            self.add_status("Failed to start. Exiting in 5 seconds...")
            self.draw()
            pygame.time.wait(5000)
            return

        # Main loop
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        self.running = False

            # Draw
            self.draw()

            # Cap at 30 FPS
            self.clock.tick(30)

        # Cleanup
        if self.forwarder:
            self.add_status("Stopping forwarder...")
            self.draw()
            self.forwarder.stop()
            self.forwarder.join(timeout=2)

        pygame.quit()


def main():
    """Entry point"""
    print("=" * 60)
    print("Steam Deck Controller Forwarder")
    print("=" * 60)

    app = ControllerApp()
    app.run()

    print("Exited cleanly")


if __name__ == '__main__':
    main()

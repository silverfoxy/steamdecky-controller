#!/usr/bin/python3
"""
Steamy Controller - Share your Steam Deck controller over the network
Modern touch-friendly Kivy GUI with beautiful design
"""

import os
import sys
from pathlib import Path

# Add lib directory to Python path for dependencies
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

os.environ['KIVY_NO_ARGS'] = '1'  # Prevent Kivy from reading command line args

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.modalview import ModalView
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty

import subprocess
import socket
import glob
import re
import logging
from pathlib import Path
from typing import Optional, List

# Configure logging
LOG_FILE = "/tmp/steamdecky-controller.log"
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class USBIPController:
    """Pure Python USB/IP controller management"""

    CONTROLLER_VID_PID = "28de:1205"  # Valve Steam Deck controller
    CONTROLLER_KEYWORDS = ["valve", "steam"]

    def __init__(self):
        self.usbip_path = self.find_usbip()
        self.usbipd_path = self.find_usbipd()
        self.current_busid: Optional[str] = None

    def find_usbip(self) -> Optional[str]:
        """Find usbip binary (Nix or system)"""
        candidates = [
            Path.home() / ".nix-profile/bin/usbip",
            "/usr/bin/usbip",
            "/usr/local/bin/usbip"
        ]

        for path in candidates:
            if path.exists():
                logger.info(f"Found usbip at: {path}")
                return str(path)

        logger.error("usbip not found! Install with: nix profile install nixpkgs#linuxPackages.usbip")
        return None

    def find_usbipd(self) -> Optional[str]:
        """Find usbipd binary"""
        if self.usbip_path:
            usbipd = Path(self.usbip_path).parent / "usbipd"
            if usbipd.exists():
                return str(usbipd)
        return None

    def clean_environment(self):
        """Remove Steam environment variables that interfere"""
        for var in ['LD_PRELOAD', 'LD_LIBRARY_PATH']:
            if var in os.environ:
                del os.environ[var]
                logger.debug(f"Removed {var} from environment")

    def load_kernel_modules(self) -> bool:
        """Load required kernel modules"""
        modules = ['usbip-core', 'usbip-host']

        for module in modules:
            try:
                logger.info(f"Loading kernel module: {module}")
                subprocess.run(['sudo', 'modprobe', module], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to load {module}: {e.stderr.decode()}")
                return False

        return True

    def find_controller(self) -> Optional[str]:
        """Find Steam Deck controller device and return busid"""
        if not self.usbip_path:
            return None

        try:
            logger.info("Searching for Steam Deck controller...")
            result = subprocess.run(
                [self.usbip_path, 'list', '-l'],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse output for controller
            for line in result.stdout.split('\n'):
                line_lower = line.lower()

                # Check for VID:PID or keywords
                if self.CONTROLLER_VID_PID in line_lower or \
                   any(keyword in line_lower for keyword in self.CONTROLLER_KEYWORDS):
                    logger.info(f"Found controller: {line.strip()}")

                    # Extract busid (format: "busid 3-3" or similar)
                    match = re.search(r'busid\s+(\d+-\d+)', line)
                    if match:
                        busid = match.group(1)
                        logger.info(f"Extracted busid: {busid}")
                        return busid

            logger.error("Steam Deck controller not found in USB devices")
            logger.debug(f"USB devices:\n{result.stdout}")
            return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list USB devices: {e.stderr}")
            return None

    def is_usbipd_running(self) -> bool:
        """Check if usbipd daemon is running"""
        try:
            result = subprocess.run(['pgrep', 'usbipd'], capture_output=True)
            return result.returncode == 0
        except Exception:
            return False

    def get_connected_clients(self) -> int:
        """Get number of connected USB/IP clients"""
        if not self.usbip_path:
            return 0

        try:
            result = subprocess.run(
                [self.usbip_path, 'port'],
                capture_output=True,
                text=True,
                timeout=2
            )
            # Count "Port" entries which indicate active connections
            port_count = result.stdout.count('Port ')
            return port_count
        except Exception as e:
            logger.debug(f"Failed to check connected clients: {e}")
            return 0

    def start_daemon(self) -> bool:
        """Start usbipd daemon"""
        if not self.usbipd_path:
            logger.error("usbipd not found")
            return False

        if self.is_usbipd_running():
            logger.info("usbipd already running")
            return True

        try:
            logger.info("Starting usbipd daemon...")
            subprocess.run(
                ['sudo', self.usbipd_path, '-D'],
                check=True,
                capture_output=True
            )
            logger.info("usbipd started successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start usbipd: {e.stderr.decode()}")
            return False

    def bind_device(self, busid: str) -> bool:
        """Bind device to usbip-host"""
        if not self.usbip_path:
            return False

        try:
            logger.info(f"Binding device {busid}...")
            subprocess.run(
                ['sudo', self.usbip_path, 'bind', '-b', busid],
                check=True,
                capture_output=True
            )
            self.current_busid = busid
            logger.info(f"Device {busid} bound successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to bind device: {e.stderr.decode()}")
            return False

    def start_sharing(self) -> tuple[bool, str]:
        """
        Start USB/IP sharing
        Returns: (success: bool, message: str)
        """
        self.clean_environment()

        # Load kernel modules
        if not self.load_kernel_modules():
            return False, "Failed to load kernel modules"

        # Find controller
        busid = self.find_controller()
        if not busid:
            return False, "Controller not found"

        # Start daemon
        if not self.start_daemon():
            return False, "Failed to start usbipd"

        # Bind device
        if not self.bind_device(busid):
            return False, "Failed to bind device"

        logger.info("=" * 50)
        logger.info("SUCCESS! Controller exported via USB/IP")
        logger.info(f"Busid: {busid}")
        logger.info("=" * 50)

        return True, busid

    def get_bound_devices(self) -> List[str]:
        """Get list of devices currently bound to usbip-host"""
        bound_devices = []
        try:
            driver_path = Path('/sys/bus/usb/drivers/usbip-host/')
            if driver_path.exists():
                for item in driver_path.iterdir():
                    if re.match(r'^\d+-\d+$', item.name):
                        bound_devices.append(item.name)
        except Exception as e:
            logger.error(f"Failed to get bound devices: {e}")

        return bound_devices

    def unbind_device(self, busid: str) -> bool:
        """Unbind device from usbip-host"""
        try:
            logger.info(f"Unbinding {busid} from usbip-host...")
            unbind_path = '/sys/bus/usb/drivers/usbip-host/unbind'

            # Use tee to write with sudo privileges
            subprocess.run(
                ['sudo', 'tee', unbind_path],
                input=busid,
                text=True,
                capture_output=True,
                check=True
            )

            # Rebind to original driver
            logger.info(f"Rebinding {busid} to system...")
            probe_path = '/sys/bus/usb/drivers_probe'
            subprocess.run(
                ['sudo', 'tee', probe_path],
                input=busid,
                text=True,
                capture_output=True,
                check=True
            )

            logger.info(f"Device {busid} restored")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to unbind device: {e}")
            return False

    def stop_daemon(self) -> bool:
        """Stop usbipd daemon"""
        try:
            logger.info("Stopping usbipd daemon...")
            subprocess.run(['sudo', 'killall', 'usbipd'], capture_output=True)
            logger.info("usbipd stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop usbipd: {e}")
            return False

    def stop_sharing(self) -> tuple[bool, str]:
        """
        Stop USB/IP sharing
        Returns: (success: bool, message: str)
        """
        logger.info("=" * 50)
        logger.info("Stopping USB/IP sharing...")
        logger.info("=" * 50)

        # Unbind all devices FIRST (before stopping daemon)
        bound_devices = self.get_bound_devices()

        if not bound_devices:
            logger.info("No devices currently bound")
        else:
            for busid in bound_devices:
                self.unbind_device(busid)

        # Now stop daemon
        self.stop_daemon()

        self.current_busid = None

        logger.info("=" * 50)
        logger.info("Controller restored to Deck")
        logger.info("=" * 50)

        return True, "Controller restored"


class BrightnessController:
    """Screen brightness management"""

    def __init__(self):
        self.backlight_path = self.find_backlight_device()
        self.original_brightness: Optional[int] = None
        self.is_dimmed = False
        self.is_off = False

    def find_backlight_device(self) -> Optional[Path]:
        """Find backlight device"""
        try:
            backlight_dirs = glob.glob('/sys/class/backlight/*')
            if backlight_dirs:
                path = Path(backlight_dirs[0])
                logger.info(f"Found backlight device: {path}")
                return path
        except Exception as e:
            logger.error(f"Failed to find backlight device: {e}")
        return None

    def get_brightness(self) -> Optional[int]:
        """Get current brightness"""
        if not self.backlight_path:
            return None
        try:
            with open(self.backlight_path / 'brightness', 'r') as f:
                return int(f.read().strip())
        except Exception as e:
            logger.error(f"Failed to read brightness: {e}")
            return None

    def get_max_brightness(self) -> Optional[int]:
        """Get maximum brightness"""
        if not self.backlight_path:
            return None
        try:
            with open(self.backlight_path / 'max_brightness', 'r') as f:
                return int(f.read().strip())
        except Exception as e:
            logger.error(f"Failed to read max brightness: {e}")
            return None

    def set_brightness(self, value: int) -> bool:
        """Set brightness value"""
        if not self.backlight_path:
            return False
        try:
            brightness_file = self.backlight_path / 'brightness'
            # Use tee to write with sudo privileges
            proc = subprocess.run(
                ['sudo', 'tee', str(brightness_file)],
                input=str(value),
                text=True,
                capture_output=True,
                check=True
            )
            logger.debug(f"Set brightness to {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to set brightness: {e}")
            return False

    def dim(self, percent: float = 0.10) -> bool:
        """Dim screen to specified percentage"""
        if self.is_dimmed:
            return True

        current = self.get_brightness()
        max_brightness = self.get_max_brightness()

        if current is not None and max_brightness is not None:
            self.original_brightness = current
            dim_value = max(1, int(max_brightness * percent))

            if self.set_brightness(dim_value):
                self.is_dimmed = True
                logger.info(f"Screen dimmed to {percent*100}%")
                return True

        return False

    def screen_off(self) -> bool:
        """Turn off screen completely"""
        if self.is_off:
            return True

        # Save current brightness if not already saved
        if self.original_brightness is None:
            current = self.get_brightness()
            if current is not None:
                self.original_brightness = current

        if self.set_brightness(0):
            self.is_off = True
            self.is_dimmed = False
            logger.info("Screen turned off")
            return True

        return False

    def restore(self) -> bool:
        """Restore original brightness"""
        if (not self.is_dimmed and not self.is_off) or self.original_brightness is None:
            return True

        if self.set_brightness(self.original_brightness):
            logger.info(f"Screen brightness restored to {self.original_brightness}")
            self.is_dimmed = False
            self.is_off = False
            self.original_brightness = None
            return True

        return False


class RoundedButton(Button):
    """Custom button with rounded corners"""
    bg_color = ListProperty([0.3, 0.3, 0.3, 1])

    def __init__(self, **kwargs):
        # Extract bg_color before passing to super
        if 'background_color' in kwargs:
            self.bg_color = kwargs.pop('background_color')
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.bind(pos=self.update_canvas, size=self.update_canvas,
                 disabled=self.update_canvas, bg_color=self.update_canvas)
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            alpha = 0.4 if self.disabled else 1.0
            Color(self.bg_color[0], self.bg_color[1], self.bg_color[2], alpha)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])


class Card(BoxLayout):
    """Card widget with semi-transparent rounded background"""
    bg_color = ListProperty([0.15, 0.15, 0.17, 0.85])  # Semi-transparent

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
            # Add subtle border
            Color(0.3, 0.3, 0.35, 0.6)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)], width=dp(1))


class ControllerApp(App):
    """Main Kivy Application"""

    def build(self):
        # Set fullscreen
        Window.fullscreen = 'auto'
        Window.clearcolor = (0.17, 0.17, 0.17, 1)  # Dark background

        # Controllers
        self.usbip = USBIPController()
        self.brightness = BrightnessController()

        # State
        self.sharing = False
        self.dim_timer = None
        self.screen_off_timer = None

        # Build UI
        return self.build_ui()

    def build_ui(self):
        """Build the main UI"""
        # Root container
        root = BoxLayout(orientation='vertical')

        # Load background image as texture from project directory
        from kivy.core.image import Image as CoreImage
        from pathlib import Path
        bg_path = Path(__file__).parent / 'background.webp'
        bg_texture = CoreImage(str(bg_path)).texture

        # Draw background on canvas
        with root.canvas.before:
            # Background image
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(texture=bg_texture, pos=(0, 0), size=Window.size)
            # Darker overlay to make background less visible
            Color(0, 0, 0, 0.60)
            self.overlay_rect = Rectangle(pos=(0, 0), size=Window.size)

        # Update background size on window resize
        def update_bg(*args):
            self.bg_rect.size = Window.size
            self.overlay_rect.size = Window.size
        Window.bind(size=update_bg)

        # Main content container with better spacing
        main = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(25))

        # Header (no background card)
        header = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100),
                          spacing=dp(5))

        icon = Label(text='~ STEAMY CONTROLLER ~', font_size=dp(44), bold=True,
                    size_hint_y=None, height=dp(60),
                    color=(0.91, 0.33, 0.13, 1))  # Yaru orange
        header.add_widget(icon)

        subtitle = Label(text='Share your controller wirelessly over the network',
                        font_size=dp(18), size_hint_y=None, height=dp(35),
                        text_size=(Window.width - dp(40), None), halign='center',
                        color=(1, 1, 1, 1))
        header.add_widget(subtitle)

        main.add_widget(header)

        # Separator line
        separator1 = Widget(size_hint_y=None, height=dp(2))
        with separator1.canvas:
            Color(0.91, 0.33, 0.13, 0.5)
            Rectangle(pos=(dp(20), 0), size=(Window.width - dp(40), dp(2)))
        main.add_widget(separator1)

        # Status (no background card, no icon - just text)
        status_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(70),
                              spacing=dp(5), padding=(dp(10), 0))

        # Status with colored text
        self.status_label = Label(text='STATUS: Ready', font_size=dp(32), bold=True, halign='left',
                                 size_hint_y=None, height=dp(42),
                                 color=(0.91, 0.33, 0.13, 1))  # Orange
        self.status_label.bind(size=self.status_label.setter('text_size'))
        status_box.add_widget(self.status_label)

        self.ip_label = Label(text=f'Deck IP: {self.get_local_ip()}',
                             font_size=dp(20), halign='left',
                             size_hint_y=None, height=dp(28),
                             color=(0.85, 0.85, 0.85, 1))
        self.ip_label.bind(size=self.ip_label.setter('text_size'))
        status_box.add_widget(self.ip_label)

        main.add_widget(status_box)

        # Instructions (no background card)
        self.instructions = Label(text='', font_size=dp(18),
                                 size_hint_y=None, height=dp(140),
                                 text_size=(Window.width - dp(50), None), valign='top',
                                 halign='left', padding=(dp(10), dp(10)),
                                 color=(1, 1, 1, 1))
        main.add_widget(self.instructions)

        # Spacer
        main.add_widget(Widget())

        # Buttons with rounded style and bright colors
        self.start_btn = RoundedButton(text='START SHARING', font_size=dp(24), bold=True,
                                      size_hint_y=None, height=dp(70),
                                      bg_color=(0.15, 0.64, 0.41, 1))
        self.start_btn.bind(on_press=self.start_sharing)
        main.add_widget(self.start_btn)

        self.stop_btn = RoundedButton(text='STOP SHARING', font_size=dp(24), bold=True,
                                     size_hint_y=None, height=dp(70),
                                     bg_color=(0.75, 0.11, 0.16, 1), disabled=True)
        self.stop_btn.bind(on_press=self.stop_sharing)
        main.add_widget(self.stop_btn)

        # Bottom buttons with better contrast
        bottom = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))

        log_btn = RoundedButton(text='VIEW LOG', font_size=dp(18),
                               bg_color=(0.40, 0.40, 0.45, 1))
        log_btn.bind(on_press=self.view_log)
        bottom.add_widget(log_btn)

        exit_btn = RoundedButton(text='EXIT', font_size=dp(18),
                                bg_color=(0.40, 0.40, 0.45, 1))
        exit_btn.bind(on_press=self.exit_app)
        bottom.add_widget(exit_btn)

        main.add_widget(bottom)

        root.add_widget(main)

        # Bind touch event
        Window.bind(on_touch_down=self.on_screen_tap)

        # Start status checker
        Clock.schedule_interval(self.check_status, 2)

        return root

    def get_local_ip(self) -> str:
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

    def start_sharing(self, instance):
        """Start USB/IP sharing"""
        if self.sharing:
            return

        logger.info("Starting controller sharing...")
        self.status_label.text = "STATUS: Starting..."
        self.start_btn.disabled = True

        # Run in thread to prevent UI freeze
        Clock.schedule_once(lambda dt: self._do_start_sharing(), 0.1)

    def _do_start_sharing(self):
        """Actually perform the start operation"""
        success, result = self.usbip.start_sharing()

        if success:
            self.sharing = True
            self.status_label.text = "STATUS: Sharing Active"
            self.status_label.color = (0.15, 0.64, 0.41, 1)  # Green

            deck_ip = self.get_local_ip()
            instructions = (
                f"On your PC, run:\n\n"
                f"  cd pc-scripts\n"
                f"  ./pc-connect.sh {deck_ip}\n\n"
                f"Or manually:\n"
                f"  sudo usbip attach -r {deck_ip} -b {result}\n\n"
                f"Use touchscreen to stop (buttons won't work!)\n"
                f"Screen will dim in 10 seconds (tap to wake)..."
            )
            self.instructions.text = instructions

            self.start_btn.disabled = True
            self.stop_btn.disabled = False

            # Dim screen after 10 seconds, then turn off after 60 seconds
            if self.dim_timer:
                self.dim_timer.cancel()
            self.dim_timer = Clock.schedule_once(lambda dt: self._dim_then_schedule_off(), 10)
        else:
            self.status_label.text = "STATUS: Failed to Start"
            self.status_label.color = (0.75, 0.11, 0.16, 1)  # Red
            self.instructions.text = f"Error: {result}\n\nCheck log for details."
            self.start_btn.disabled = False

    def _dim_then_schedule_off(self):
        """Dim screen and schedule screen off after 1 minute"""
        if self.sharing:
            self.brightness.dim()
            # Schedule screen off after 60 seconds
            if self.screen_off_timer:
                self.screen_off_timer.cancel()
            self.screen_off_timer = Clock.schedule_once(lambda dt: self._turn_screen_off(), 60)

    def _turn_screen_off(self):
        """Turn screen off completely"""
        if self.sharing:
            self.brightness.screen_off()

    def stop_sharing(self, instance):
        """Stop USB/IP sharing"""
        if not self.sharing:
            return

        logger.info("Stopping controller sharing...")
        self.status_label.text = "STATUS: Stopping..."
        self.stop_btn.disabled = True

        Clock.schedule_once(lambda dt: self._do_stop_sharing(), 0.1)

    def _do_stop_sharing(self):
        """Actually perform the stop operation"""
        success, message = self.usbip.stop_sharing()

        self.sharing = False
        self.status_label.text = "STATUS: Ready"
        self.status_label.color = (0.91, 0.33, 0.13, 1)  # Orange
        self.instructions.text = ""

        self.start_btn.disabled = False
        self.stop_btn.disabled = True

        # Restore brightness and cancel timers
        self.brightness.restore()
        if self.dim_timer:
            self.dim_timer.cancel()
            self.dim_timer = None
        if self.screen_off_timer:
            self.screen_off_timer.cancel()
            self.screen_off_timer = None

    def on_screen_tap(self, window, touch):
        """Handle screen tap - wake if dimmed or off"""
        if (self.brightness.is_dimmed or self.brightness.is_off) and self.sharing:
            self.brightness.restore()

            # Cancel existing timers
            if self.dim_timer:
                self.dim_timer.cancel()
            if self.screen_off_timer:
                self.screen_off_timer.cancel()

            # Re-dim after 10 seconds, then screen off after 1 minute
            self.dim_timer = Clock.schedule_once(lambda dt: self._dim_then_schedule_off(), 10)

    def check_status(self, dt):
        """Periodically check USB/IP status and connected clients"""
        if self.sharing:
            # Check if PC is connected
            connected_clients = self.usbip.get_connected_clients()
            if connected_clients > 0:
                self.status_label.text = f"STATUS: PC Connected ({connected_clients})"
                self.status_label.color = (0.15, 0.64, 0.41, 1)  # Green
            else:
                self.status_label.text = "STATUS: Waiting for PC..."
                self.status_label.color = (0.91, 0.33, 0.13, 1)  # Orange
        elif self.usbip.is_usbipd_running():
            self.status_label.text = "STATUS: WARNING - USB/IP active"
            self.status_label.color = (0.91, 0.33, 0.13, 1)  # Orange

    def view_log(self, instance):
        """Open log file in popup with scrollbar"""
        popup = ModalView(size_hint=(0.9, 0.9))

        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        title = Label(text='Application Log', font_size=dp(28), bold=True,
                     size_hint_y=None, height=dp(50))
        layout.add_widget(title)

        # Log content with scrollbar
        scroll = ScrollView(size_hint=(1, 1), bar_width=dp(15), bar_color=(0.91, 0.33, 0.13, 1))
        log_text = TextInput(readonly=True, font_size=dp(14), size_hint_y=None)
        log_text.bind(minimum_height=log_text.setter('height'))

        try:
            with open(LOG_FILE, 'r') as f:
                log_text.text = f.read()
        except Exception as e:
            log_text.text = f"Error loading log file: {e}"

        scroll.add_widget(log_text)
        layout.add_widget(scroll)

        close_btn = RoundedButton(text='CLOSE', font_size=dp(22), size_hint_y=None, height=dp(70),
                                 bg_color=(0.91, 0.33, 0.13, 1))
        close_btn.bind(on_press=popup.dismiss)
        layout.add_widget(close_btn)

        popup.add_widget(layout)
        popup.open()

    def exit_app(self, instance):
        """Exit application"""
        logger.info("Exiting application...")

        if self.sharing:
            self.usbip.stop_sharing()

        # Force brightness restore
        if self.brightness.original_brightness:
            self.brightness.set_brightness(self.brightness.original_brightness)
        self.brightness.is_dimmed = False
        self.brightness.is_off = False

        self.stop()


def main():
    """Main entry point"""
    logger.info("=" * 50)
    logger.info("Steamy Controller - Starting")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 50)

    ControllerApp().run()

    logger.info("Application closed")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Steam Deck Controller Sharing App
Touch-friendly GUI for enabling/disabling controller sharing
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import socket
import threading
import time

class ControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam Deck Controller Sharing")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#1b2838')  # Steam blue-gray

        self.mode = "evdev"  # or "usbip"
        self.is_active = False
        self.test_mode = False  # Local loopback testing
        self.status_text = "Ready"
        self.deck_ip = self.get_local_ip()
        self.busid = ""

        self.setup_ui()
        self.update_status()

    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "unknown"

    def setup_ui(self):
        """Create the touch-friendly UI"""

        # Title
        title = tk.Label(
            self.root,
            text="Steam Deck Controller Sharing",
            font=("Arial", 32, "bold"),
            bg='#1b2838',
            fg='white'
        )
        title.pack(pady=30)

        # Status frame
        status_frame = tk.Frame(self.root, bg='#1b2838')
        status_frame.pack(pady=20)

        self.status_label = tk.Label(
            status_frame,
            text="Status: Ready",
            font=("Arial", 24),
            bg='#1b2838',
            fg='#66c0f4'  # Steam blue
        )
        self.status_label.pack()

        # Mode selector
        mode_frame = tk.Frame(self.root, bg='#1b2838')
        mode_frame.pack(pady=20)

        tk.Label(
            mode_frame,
            text="Mode:",
            font=("Arial", 20),
            bg='#1b2838',
            fg='white'
        ).pack(side=tk.LEFT, padx=10)

        self.mode_var = tk.StringVar(value="Network (evdev)")
        self.mode_button = tk.Button(
            mode_frame,
            textvariable=self.mode_var,
            font=("Arial", 18),
            bg='#2a475e',
            fg='white',
            activebackground='#66c0f4',
            width=20,
            height=2,
            command=self.toggle_mode
        )
        self.mode_button.pack(side=tk.LEFT, padx=10)

        # Info display
        self.info_frame = tk.Frame(self.root, bg='#1b2838')
        self.info_frame.pack(pady=20)

        self.ip_label = tk.Label(
            self.info_frame,
            text=f"Deck IP: {self.deck_ip}",
            font=("Arial", 18),
            bg='#1b2838',
            fg='#c7d5e0'
        )
        self.ip_label.pack()

        self.busid_label = tk.Label(
            self.info_frame,
            text="",
            font=("Arial", 18),
            bg='#1b2838',
            fg='#c7d5e0'
        )
        self.busid_label.pack()

        self.instructions_label = tk.Label(
            self.info_frame,
            text="",
            font=("Arial", 14),
            bg='#1b2838',
            fg='#8f98a0',
            wraplength=600,
            justify=tk.LEFT
        )
        self.instructions_label.pack(pady=10)

        # Main action button
        self.action_button = tk.Button(
            self.root,
            text="START SHARING",
            font=("Arial", 28, "bold"),
            bg='#5c7e10',  # Steam green
            fg='white',
            activebackground='#a4d007',
            width=20,
            height=3,
            command=self.toggle_sharing
        )
        self.action_button.pack(pady=30)

        # Test mode button (local loopback)
        self.test_button = tk.Button(
            self.root,
            text="TEST MODE (Local Loopback)",
            font=("Arial", 18),
            bg='#2a475e',
            fg='white',
            activebackground='#66c0f4',
            width=25,
            height=2,
            command=self.toggle_test_mode
        )
        self.test_button.pack(pady=10)

        # Exit button
        exit_button = tk.Button(
            self.root,
            text="Exit",
            font=("Arial", 16),
            bg='#c5391c',  # Red
            fg='white',
            activebackground='#ee5a3c',
            width=10,
            height=2,
            command=self.root.quit
        )
        exit_button.pack(pady=20)

    def toggle_mode(self):
        """Switch between evdev and USB/IP modes"""
        if self.is_active:
            return  # Can't change mode while active

        if self.mode == "evdev":
            self.mode = "usbip"
            self.mode_var.set("USB/IP (Full)")
            self.instructions_label.config(
                text="USB/IP mode: Full controller with trackpads!\n"
                     "Controller will be unavailable on Deck.\n"
                     "On PC: sudo usbip attach -r <ip> -b <busid>"
            )
        else:
            self.mode = "evdev"
            self.mode_var.set("Network (evdev)")
            self.instructions_label.config(text="Network mode: Gamepad only (no trackpad)")

    def toggle_test_mode(self):
        """Toggle local loopback test mode"""
        if self.is_active:
            return  # Already running

        self.test_mode = not self.test_mode
        if self.test_mode:
            self.mode = "usbip"  # Test mode requires USB/IP
            self.mode_var.set("USB/IP (Test)")
            self.test_button.config(bg='#5c7e10', text="TEST MODE ENABLED")
            self.mode_button.config(state='disabled')
            self.instructions_label.config(
                text="Test Mode: Controller will be exported and re-imported locally.\n"
                     "No PC needed - tests USB/IP setup on Deck only!"
            )
        else:
            self.test_button.config(bg='#2a475e', text="TEST MODE (Local Loopback)")
            self.mode_button.config(state='normal')
            self.mode_var.set("USB/IP (Full)")
            self.instructions_label.config(text="")

    def toggle_sharing(self):
        """Start or stop sharing"""
        if self.is_active:
            self.stop_sharing()
        else:
            self.start_sharing()

    def start_sharing(self):
        """Start sharing in selected mode"""
        self.status_label.config(text="Status: Starting...", fg='yellow')
        self.action_button.config(state='disabled')

        # Run in thread to not block UI
        thread = threading.Thread(target=self._start_sharing_thread)
        thread.daemon = True
        thread.start()

    def _start_sharing_thread(self):
        """Background thread for starting sharing"""
        try:
            if self.mode == "usbip":
                # Start USB/IP
                result = subprocess.run(
                    ["/bin/bash", "-c", """
                        # Find controller
                        DEVICE_INFO=$(lsusb | grep -i "valve\\|steam" | head -1)
                        if [ -z "$DEVICE_INFO" ]; then
                            echo "ERROR: Controller not found"
                            exit 1
                        fi

                        # Extract busid
                        BUS_ID=$(echo "$DEVICE_INFO" | awk '{print $2}' | sed 's/^0*//')
                        DEV_ID=$(echo "$DEVICE_INFO" | awk '{print $4}' | sed 's/://g' | sed 's/^0*//')
                        BUSID="${BUS_ID}-${DEV_ID}"

                        # Load and start
                        sudo modprobe usbip-core 2>/dev/null
                        sudo modprobe usbip-host 2>/dev/null
                        sudo killall usbipd 2>/dev/null
                        sudo usbipd -D
                        sleep 0.5

                        # Bind
                        sudo usbip bind -b "$BUSID" 2>&1
                        echo "$BUSID"
                    """],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    self.busid = result.stdout.strip().split('\n')[-1]

                    # If test mode, also attach locally
                    if self.test_mode:
                        time.sleep(1)  # Wait for usbipd to fully start
                        attach_result = subprocess.run(
                            ["sudo", "usbip", "attach", "-r", "127.0.0.1", "-b", self.busid],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if attach_result.returncode != 0:
                            self.root.after(0, self.update_ui_error, "Failed to attach in test mode")
                            return

                    self.is_active = True
                    self.root.after(0, self.update_ui_active)
                else:
                    self.root.after(0, self.update_ui_error, "Failed to start USB/IP")
            else:
                # Start evdev forwarder
                # TODO: Implement evdev mode startup
                self.root.after(0, self.update_ui_error, "Evdev mode not yet implemented in app")

        except Exception as e:
            self.root.after(0, self.update_ui_error, str(e))

    def stop_sharing(self):
        """Stop sharing"""
        self.status_label.config(text="Status: Stopping...", fg='yellow')
        self.action_button.config(state='disabled')

        thread = threading.Thread(target=self._stop_sharing_thread)
        thread.daemon = True
        thread.start()

    def _stop_sharing_thread(self):
        """Background thread for stopping sharing"""
        try:
            if self.mode == "usbip":
                # If test mode, detach first
                if self.test_mode:
                    subprocess.run(
                        ["sudo", "usbip", "detach", "-p", "0"],
                        capture_output=True,
                        timeout=10
                    )
                    time.sleep(0.5)

                # Unbind and stop
                subprocess.run(
                    ["/bin/bash", "-c", """
                        sudo usbip list -l 2>/dev/null | grep "busid" | awk '{print $2}' | while read BUSID; do
                            sudo usbip unbind -b "$BUSID" 2>&1
                        done
                        sudo killall usbipd 2>/dev/null
                    """],
                    timeout=10
                )

            self.is_active = False
            self.busid = ""
            self.root.after(0, self.update_ui_inactive)

        except Exception as e:
            self.root.after(0, self.update_ui_error, str(e))

    def update_ui_active(self):
        """Update UI for active state"""
        if self.test_mode:
            self.status_label.config(text="Status: TEST MODE ACTIVE", fg='#a4d007')
        else:
            self.status_label.config(text="Status: ACTIVE", fg='#a4d007')

        self.action_button.config(
            text="STOP SHARING",
            bg='#c5391c',
            activebackground='#ee5a3c',
            state='normal'
        )
        self.mode_button.config(state='disabled')
        self.test_button.config(state='disabled')

        if self.mode == "usbip":
            self.busid_label.config(text=f"Bus ID: {self.busid}")
            if self.test_mode:
                self.instructions_label.config(
                    text=f"✓ Test mode running!\n"
                         f"Controller exported at {self.deck_ip}:{self.busid}\n"
                         f"and re-imported locally via loopback.\n"
                         f"Check if Steam Input still works!"
                )
            else:
                self.instructions_label.config(
                    text=f"On PC run:\nsudo usbip attach -r {self.deck_ip} -b {self.busid}"
                )

    def update_ui_inactive(self):
        """Update UI for inactive state"""
        self.status_label.config(text="Status: Ready", fg='#66c0f4')
        self.action_button.config(
            text="START SHARING",
            bg='#5c7e10',
            activebackground='#a4d007',
            state='normal'
        )
        self.mode_button.config(state='normal' if not self.test_mode else 'disabled')
        self.test_button.config(state='normal')
        self.busid_label.config(text="")

    def update_ui_error(self, error):
        """Update UI for error state"""
        self.status_label.config(text=f"Error: {error}", fg='#ee5a3c')
        self.action_button.config(state='normal')
        self.mode_button.config(state='normal')

    def update_status(self):
        """Periodic status update"""
        # Could check actual status here
        self.root.after(2000, self.update_status)

if __name__ == "__main__":
    root = tk.Tk()
    app = ControllerApp(root)
    root.mainloop()

#!/usr/bin/env python3
"""
Steam Deck Controller USB/IP - Touchscreen GUI
Big buttons for when controller is disabled
"""

import tkinter as tk
from tkinter import font as tkfont
import subprocess
import socket
import os
from pathlib import Path

# Get script directory
SCRIPT_DIR = Path(__file__).parent
START_SCRIPT = SCRIPT_DIR / "deck-start-usbip.sh"
STOP_SCRIPT = SCRIPT_DIR / "deck-stop-usbip.sh"

class ControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam Deck Controller Share")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#1b2838')  # Steam dark blue

        self.sharing = False
        self.process = None

        # Big fonts for touchscreen
        self.title_font = tkfont.Font(family="Arial", size=32, weight="bold")
        self.button_font = tkfont.Font(family="Arial", size=28, weight="bold")
        self.status_font = tkfont.Font(family="Arial", size=20)

        self.setup_ui()
        self.update_status()

    def setup_ui(self):
        # Header with gradient effect (simulated with frames)
        header = tk.Frame(self.root, bg='#171a21', height=120)
        header.pack(fill='x')
        header.pack_propagate(False)

        # Title with glow effect (using multiple labels)
        title_frame = tk.Frame(header, bg='#171a21')
        title_frame.place(relx=0.5, rely=0.5, anchor='center')

        title = tk.Label(
            title_frame,
            text="🎮 Controller Share",
            font=self.title_font,
            bg='#171a21',
            fg='#66c0f4'
        )
        title.pack()

        subtitle = tk.Label(
            title_frame,
            text="Share your Steam Deck controller over USB/IP",
            font=tkfont.Font(family="Arial", size=14),
            bg='#171a21',
            fg='#8f98a0'
        )
        subtitle.pack()

        # Status card with border
        status_card = tk.Frame(self.root, bg='#212b36', relief='raised', bd=2)
        status_card.pack(pady=20, padx=40, fill='x')

        # Status indicator
        status_inner = tk.Frame(status_card, bg='#212b36')
        status_inner.pack(pady=15, padx=15)

        self.status_indicator = tk.Label(
            status_inner,
            text="●",
            font=tkfont.Font(family="Arial", size=40),
            bg='#212b36',
            fg='#66c0f4'  # Blue (ready state)
        )
        self.status_indicator.pack(side='left', padx=10)

        status_text_frame = tk.Frame(status_inner, bg='#212b36')
        status_text_frame.pack(side='left', fill='both', expand=True)

        self.status_label = tk.Label(
            status_text_frame,
            text="Ready",
            font=tkfont.Font(family="Arial", size=24, weight="bold"),
            bg='#212b36',
            fg='white'
        )
        self.status_label.pack(anchor='w')

        # IP Address label
        self.ip_label = tk.Label(
            status_text_frame,
            text=f"Deck IP: {self.get_local_ip()}",
            font=tkfont.Font(family="Arial", size=16),
            bg='#212b36',
            fg='#8f98a0'
        )
        self.ip_label.pack(anchor='w')

        # Instructions label (fixed height so it doesn't push buttons off screen)
        instructions_frame = tk.Frame(self.root, bg='#1b2838', height=150)
        instructions_frame.pack(pady=10, fill='x')
        instructions_frame.pack_propagate(False)  # Don't resize based on content

        self.instructions = tk.Label(
            instructions_frame,
            text="",
            font=tkfont.Font(family="Arial", size=14),
            bg='#1b2838',
            fg='#8f98a0',
            justify='left',
            wraplength=700
        )
        self.instructions.pack()

        # Button frame
        button_frame = tk.Frame(self.root, bg='#1b2838')
        button_frame.pack(expand=True)

        # Start button (BIG for touchscreen) with modern styling
        self.start_btn = tk.Button(
            button_frame,
            text="▶  START SHARING",
            font=self.button_font,
            bg='#5c7e10',  # Steam green
            fg='white',
            activebackground='#7ba31a',
            activeforeground='white',
            command=self.start_sharing,
            width=22,
            height=3,
            relief='flat',
            bd=0,
            cursor='hand2',
            highlightthickness=0
        )
        self.start_btn.pack(pady=15)
        # Bind hover effects
        self.start_btn.bind('<Enter>', lambda e: self.start_btn.config(bg='#6ea113'))
        self.start_btn.bind('<Leave>', lambda e: self.start_btn.config(bg='#5c7e10'))

        # Stop button (BIG for touchscreen) with modern styling
        self.stop_btn = tk.Button(
            button_frame,
            text="⏹  STOP SHARING",
            font=self.button_font,
            bg='#a94442',  # Darker red
            fg='white',
            activebackground='#c9302c',
            activeforeground='white',
            command=self.stop_sharing,
            width=22,
            height=3,
            relief='flat',
            bd=0,
            cursor='hand2',
            state='disabled',
            highlightthickness=0
        )
        self.stop_btn.pack(pady=15)
        # Bind hover effects
        self.stop_btn.bind('<Enter>', lambda e: self.stop_btn.config(bg='#c9302c') if self.stop_btn['state'] == 'normal' else None)
        self.stop_btn.bind('<Leave>', lambda e: self.stop_btn.config(bg='#a94442') if self.stop_btn['state'] == 'normal' else None)

        # Bottom buttons frame
        bottom_frame = tk.Frame(self.root, bg='#1b2838')
        bottom_frame.pack(side='bottom', pady=25)

        # View Log button with better styling
        log_btn = tk.Button(
            bottom_frame,
            text="📄 View Log",
            font=tkfont.Font(family="Arial", size=16),
            bg='#2a475e',
            fg='#c7d5e0',
            activebackground='#3d5a71',
            activeforeground='white',
            command=self.view_log,
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        log_btn.pack(side='left', padx=10)
        log_btn.bind('<Enter>', lambda e: log_btn.config(bg='#3d5a71'))
        log_btn.bind('<Leave>', lambda e: log_btn.config(bg='#2a475e'))

        # Exit button with better styling
        exit_btn = tk.Button(
            bottom_frame,
            text="✕ Exit",
            font=tkfont.Font(family="Arial", size=16),
            bg='#2a475e',
            fg='#c7d5e0',
            activebackground='#3d5a71',
            activeforeground='white',
            command=self.exit_app,
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        exit_btn.pack(side='left', padx=10)
        exit_btn.bind('<Enter>', lambda e: exit_btn.config(bg='#3d5a71'))
        exit_btn.bind('<Leave>', lambda e: exit_btn.config(bg='#2a475e'))

        # Bind escape key
        self.root.bind('<Escape>', lambda e: self.exit_app())

    def get_local_ip(self):
        """Get Deck's local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "unknown"

    def start_sharing(self):
        """Start USB/IP sharing"""
        if self.sharing:
            return

        self.status_indicator.config(fg='#f0ad4e')  # Orange
        self.status_label.config(text="Starting...", fg='white')
        self.start_btn.config(state='disabled')
        self.root.update()

        try:
            # Run start script silently in background
            self.process = subprocess.Popen(
                [str(START_SCRIPT)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Check if it actually started successfully
            self.root.after(3000, self.check_if_started)

        except Exception as e:
            self.status_label.config(
                text=f"❌ Error: {str(e)[:50]}",
                fg='#cd5c5c'
            )
            self.start_btn.config(state='normal')

    def check_if_started(self):
        """Check if usbipd actually started"""
        try:
            result = subprocess.run(
                ['pgrep', 'usbipd'],
                capture_output=True
            )

            if result.returncode == 0:
                # Success! usbipd is running
                self.finish_start()
            else:
                # Failed to start - read last lines from log
                try:
                    with open('/tmp/steamdecky-controller.log', 'r') as f:
                        lines = f.readlines()
                        last_lines = ''.join(lines[-10:])  # Last 10 lines
                except:
                    last_lines = "Could not read log"

                self.status_indicator.config(fg='#cd5c5c')  # Red
                self.status_label.config(
                    text="Failed to Start",
                    fg='white'
                )
                self.start_btn.config(state='normal')

                self.instructions.config(
                    text=f"Check log: /tmp/steamdecky-controller.log\n\n"
                         f"Last lines:\n{last_lines[-200:]}"
                )
        except:
            # Can't check, assume failed
            self.start_btn.config(state='normal')

    def finish_start(self):
        """Update UI after starting"""
        self.sharing = True
        self.status_indicator.config(fg='#5c7e10')  # Green
        self.status_label.config(
            text="Sharing Active",
            fg='white'
        )

        deck_ip = self.get_local_ip()
        self.instructions.config(
            text=f"On your PC, run:\n\n"
                 f"  cd pc-scripts\n"
                 f"  ./pc-connect.sh {deck_ip}\n\n"
                 f"Use touchscreen to stop (buttons won't work!)"
        )

        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

    def stop_sharing(self):
        """Stop USB/IP sharing"""
        if not self.sharing:
            return

        self.status_indicator.config(fg='#f0ad4e')  # Orange
        self.status_label.config(text="Stopping...", fg='white')
        self.stop_btn.config(state='disabled')
        self.root.update()

        try:
            # Kill the start script process if it's still running
            if self.process:
                try:
                    self.process.terminate()
                except:
                    pass

            # Run stop script silently
            subprocess.Popen(
                [str(STOP_SCRIPT)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Give it a moment then check if stopped
            self.root.after(2000, self.check_if_stopped)

        except Exception as e:
            self.status_label.config(
                text=f"❌ Error: {str(e)[:50]}",
                fg='#cd5c5c'
            )
            self.stop_btn.config(state='normal')

    def check_if_stopped(self):
        """Check if usbipd actually stopped"""
        try:
            result = subprocess.run(
                ['pgrep', 'usbipd'],
                capture_output=True
            )

            if result.returncode != 0:
                # Success! usbipd is not running
                self.sharing = False
                self.status_indicator.config(fg='#66c0f4')  # Blue (ready)
                self.status_label.config(
                    text="Ready",
                    fg='white'
                )
                self.instructions.config(text="")
                self.start_btn.config(state='normal')
                self.stop_btn.config(state='disabled')
            else:
                # Still running - check terminal for issues
                self.status_indicator.config(fg='#f0ad4e')  # Orange warning
                self.status_label.config(
                    text="Still Running - Check Log",
                    fg='white'
                )
                self.stop_btn.config(state='normal')
        except:
            # Can't check, assume stopped
            self.sharing = False
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')

    def update_status(self):
        """Check if usbipd is running"""
        try:
            result = subprocess.run(
                ['pgrep', 'usbipd'],
                capture_output=True
            )
            if result.returncode == 0 and not self.sharing:
                # usbipd is running but we didn't start it
                self.status_label.config(
                    text="⚠ USB/IP may be active (started elsewhere)",
                    fg='#f0ad4e'
                )
        except:
            pass

        # Check again in 2 seconds
        self.root.after(2000, self.update_status)

    def view_log(self):
        """Open log file in text editor"""
        subprocess.Popen(['kate', '/tmp/steamdecky-controller.log'])

    def exit_app(self):
        """Exit the application"""
        if self.sharing:
            # Auto-stop if still sharing
            self.stop_sharing()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ControllerApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()

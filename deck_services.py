"""Lifecycle helpers for USB/IP discovery and idle-sleep prevention on Deck."""

import logging
import os
import re
import shutil
from pathlib import Path
import socket
import subprocess
import time

logger = logging.getLogger(__name__)


def parse_controller_busid(line):
    """Return the full USB/IP port path for the Valve controller on this line."""
    if '28de:1205' not in line.lower():
        return None
    match = re.search(r'\bbusid\s+(\d+-\d+(?:\.\d+)*)\b', line, re.IGNORECASE)
    return match.group(1) if match else None


class DiscoveryAdvertiser:
    """Publish the export only while the controller is shared."""

    def __init__(self):
        self.process = None

    def start(self, busid):
        if self.process and self.process.poll() is None:
            return True
        self.process = None
        publisher = shutil.which('avahi-publish-service')
        if not publisher:
            nix_publisher = Path.home() / '.nix-profile/bin/avahi-publish-service'
            if nix_publisher.is_file() and os.access(nix_publisher, os.X_OK):
                publisher = str(nix_publisher)
        if not publisher:
            logger.warning('Avahi publisher unavailable; use the Deck IP on the client')
            return False
        try:
            self.process = subprocess.Popen(
                [publisher, f'Steamy Controller ({socket.gethostname()})',
                 '_steamy-controller._tcp', '3240', f'busid={busid}',
                 'vidpid=28de:1205'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.05)
            if self.process.poll() is not None:
                logger.warning('Avahi service registration failed; use the Deck IP')
                self.process = None
                return False
            return True
        except OSError as exc:
            logger.warning('Avahi publisher failed: %s', exc)
            self.process = None
            return False

    def ensure_active(self, busid):
        return self.start(busid)

    def stop(self):
        process, self.process = self.process, None
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


class SleepInhibitor:
    """Keep the Deck awake for as long as controller sharing is active."""

    def __init__(self):
        self.process = None

    def start(self):
        if self.process and self.process.poll() is None:
            return True
        self.process = None
        systemd_inhibit = shutil.which('systemd-inhibit')
        sleep = shutil.which('sleep')
        if not systemd_inhibit or not sleep:
            logger.warning('systemd-inhibit unavailable; Deck may sleep while sharing')
            return False
        try:
            self.process = subprocess.Popen(
                [systemd_inhibit, '--what=idle:sleep', '--mode=block',
                 '--no-ask-password', '--who=Steamy Controller',
                 '--why=Controller is being shared over USB/IP', '--', sleep, 'infinity'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.05)
            if self.process.poll() is not None:
                logger.warning('systemd-inhibit exited before acquiring the sleep lock')
                self.process = None
                return False
            return True
        except OSError as exc:
            logger.warning('Could not inhibit sleep: %s', exc)
            self.process = None
            return False

    def ensure_active(self):
        """Reacquire if the inhibitor died while the PC was connected."""
        return self.start()

    def stop(self):
        process, self.process = self.process, None
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

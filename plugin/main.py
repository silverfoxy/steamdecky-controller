import asyncio
import os
import socket
import subprocess
import sys
import decky_plugin

logger = decky_plugin.logger

# Plugin directory
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

# Add bundled dependencies to Python path
LIB_PATH = os.path.join(PLUGIN_DIR, "lib")
if os.path.exists(LIB_PATH):
    sys.path.insert(0, LIB_PATH)
    logger.info(f"Added bundled lib path: {LIB_PATH}")
else:
    logger.warning(f"Bundled lib path does not exist: {LIB_PATH}")
FORWARDER_SCRIPT = os.path.join(PLUGIN_DIR, "controller_forwarder.py")

# Default port for controller events
DEFAULT_PORT = 9090


def _local_ip() -> str:
    """Get the local IP address of the Steam Deck"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def _check_evdev() -> bool:
    """Check if python-evdev is available"""
    try:
        logger.info(f"Attempting to import evdev. sys.path: {sys.path[:3]}...")
        import evdev
        logger.info(f"✓ evdev imported successfully. Version: {evdev.__version__ if hasattr(evdev, '__version__') else 'unknown'}")
        logger.info(f"evdev location: {evdev.__file__ if hasattr(evdev, '__file__') else 'unknown'}")
        return True
    except ImportError as e:
        logger.error(f"✗ evdev ImportError: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error checking evdev: {e}", exc_info=True)
        return False


class Plugin:
    _forwarder_proc: subprocess.Popen | None = None
    _port: int = DEFAULT_PORT
    _cached_deck_ip: str | None = None
    _deps_checked: dict | None = None

    # ── public API (called from frontend) ────────────────────────────────────

    async def check_deps(self) -> dict:
        """Check if evdev is available (cached after first call)"""
        logger.info("=== check_deps called ===")
        if self._deps_checked is not None:
            logger.info("Returning cached deps")
            return self._deps_checked

        logger.info("Checking dependencies (not cached)...")
        evdev_ok = _check_evdev()
        logger.info(f"evdev check result: {evdev_ok}")

        forwarder_exists = os.path.exists(FORWARDER_SCRIPT)
        logger.info(f"forwarder exists: {forwarder_exists}")

        self._deps_checked = {
            "evdev": evdev_ok,
            "forwarder": forwarder_exists,
            "ready": evdev_ok and forwarder_exists,
        }
        logger.info(f"Dependencies final result: {self._deps_checked}")
        return self._deps_checked

    async def get_status(self) -> dict:
        """Get current sharing status"""
        try:
            logger.info("=== get_status called ===")
            running = (
                self._forwarder_proc is not None
                and self._forwarder_proc.poll() is None
            )

            # Cache the deck IP to avoid repeated socket connections
            if self._cached_deck_ip is None:
                logger.info("Getting deck IP...")
                self._cached_deck_ip = _local_ip()
                logger.info(f"Detected deck IP: {self._cached_deck_ip}")

            result = {
                "running": running,
                "port": self._port,
                "deck_ip": self._cached_deck_ip,
            }
            logger.info(f"Returning status: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in get_status: {e}", exc_info=True)
            return {"running": False, "port": self._port, "deck_ip": "error"}

    async def start_sharing(self, port: int = DEFAULT_PORT) -> dict:
        """Start forwarding controller events (Deck runs server)"""
        logger.info(f"========== start_sharing called with port={port} ==========")

        # Check if already running
        if self._forwarder_proc is not None and self._forwarder_proc.poll() is None:
            logger.warning("Cannot start: already running")
            return {"success": False, "error": "Already running"}

        # Check dependencies inline
        logger.info("Checking dependencies...")
        evdev_ok = _check_evdev()
        logger.info(f"evdev available: {evdev_ok}")

        forwarder_exists = os.path.exists(FORWARDER_SCRIPT)
        logger.info(f"forwarder exists: {forwarder_exists}")

        if not evdev_ok:
            error_msg = "Missing: python-evdev"
            logger.error(f"Cannot start: {error_msg}")
            return {"success": False, "error": error_msg}

        if not forwarder_exists:
            error_msg = "Missing: controller_forwarder.py"
            logger.error(f"Cannot start: {error_msg}")
            return {"success": False, "error": error_msg}

        try:
            # Start the forwarder server process using system Python
            # Note: sys.executable is the PyInstaller frozen Decky binary, not a Python interpreter
            # We need system Python to use evdev (same approach as decktation plugin)
            python_bin = "/usr/bin/python3"
            if not os.path.exists(python_bin):
                # Fallback to finding python3 in PATH
                import shutil
                python_bin = shutil.which("python3")
                if not python_bin:
                    logger.error("No python3 found in system")
                    return {"success": False, "error": "System Python not found"}

            logger.info(f"Starting controller forwarder server on port {port}")
            logger.info(f"Using system Python: {python_bin}")
            logger.info(f"Forwarder script: {FORWARDER_SCRIPT}")

            # Start forwarder with system Python (not Decky's bundled Python)
            self._forwarder_proc = subprocess.Popen(
                [python_bin, FORWARDER_SCRIPT, "-p", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            logger.info(f"Subprocess created with PID: {self._forwarder_proc.pid}")

            # Wait a moment to check if it started successfully
            await asyncio.sleep(0.5)

            poll_result = self._forwarder_proc.poll()
            logger.info(f"After 0.5s, process poll result: {poll_result}")

            if poll_result is not None:
                # Process exited immediately, something went wrong
                logger.error(f"Forwarder exited with code: {poll_result}")
                return {"success": False, "error": "Forwarder failed to start. Check system logs."}

            self._port = port

            logger.info(f"✓ Controller forwarder started successfully on port {port}")
            return {
                "success": True,
                "port": port,
                "deck_ip": _local_ip()
            }

        except Exception as e:
            logger.error(f"start_sharing exception: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def stop_sharing(self) -> dict:
        """Stop forwarding controller events"""
        try:
            if self._forwarder_proc is not None:
                logger.info("Stopping controller forwarder")
                self._forwarder_proc.terminate()
                try:
                    self._forwarder_proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    logger.warning("Forwarder didn't stop gracefully, killing")
                    self._forwarder_proc.kill()
                self._forwarder_proc = None

            logger.info("Controller sharing stopped")
            return {"success": True}

        except Exception as e:
            logger.error(f"stop_sharing error: {e}")
            return {"success": False, "error": str(e)}

    # ── lifecycle ─────────────────────────────────────────────────────────────

    async def _main(self):
        logger.info("DeckController plugin loaded")

    async def _unload(self):
        logger.info("DeckController plugin unloading")
        # Stop forwarder if running
        if self._forwarder_proc is not None:
            try:
                self._forwarder_proc.terminate()
                self._forwarder_proc.wait(timeout=3)
            except:
                pass

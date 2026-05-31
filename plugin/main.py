import asyncio
import os
import re
import signal
import socket
import subprocess
import decky_plugin

logger = decky_plugin.logger

USBIPD_PATHS = ["/usr/sbin/usbipd", "/usr/bin/usbipd", "/sbin/usbipd"]
USBIP_PATHS  = ["/usr/sbin/usbip",  "/usr/bin/usbip",  "/sbin/usbip"]
VALVE_VID    = "28de"


def _find_bin(paths: list[str]) -> str | None:
    for p in paths:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def _local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def _find_controller_busid(usbip: str) -> str | None:
    """Parse `usbip list -l` to find the Valve controller bus ID.

    Output looks like:
      - busid 3-2 (28de:1205)
        Valve Software : Steam Deck Controller (28de:1205)
    """
    result = subprocess.run([usbip, "list", "-l"], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if VALVE_VID in line.lower():
            m = re.search(r"busid\s+([\d]+-[\d.]+)", line)
            if m:
                return m.group(1)
    return None


class Plugin:
    _usbipd_proc: subprocess.Popen | None = None
    _bound_busid: str | None = None

    # ── public API (called from frontend) ────────────────────────────────────

    async def check_deps(self) -> dict:
        usbipd = _find_bin(USBIPD_PATHS)
        usbip  = _find_bin(USBIP_PATHS)

        modules_ok = True
        for mod in ("usbip-core", "usbip-host"):
            r = subprocess.run(["modprobe", "--dry-run", mod], capture_output=True)
            if r.returncode != 0:
                modules_ok = False
                break

        return {
            "usbipd":  usbipd is not None,
            "usbip":   usbip  is not None,
            "modules": modules_ok,
            "ready":   usbipd is not None and usbip is not None and modules_ok,
        }

    async def get_status(self) -> dict:
        running = (
            self._usbipd_proc is not None
            and self._usbipd_proc.poll() is None
        )
        return {
            "running": running,
            "busid":   self._bound_busid,
            "ip":      _local_ip(),
        }

    async def start_sharing(self) -> dict:
        usbipd = _find_bin(USBIPD_PATHS)
        usbip  = _find_bin(USBIP_PATHS)

        if not usbipd or not usbip:
            return {"success": False, "error": "usbipd/usbip not found — see README"}

        try:
            for mod in ("usbip-core", "usbip-host"):
                subprocess.run(["modprobe", mod], check=True, capture_output=True)

            busid = _find_controller_busid(usbip)
            if not busid:
                return {"success": False, "error": "Valve controller not found on USB bus"}

            r = subprocess.run([usbip, "bind", "-b", busid], capture_output=True, text=True)
            if r.returncode != 0 and "already bound" not in r.stderr:
                return {"success": False, "error": f"bind failed: {r.stderr.strip()}"}

            self._bound_busid = busid

            if self._usbipd_proc is None or self._usbipd_proc.poll() is not None:
                self._usbipd_proc = subprocess.Popen(
                    [usbipd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            logger.info(f"Sharing controller busid={busid} ip={_local_ip()}")
            return {"success": True, "busid": busid, "ip": _local_ip()}

        except subprocess.CalledProcessError as e:
            logger.error(f"start_sharing: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"start_sharing: {e}")
            return {"success": False, "error": str(e)}

    async def stop_sharing(self) -> dict:
        usbip = _find_bin(USBIP_PATHS)
        try:
            if usbip and self._bound_busid:
                subprocess.run([usbip, "unbind", "-b", self._bound_busid], capture_output=True)
                self._bound_busid = None

            if self._usbipd_proc is not None:
                self._usbipd_proc.terminate()
                try:
                    self._usbipd_proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._usbipd_proc.kill()
                self._usbipd_proc = None

            logger.info("Controller sharing stopped")
            return {"success": True}

        except Exception as e:
            logger.error(f"stop_sharing: {e}")
            return {"success": False, "error": str(e)}

    # ── lifecycle ─────────────────────────────────────────────────────────────

    async def _main(self):
        logger.info("DeckController plugin loaded")

    async def _unload(self):
        logger.info("DeckController plugin unloading")
        await self.stop_sharing()

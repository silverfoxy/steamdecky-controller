# Steamy Controller

**Share your Steam Deck controller wirelessly over the network**

A beautiful, modern GUI app for sharing your Steam Deck's built-in controller to your PC using USB/IP. Features automatic PC connection detection, sleep prevention while sharing, screen dimming, and a touch-friendly interface.

## Features

- **Share controller over network** - Use your Deck's controls on your PC
- **PC connection detection** - Automatically detects when your PC connects
- **PC auto-discovery** - Linux client finds an actively sharing Deck via mDNS (Avahi)
- **Sleep prevention while sharing** - Rechecks and restores the idle/sleep inhibitor if it exits

## Prerequisites

### Steam Deck Setup

1. **Install USB/IP tools via Nix:**

   ```bash
   nix profile install nixpkgs#linuxPackages.usbip
   ```

2. **Configure passwordless sudo (REQUIRED):**

   The app needs to run certain commands without password prompts. Create a sudoers file:

   ```bash
   sudo visudo -f /etc/sudoers.d/steamdecky-controller
   ```

   Add these lines (replace `deck` with your username if different):

   ```
   # Steamy Controller - USB/IP and system control
   deck ALL=(ALL) NOPASSWD: /usr/bin/modprobe usbip-core
   deck ALL=(ALL) NOPASSWD: /usr/bin/modprobe usbip-host
   deck ALL=(ALL) NOPASSWD: /usr/bin/modprobe vhci-hcd
   deck ALL=(ALL) NOPASSWD: /home/deck/.nix-profile/bin/usbipd
   deck ALL=(ALL) NOPASSWD: /home/deck/.nix-profile/bin/usbip
   deck ALL=(ALL) NOPASSWD: /usr/bin/killall usbipd
   deck ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/bus/usb/drivers/usbip-host/unbind
   deck ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/bus/usb/drivers_probe
   deck ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/class/backlight/*/brightness
   ```

   Save and exit. Test it works:

   ```bash
   sudo modprobe usbip-core  # Should not ask for password
   ```

3. **Optional auto-discovery:** Install `avahi-publish-service` and run `avahi-daemon` on the Deck. The app advertises `_steamy-controller._tcp` on port 3240 only while sharing. If unavailable, the displayed IP and bus ID still work with the manual client command. Discovery needs mDNS (UDP 5353) permitted on the local network.

4. **Sleep prevention:** The app requires `systemd-inhibit` and `sleep` to hold an idle/sleep block during sharing. It retries if the inhibitor exits and shows a warning if it cannot hold the block; screen dimming is separate from suspend prevention.

### PC Setup

Install USB/IP tools and Avahi on the Linux PC (plus Python 3 for the discovery parser):

- **Ubuntu/Debian:** `sudo apt install linux-tools-generic avahi-utils`
- **Fedora:** `sudo dnf install usbip avahi-tools`
- **Arch:** `sudo pacman -S usbip avahi`

Ensure `avahi-daemon` is running. If mDNS is unavailable, pass the Deck IP and displayed bus ID explicitly instead.

## Quick Start

### 1. Add to Steam Library

1. Switch to **Desktop Mode**
2. Open **Steam** → Games → **Add Non-Steam Game**
3. Browse to: `/home/deck/.../steamdecky-controller/`
4. Select **`deck-controller-gui.py`**
5. Optional: Rename to "Steamy Controller"

### 2. Launch from Gaming Mode

1. Find **Steamy Controller** in your library
2. Tap **START SHARING** (green button)
3. Status changes to **"Waiting for PC..."** (orange)

### 3. Connect from PC

```bash
cd pc-scripts
./pc-connect.sh
```

The client selects the one advertised Deck and checks the advertised USB bus ID against the exported Valve controller before attaching. If more than one Deck is found, it refuses to guess; use `./pc-connect.sh <deck-ip> <busid>`. This also works when Avahi/mDNS is unavailable. Discovery is for convenience, **not authentication**: use USB/IP only on a trusted network.

Status changes to **"PC Connected"** (green) ✅

### 4. Stop Sharing

Use **touchscreen** to tap **STOP SHARING** button

- Controller restored to Deck (the app will keep the sleep lock and offer a retry if restore fails)
- Screen brightness restored
- Status returns to **"Ready"** only after successful restoration. The app leaves `usbipd` running because another USB/IP export may use it; the controller itself is no longer exported. USB/IP has no built-in authentication, so restrict port 3240 to trusted hosts/networks.

## How It Works

1. **Start Sharing** - Controller unbinds from Deck, shared via USB/IP
2. **PC Connects** - App detects connection, status turns green
3. **Auto Screen Management:**
   - Screen dims after 10 seconds
   - Tap screen to wake
   - Idle suspend and idle display sleep are blocked while sharing is active
4. **Stop Sharing** - Controller rebinds to Deck, everything restored

## Important Notes

### ⚠️ Controller Disabled While Sharing

When sharing is active:

- **Physical buttons won't work on the Deck**
- **Must use touchscreen** to stop sharing
- This is normal - controller is bound to USB/IP

### Screen Behavior

- **Dims after 10 seconds** - Tap screen to wake
- **Deck stays awake while sharing** - The controller is unavailable to Steam Input
  during USB/IP sharing, so the app blocks idle sleep until you stop sharing
- **Auto-restores on exit** - Brightness returns to normal

### Network Requirements

- Both devices on same network
- Low latency connection recommended
- PC firewall may need USB/IP traffic allowed (port 3240)

## Troubleshooting

### "Permission denied" or sudo prompts

You need to configure sudoers (see Prerequisites section above). The app requires passwordless sudo for:

- Loading kernel modules
- Starting/stopping usbipd
- Binding/unbinding devices
- Controlling screen brightness

### "usbip not found"

Make sure you installed via Nix and the path in sudoers matches:

```bash
which usbip  # Should show /home/deck/.nix-profile/bin/usbip
```

### App won't start

Make sure you're using a Python environment with working Kivy native modules; the app does **not** use tkinter. This repository's `lib/` contains Python sources but may not include compiled Kivy extensions for every system. If `kivy._clock` is missing, install a matching Kivy build for your Python interpreter. Then launch:

```bash
/usr/bin/python3 deck-controller-gui.py
```

The app should launch automatically when run from Steam.

### Check USB/IP status

```bash
# On Deck (server side):
~/.nix-profile/bin/usbip list -l

# Check if PC is connected:
~/.nix-profile/bin/usbip port

# On PC (client side):
sudo usbip port
```

### Can't stop sharing

If the app crashes or you can't stop:

```bash
# Restore controller manually:
echo "3-3" | sudo tee /sys/bus/usb/drivers/usbip-host/unbind
echo "3-3" | sudo tee /sys/bus/usb/drivers_probe
sudo killall usbipd
```

## Project Structure

```
steamdecky-controller/
├── deck-controller-gui.py    # Main Kivy app
├── deck_services.py          # Avahi publication and sleep inhibitor lifecycle
├── background.webp           # Custom background image
├── lib/                      # Python dependencies (self-contained)
│   ├── kivy/                # Modern touch UI framework
│   ├── darkdetect/
│   ├── filetype/
│   └── packaging/
├── pc-scripts/
│   ├── discover_deck.py      # Parse resolved Avahi service records
│   ├── pc-connect.sh         # Discover/connect from Linux PC
│   └── pc-disconnect.sh      # Disconnect from PC
└── README.md
```

## Technical Details

### USB/IP Approach

Uses Linux kernel's USB/IP functionality to share USB devices over the network:

- **No plugins required** - Pure kernel-level solution
- **Low latency** - Minimal overhead over LAN
- **Standard protocol** - Works with any Linux USB/IP client

### Controller Device

Steam Deck controller details:

- **VID:PID** - `28de:1205` (Valve Software)
- **Bus ID** - Usually `3-3` (may vary)
- **Device** - `/dev/input/event*`

## License

MIT

---

**Made for Steam Deck** ☁️🎮

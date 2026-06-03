# Steam Deck Controller Forwarding via USB/IP

Forward your Steam Deck's built-in controller to your PC over the network using USB/IP.

## Overview

This project allows you to use your Steam Deck's physical controls on your PC while streaming games or using remote play. Instead of complex plugin approaches, we use the Linux kernel's USB/IP functionality to share the controller device over the network.

## How It Works

1. **On the Deck:** USB/IP exports the controller device and shares it over the network
2. **On the PC:** USB/IP attaches to the remote device, making it appear as a local USB controller
3. **Result:** PC sees the Steam Deck controller as if it were directly connected via USB

## Prerequisites

### Steam Deck
- USB/IP tools installed via Nix: `nix profile install nixpkgs#linuxPackages.usbip`
- Root/sudo access
- **Python 3 with tkinter** (pre-installed on Steam Deck)

### PC
- USB/IP tools installed:
  - **Ubuntu/Debian:** `sudo apt install linux-tools-generic`
  - **Fedora:** `sudo dnf install usbip`
  - **Arch:** `sudo pacman -S usbip`
- Root/sudo access

## Quick Start

### Option 1: Touchscreen GUI (Recommended)

**Why use the GUI?** When the controller is exported, physical buttons stop working on the Deck. You need touchscreen controls to stop sharing!

1. **Add to Steam as Non-Steam Game:**
   - Desktop Mode → Steam → Games → Add Non-Steam Game
   - Browse to: `/home/deck/Documents/personal/steamdecky-controller/`
   - Select `deck-controller-gui.py`
   - Rename to "Controller Share" (optional)

2. **Launch from Gaming Mode:**
   - Find "Controller Share" in your library
   - Tap **START SHARING** (big green button)
   - Controller is now disabled on Deck, shared via network

3. **On PC:**
   ```bash
   cd pc-scripts
   ./pc-connect.sh <deck-ip>
   ```

4. **Stop Sharing:**
   - Use **touchscreen** to tap "STOP SHARING" button
   - Controller re-enabled on Deck

### Option 2: Shell Scripts (Terminal)

**On Deck:**
```bash
./deck-start-usbip.sh    # Start sharing
./deck-stop-usbip.sh     # Stop sharing
```

**On PC:**
```bash
cd pc-scripts
./pc-connect.sh <deck-ip>
./pc-disconnect.sh
```

## Test Mode (Local Loopback on Deck)

To test USB/IP without a PC:

```bash
# 1. Start sharing
./deck-start-usbip.sh

# 2. Load client module
sudo modprobe vhci-hcd

# 3. Attach to localhost
sudo ~/.nix-profile/bin/usbip attach -r 127.0.0.1 -b 3-3
```

If the controller still works on the Deck, USB/IP is working correctly!

## Important Notes

### Controller Disabled While Sharing
When you start sharing:
- **Physical buttons won't work on the Deck** (controller is unbound)
- **Use the touchscreen** to stop sharing
- This is why the GUI app is recommended!

### Network Requirements
- Both devices must be on the same network
- Low latency connection recommended (wired or 5GHz WiFi)
- PC firewall may need to allow USB/IP traffic

## Troubleshooting

### "usbip not found" when using sudo
If you installed via Nix, sudo doesn't see your user's PATH. The scripts handle this automatically by using the full path.

### "device with the specified bus ID does not exist"
Run `usbip list -l` to see the correct busid format. The scripts now use this automatically.

### "is vhci_hcd loaded?"
Load the client-side kernel module:
```bash
sudo modprobe vhci-hcd
```

### GUI app won't start
- Make sure tkinter is installed: `python3 -m tkinter` (should open a window)
- Check the script is executable: `chmod +x deck-controller-gui.py`

### Check USB/IP status
```bash
# On Deck (server side):
sudo usbip list -l

# On PC (client side):
sudo usbip port
```

## Why USB/IP?

See [JOURNEY.md](JOURNEY.md) for the full story of approaches tried and lessons learned.

**TL;DR:** Direct event reading and Decky plugins hit permission barriers. USB/IP is a kernel-level solution that:
- Requires no plugins or modifications
- Works at the USB device level
- Is well-supported in Linux
- Has minimal latency over LAN

## Project Structure

```
.
├── deck-controller-gui.py   # Touchscreen GUI app (recommended)
├── deck-start-usbip.sh      # Start sharing controller from Deck
├── deck-stop-usbip.sh       # Stop sharing
├── pc-scripts/
│   ├── pc-connect.sh        # Connect to controller from PC
│   └── pc-disconnect.sh     # Disconnect from controller
├── archive/                 # Previous approaches (see archive/README.md)
└── JOURNEY.md              # Development story and lessons learned
```

## License

MIT

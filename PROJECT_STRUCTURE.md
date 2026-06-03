# Project Structure

## Overview

This project shares the Steam Deck's built-in controller to a PC over the network using USB/IP.

## Directory Structure

```
steamdecky-controller/
├── README.md                    # Main documentation - how to use USB/IP solution
├── JOURNEY.md                   # Development story and lessons learned
├── PROJECT_STRUCTURE.md         # This file
│
├── deck-start-usbip.sh         # Start sharing controller from Deck
├── deck-stop-usbip.sh          # Stop sharing controller
│
├── pc-scripts/                 # Scripts for PC to connect to Deck
│   ├── pc-connect.sh           # Connect to shared controller
│   └── pc-disconnect.sh        # Disconnect from controller
│
└── archive/                    # Previous approaches (archived)
    ├── README.md               # What's in the archive and why
    ├── decky-plugin-attempt/   # Decky Loader plugin approach
    │   ├── plugin/             # Plugin code
    │   └── pc-client/          # Original PC client
    └── experiments/            # Testing and discovery scripts
```

## Current Solution: USB/IP

The active codebase uses Linux kernel's USB/IP functionality to share the Steam Deck controller as a USB device over the network.

### Deck Scripts

| File | Purpose |
|------|---------|
| `deck-start-usbip.sh` | Export and share the controller via USB/IP |
| `deck-stop-usbip.sh` | Stop sharing and rebind controller to local system |

### PC Scripts

| File | Purpose |
|------|---------|
| `pc-scripts/pc-connect.sh` | Attach to remote controller from PC |
| `pc-scripts/pc-disconnect.sh` | Detach from controller |

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | User-facing documentation, quick start guide |
| `JOURNEY.md` | Developer documentation, approaches tried, lessons learned |
| `PROJECT_STRUCTURE.md` | This file - project overview |
| `archive/README.md` | Explanation of archived code |

## How It Works

USB/IP is a Linux kernel feature that allows USB devices to be shared over a network.

### Architecture

```
┌──────────────────────────────────────────────────┐
│                  Steam Deck                      │
│                                                  │
│  ┌──────────────┐       ┌────────────────┐     │
│  │  Controller  │──USB──│  usbipd        │     │
│  │  (28de:1205) │       │  (exports USB) │─────┼──┐
│  └──────────────┘       └────────────────┘     │  │
│                                                  │  │
└──────────────────────────────────────────────────┘  │
                                                      │
                                           Network/TCP│
                                                      │
┌──────────────────────────────────────────────────┐  │
│                   PC (Linux)                     │  │
│                                                  │  │
│  ┌────────────────┐     ┌──────────────────┐   │  │
│  │  vhci-hcd      │◄────│  usbip attach    │◄──┼──┘
│  │  (USB device)  │     │  (client)        │   │
│  └────────┬───────┘     └──────────────────┘   │
│           │                                     │
│           ▼                                     │
│  ┌────────────────┐                            │
│  │  Games/Apps    │                            │
│  │  (sees real    │                            │
│  │   USB device)  │                            │
│  └────────────────┘                            │
└──────────────────────────────────────────────────┘
```

### Workflow

**On Deck:**
1. `deck-start-usbip.sh` finds controller (busid 3-3)
2. Unbinds from local USB driver
3. Starts `usbipd` daemon to share over network
4. Controller is exported but not locally available

**On PC:**
1. `pc-connect.sh <deck-ip>` loads `vhci-hcd` module
2. Attaches to remote USB device via TCP
3. Controller appears as `/dev/input/eventX`
4. Games see it as a native USB controller

**Test Mode (Loopback):**
- Attach to 127.0.0.1 on the Deck itself
- Controller re-appears via USB/IP tunnel
- Validates setup before PC testing

## Requirements

### Steam Deck
- **USB/IP tools:** `nix profile install nixpkgs#linuxPackages.usbip`
- **Kernel modules:** `usbip-core`, `usbip-host` (auto-loaded by script)
- **Permissions:** sudo/root access

### PC
- **USB/IP tools:**
  - Ubuntu/Debian: `sudo apt install linux-tools-generic`
  - Fedora: `sudo dnf install usbip`
  - Arch: `sudo pacman -S usbip`
- **Kernel module:** `vhci-hcd` (auto-loaded by script)
- **Permissions:** sudo/root access

## Usage

### On Deck
```bash
./deck-start-usbip.sh    # Start sharing
./deck-stop-usbip.sh     # Stop sharing
```

### On PC
```bash
cd pc-scripts
./pc-connect.sh 192.168.1.206     # Connect to Deck
./pc-disconnect.sh                # Disconnect
```

### Test Mode
```bash
# On Deck only:
./deck-start-usbip.sh
sudo modprobe vhci-hcd
sudo ~/.nix-profile/bin/usbip attach -r 127.0.0.1 -b 3-3
# Controller should still work on Deck!
```

## Archive

Previous approaches (evdev, Decky plugin) are preserved in `archive/` for:
- Historical reference
- Learning from what didn't work
- Potential code reuse for other projects

See [JOURNEY.md](JOURNEY.md) for the full development story.

## Key Insights

**Why USB/IP won:**
- Works at kernel level (no permission issues)
- Doesn't conflict with Steam Input
- Native USB device on PC (no virtual device needed)
- Minimal latency over LAN
- Standard Linux tooling

**What we learned:**
- The controller is just a USB device (VID:28de PID:1205)
- `usbip list -l` shows correct busid format (not lsusb)
- Test locally first with loopback (127.0.0.1)
- Nix + sudo PATH issues solved with full paths

## License

MIT

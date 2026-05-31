# Steam Deck Controller Forwarder - Project Structure

## Overview

This project enables forwarding Steam Deck controller input to a Linux PC over Wi-Fi using evdev/uinput.

## Directory Structure

```
steamdecky-controller/
├── plugin/                      # Decky Loader plugin (Deck side)
│   ├── src/
│   │   └── index.tsx           # Frontend UI
│   ├── dist/                   # Built frontend (generated)
│   ├── main.py                 # Backend plugin logic
│   ├── controller_forwarder.py # Reads evdev, forwards events over UDP
│   ├── plugin.json             # Plugin metadata
│   ├── package.json            # Node dependencies
│   ├── rollup.config.js        # Build configuration
│   ├── tsconfig.json           # TypeScript config
│   ├── build.sh                # Build frontend only
│   ├── copy.sh                 # Copy to Decky (no build)
│   ├── deploy.sh               # Build + deploy to Decky
│   ├── README.md               # Main plugin documentation
│   ├── DEVELOPMENT_LOG.md      # Development history & decisions
│   ├── TESTING_GUIDE.md        # Testing instructions
│   └── legacy-usbip/           # Old USB/IP approach (deprecated)
│
├── pc-client/                   # PC side client
│   ├── pc_client.py            # Receives events, creates virtual controller
│   ├── setup.sh                # One-time PC setup script
│   ├── README.md               # PC client documentation
│   ├── connect-usbip.sh.old    # Old USB/IP script (deprecated)
│   └── disconnect-usbip.sh.old # Old USB/IP script (deprecated)
│
└── PROJECT_STRUCTURE.md         # This file
```

## Key Files

### Deck Side (Plugin)

| File | Purpose |
|------|---------|
| `main.py` | Plugin backend - manages forwarder process |
| `controller_forwarder.py` | Reads evdev events, forwards via UDP |
| `src/index.tsx` | React frontend UI |
| `dist/index.js` | Built frontend (IIFE format) |
| `plugin.json` | Plugin metadata for Decky |

### PC Side (Client)

| File | Purpose |
|------|---------|
| `pc_client.py` | Receives UDP events, creates virtual uinput device |
| `setup.sh` | Installs python3-uinput, configures uinput module |
| `README.md` | PC setup & troubleshooting guide |

### Documentation

| File | Purpose |
|------|---------|
| `plugin/README.md` | Main plugin documentation |
| `plugin/DEVELOPMENT_LOG.md` | Full development history, design decisions |
| `plugin/TESTING_GUIDE.md` | Quick testing guide |
| `pc-client/README.md` | PC client setup & usage |
| `PROJECT_STRUCTURE.md` | This file - project overview |

### Build Scripts

| Script | Purpose |
|--------|---------|
| `build.sh` | Build frontend only (`npm run build`) |
| `copy.sh` | Copy files to Decky without building |
| `deploy.sh` | Build + copy to Decky (recommended) |

## Workflow

### Development

1. **Edit code** in `plugin/src/` or `plugin/main.py`
2. **Build**: `cd plugin && ./build.sh`
3. **Deploy**: `./deploy.sh`
4. **Restart Decky Loader** to reload plugin

### Testing

1. **PC**: Run `cd pc-client && python3 pc_client.py`
2. **Deck**: Open plugin, enter PC IP, click "Start Sharing"
3. **Test**: Press buttons on Deck, verify on PC

## Technology Stack

### Deck Side
- **Python 3** (plugin backend)
- **python-evdev** (reading controller events)
- **React + TypeScript** (frontend UI)
- **Rollup 2.x** (bundler, IIFE output)
- **Decky Frontend Lib** (UI components)

### PC Side
- **Python 3** (client)
- **python-uinput** (virtual device creation)
- **Linux uinput module** (kernel virtual input)

### Network
- **UDP** (event transport, port 9090)
- **Custom protocol** (8-byte event packets)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Steam Deck                         │
│                                                         │
│  ┌──────────────┐         ┌──────────────────┐        │
│  │   Physical   │  evdev  │  controller_     │        │
│  │  Controller  ├────────→│  forwarder.py    │        │
│  │              │         │                  │        │
│  └──────────────┘         └─────────┬────────┘        │
│                                     │                  │
│  ┌──────────────┐                  │ UDP              │
│  │ Decky Plugin │                  │ (events)         │
│  │  (manages)   ├──────────────────┘                  │
│  └──────────────┘                                     │
└─────────────────────────────┬───────────────────────────┘
                              │
                              │ Network (WiFi)
                              │
┌─────────────────────────────┴───────────────────────────┐
│                        Linux PC                         │
│                                                         │
│  ┌──────────────────┐       ┌──────────────────┐      │
│  │  pc_client.py    │       │    Virtual       │      │
│  │  (receives UDP)  ├──────→│   Controller     │      │
│  │                  │ uinput│   /dev/input/*   │      │
│  └──────────────────┘       └────────┬─────────┘      │
│                                       │                │
│                              ┌────────┴─────────┐     │
│                              │   Games/Apps     │     │
│                              └──────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Event Flow

1. User presses button on Steam Deck
2. Linux kernel generates evdev event → `/dev/input/eventX`
3. `controller_forwarder.py` reads event
4. Packs into 8 bytes: `[type:u16, code:u16, value:i32]`
5. Sends via UDP to PC IP:9090
6. `pc_client.py` receives packet
7. Unpacks event
8. Injects into virtual uinput device
9. PC games/apps see it as real controller input

## Port Information

- **Default**: UDP port 9090
- **Configurable** in plugin UI
- **Firewall**: Must allow incoming UDP on PC

## Dependencies

### Deck (Pre-installed on SteamOS)
- python-evdev
- Python 3.10+

### PC (Requires installation)
- python3-uinput
- uinput kernel module
- Python 3.6+

## Build Output

After `npm run build`:
- `dist/index.js` - IIFE bundle (not ES module)
- Includes React, UI components
- Externals: react, react-dom, decky-frontend-lib (provided by Decky)

## Deployment Target

- **Path**: `~/homebrew/plugins/steamdecky-controller/`
- **Required files**:
  - `main.py`
  - `controller_forwarder.py`
  - `plugin.json`
  - `package.json`
  - `dist/index.js`

## Version History

- **v1.0** - Initial USB/IP approach (deprecated)
- **v2.0** - Evdev/uinput approach (current)

## Future Ideas

- Auto-discover PC on network (mDNS/Bonjour)
- Multiple controller support
- Latency monitoring
- Compression for high-frequency events
- Encryption for events
- Web-based PC client (no Python required)
- Binary distribution for PC client

## Contributing

When modifying:
1. Update relevant documentation
2. Test on both Deck and PC
3. Update DEVELOPMENT_LOG.md with significant changes
4. Keep legacy files in `legacy-usbip/` for reference

## License

MIT

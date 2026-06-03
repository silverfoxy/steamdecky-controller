# Steam Deck Controller Client (PC Side)

This directory contains the PC client for receiving controller input from your Steam Deck over the network.

## Quick Start

### 1. Run Setup (One-time)

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Install `python3-uinput`
- Load the `uinput` kernel module
- Configure uinput to load on boot
- Optionally add your user to the `input` group

### 2. Run the Client

```bash
python3 pc_client.py -p 9090
```

You should see:
```
============================================================
Steam Deck Controller Client
============================================================
Creating virtual Steam Deck controller...
Virtual controller created: /dev/input/eventX
Listening for events from Steam Deck on port 9090...
Press Ctrl+C to stop
```

### 3. Start Sharing from Deck

On your Steam Deck:
1. Open the Decky Loader plugin
2. Enter your PC's IP address
3. Click "Start Sharing"
4. Press buttons and see events on your PC!

## Files

- `pc_client.py` - Main client script (receives events, creates virtual controller)
- `setup.sh` - One-time setup script for dependencies
- `README.md` - This file

## Manual Setup

If you prefer not to use the setup script:

```bash
# Install dependencies
sudo apt install python3-uinput  # Ubuntu/Debian
sudo dnf install python3-uinput  # Fedora
sudo pacman -S python-uinput     # Arch

# Load uinput module
sudo modprobe uinput

# Make it load on boot
echo "uinput" | sudo tee /etc/modules-load.d/uinput.conf

# Optional: Run without sudo
sudo usermod -a -G input $USER
# Then log out and back in
```

## Testing

### Verify the Virtual Controller

```bash
# List input devices
cat /proc/bus/input/devices | grep -A10 "Steam Deck"

# Should show:
# N: Name="Steam Deck Controller (Network)"
# I: Bus=0003 Vendor=28de Product=1205 Version=0200

# Test with evtest
sudo evtest
# Select the "Steam Deck Controller (Network)" device
# Press buttons on Deck, see events here!

# Test as joystick
jstest /dev/input/js0  # Adjust js number as needed
```

### Check Firewall

If no events are received, allow UDP port 9090:

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 9090/udp

# Fedora (firewalld)
sudo firewall-cmd --add-port=9090/udp --permanent
sudo firewall-cmd --reload

# Check what's listening
sudo ss -ulnp | grep 9090
```

## Usage Options

```bash
# Basic usage (listen on port 9090)
python3 pc_client.py

# Custom port
python3 pc_client.py -p 8888

# Run with sudo (if not in input group)
sudo python3 pc_client.py

# See help
python3 pc_client.py --help
```

## Troubleshooting

### "Permission denied" when creating device

Add yourself to the input group:
```bash
sudo usermod -a -G input $USER
```
Then log out and back in, or run with sudo temporarily.

### "Module uinput not found"

Load the kernel module:
```bash
sudo modprobe uinput
```

### "python3-uinput not installed"

Install it:
```bash
sudo apt install python3-uinput
```

### No events received

1. Check firewall allows UDP port 9090
2. Verify both devices on same network
3. Check PC IP address in Deck plugin is correct
4. Make sure Deck plugin shows "Forwarding" status

### Virtual device not appearing

Check if uinput module is loaded:
```bash
lsmod | grep uinput
```

Check for errors:
```bash
dmesg | grep uinput
```

## Advanced Usage

### Run as Systemd Service

Create `/etc/systemd/system/deck-controller-client.service`:

```ini
[Unit]
Description=Steam Deck Controller Client
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
ExecStart=/usr/bin/python3 /path/to/pc_client.py -p 9090
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable deck-controller-client
sudo systemctl start deck-controller-client
sudo systemctl status deck-controller-client
```

### Multiple Steam Decks

Run multiple instances on different ports:
```bash
# Terminal 1 - Deck 1
python3 pc_client.py -p 9090

# Terminal 2 - Deck 2
python3 pc_client.py -p 9091
```

Then configure each Deck to use its assigned port.

## Legacy Scripts

- `connect-usbip.sh.old` - Old USB/IP approach (deprecated)
- `disconnect-usbip.sh.old` - Old USB/IP approach (deprecated)

These are kept for reference but are no longer used.

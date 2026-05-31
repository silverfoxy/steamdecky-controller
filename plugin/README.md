# Steam Deck Controller Forwarder

A Decky Loader plugin that forwards your Steam Deck's controller input to a Linux PC over Wi-Fi using evdev/uinput. Your controller works on **both** the Deck and PC simultaneously!

## Features

- **Safe**: No driver unbinding or system modifications required
- **Low latency**: UDP-based event forwarding
- **Works everywhere**: Controller stays functional on Deck while forwarding
- **Virtual device**: Creates a virtual Steam Deck controller on your PC
- **Simple setup**: No complex dependencies or permissions

## Architecture

```
Steam Deck:                     Network (UDP)                PC:
┌──────────────────┐           ┌─────────┐         ┌──────────────────┐
│  /dev/input/eventX│──read───>│ Forward │───UDP──>│  Receive events  │
│ (real controller) │           │ events  │         │  Create uinput   │
└──────────────────┘           └─────────┘         │  virtual device  │
                                                    └──────────────────┘
```

## Requirements

### Steam Deck
- **Decky Loader** installed
- **python-evdev** (pre-installed on Steam Deck)

### Linux PC
- **python-uinput**: `sudo apt install python3-uinput`
- **uinput module**: `sudo modprobe uinput`
- **PC client script**: `pc_client.py` (provided)

## PC Setup

### 1. Install Dependencies

```bash
# Install uinput support
sudo apt install python3-uinput

# Load uinput module
sudo modprobe uinput

# Make uinput load on boot (optional)
echo "uinput" | sudo tee /etc/modules-load.d/uinput.conf
```

### 2. Add User to Input Group (Optional)

To run without sudo:

```bash
sudo usermod -a -G input $USER
# Log out and back in for this to take effect
```

### 3. Get the PC Client Script

Copy `pc_client.py` from the plugin directory to your PC, or download it from the repository.

## Usage

### On Your PC:

1. **Run the client**:
   ```bash
   python3 pc_client.py -p 9090
   ```

   The client will create a virtual Steam Deck controller and wait for events.

### On Your Steam Deck:

1. **Open the plugin** in Decky (Quick Access → Controller icon)

2. **Enter your PC's IP address** (e.g., `192.168.1.100`)

3. **Click "Start Sharing"**

4. **Test the controller!** Press buttons on your Steam Deck and they should register on your PC.

### Verify It's Working (PC):

```bash
# List input devices - you should see "Steam Deck Controller (Network)"
cat /proc/bus/input/devices | grep -A10 "Steam Deck"

# Test with evtest
sudo evtest
# Select the "Steam Deck Controller (Network)" device
# Press buttons on Deck, see events on PC!

# Or use jstest for joystick testing
jstest /dev/input/js0
```

## Troubleshooting

### "python-evdev not installed" on Deck

This should be pre-installed, but if not:
```bash
pip install --user evdev
```

### "python-uinput not installed" on PC

```bash
sudo apt install python3-uinput
```

### "Permission denied" for uinput on PC

Either add yourself to the input group (see PC Setup) or run with sudo:
```bash
sudo python3 pc_client.py -p 9090
```

### No events received on PC

- Check firewall on PC (allow UDP port 9090)
- Verify IP address is correct
- Make sure both devices are on the same network
- Check the plugin shows "Forwarding" status

### Controller not found on Deck

The plugin looks for the Steam Deck controller by:
- Vendor ID: 0x28de (Valve)
- Product ID: 0x1205 (Steam Deck Controller)
- Name containing "Steam" and "Deck"

If it still can't find it, check available devices:
```bash
python3 -c "from evdev import list_devices, InputDevice; [print(f'{InputDevice(d).name} - {d}') for d in list_devices()]"
```

## Development

### Building the Plugin

```bash
npm install
npm run build
```

### Deploying to Decky

```bash
./deploy.sh
# Then restart Decky Loader
```

### Manual Testing (Standalone Scripts)

You can test the forwarder without the plugin:

**On PC:**
```bash
python3 pc_client.py -p 9090
```

**On Deck:**
```bash
python3 controller_forwarder.py <PC_IP> -p 9090
```

## Files

- `main.py` - Plugin backend (manages forwarder process)
- `controller_forwarder.py` - Reads evdev events and forwards via UDP
- `pc_client.py` - Receives events and creates virtual uinput device
- `src/index.tsx` - Plugin frontend UI
- `plugin.json` - Plugin metadata
- `DEVELOPMENT_LOG.md` - Development history and design decisions
- `TESTING_GUIDE.md` - Quick testing guide

## Technical Details

### Event Format

Events are forwarded using the standard Linux input event structure:
- `type`: uint16 (event type, e.g., EV_KEY, EV_ABS)
- `code`: uint16 (event code, e.g., BTN_A, ABS_X)
- `value`: int32 (event value)

Total: 8 bytes per event, sent via UDP

### Controller Capabilities

The virtual device matches the Steam Deck controller exactly:
- All buttons (A/B/X/Y, bumpers, triggers, D-pad, etc.)
- Both analog sticks (with full range)
- Analog triggers
- Vendor/Product IDs match Steam Deck controller

### Why UDP?

- **Low latency**: No connection overhead
- **Simple**: No handshaking required
- **Efficient**: Minimal bandwidth for controller events
- **Lossy is OK**: Missing a frame or two doesn't matter for input

## Why This Approach?

We initially tried USB/IP for true USB passthrough, but hit fundamental permission issues:
- Requires driver unbinding (needs root/capabilities)
- Controller becomes unavailable on Deck
- Risk of breaking controller if something fails
- Complex setup with udev rules

The evdev/uinput approach is:
- **Safer**: No driver modifications
- **Simpler**: No special permissions needed
- **Better UX**: Controller works on both devices
- **More reliable**: Can't break the controller

See `DEVELOPMENT_LOG.md` for the full story.

## License

MIT

## Contributing

Pull requests welcome! Please test thoroughly on both Steam Deck and target PC.

## Acknowledgments

- Built for [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader)
- Uses [python-evdev](https://python-evdev.readthedocs.io/)
- Uses [python-uinput](https://github.com/tuomasjjrasanen/python-uinput)

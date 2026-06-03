# Testing Guide - evdev/uinput Controller Forwarding

## Quick Test (Standalone)

### On Your PC:

1. **Install dependencies**:
```bash
sudo apt install python3-uinput
sudo modprobe uinput

# Verify uinput is loaded
lsmod | grep uinput
```

2. **Copy pc_client.py to your PC**

3. **Run the client**:
```bash
python3 pc_client.py
# It will wait for events from the Steam Deck
```

### On Your Steam Deck:

1. **Check if evdev is available** (should be pre-installed):
```bash
python -c "import evdev; print('evdev OK')"
```

2. **Find your PC's IP address** (from your PC):
```bash
ip addr | grep inet
# Look for something like 192.168.1.x
```

3. **Run the forwarder**:
```bash
cd /home/deck/Documents/personal/steamdecky-controller/plugin
python3 controller_forwarder.py <YOUR_PC_IP>
```

4. **Press buttons on your Steam Deck!**
   - You should see event counts increasing
   - On PC, you should see events being received
   - Controller works on both Deck AND PC simultaneously!

### Verify on PC:

```bash
# List input devices - you should see the virtual controller
cat /proc/bus/input/devices | grep -A10 "Steam Deck"

# Test with evtest
sudo evtest
# Select the "Steam Deck Controller (Network)" device
# Press buttons on Deck, see events on PC!

# Or use jstest for joystick testing
jstest /dev/input/js0  # or whichever js device it is
```

## Troubleshooting

**"python-evdev not installed"** on Deck:
```bash
# evdev should be pre-installed, but if not:
pip install --user evdev
```

**"python-uinput not installed"** on PC:
```bash
sudo apt install python3-uinput
```

**"Permission denied" for uinput**:
```bash
# Add yourself to input group
sudo usermod -a -G input $USER
# Log out and back in

# Or run with sudo (testing only)
sudo python3 pc_client.py
```

**No events received**:
- Check firewall on PC (allow UDP port 9090)
- Verify IP address is correct
- Make sure both on same network

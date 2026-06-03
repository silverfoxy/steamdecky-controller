# Steam Deck Controller Forwarder App

A standalone fullscreen app that forwards your Steam Deck's controller input to a PC over the network.

## Features

- 🎮 Fullscreen GUI showing connection status
- 🔒 Automatically grabs controller (Deck controls disabled while running)
- 📡 Forwards all button/joystick events to PC
- 🖥️ Visual feedback of connection and events
- 🔄 Exit app to release controller back to Deck

## Setup

### 1. Dependencies (Choose One Method)

**Option A: Using Nix (Recommended for Steam Deck)**

Since Steam Deck has an immutable filesystem, use Nix to manage dependencies.
No installation needed - dependencies are loaded when you run the app!

Just use the `launch-nix.sh` launcher (it will download/build on first run).

**Option B: Using pip (if you have a mutable system)**

```bash
pip install pygame
```
Then use the regular `launch.sh` launcher.

### 2. Add to Steam as Non-Steam Game

1. Switch to **Desktop Mode** on Steam Deck
2. Open Steam
3. Click **Games** → **Add a Non-Steam Game to My Library**
4. Click **Browse**
5. Navigate to: `/home/deck/Documents/personal/steamdecky-controller/deck-controller-app/`
6. Select `launch-nix.sh` (recommended) or `launch.sh` (if using pip)
7. Click **Add Selected Programs**

### 3. Rename and Customize (Optional)

1. Right-click the game in your library → **Properties**
2. Change name to: **"Deck Controller Forwarder"**
3. You can add a custom icon/banner if you want

### 4. Switch Back to Gaming Mode

Return to Gaming Mode and you'll see the app in your library.

## Usage

### On Steam Deck:

1. Launch **Deck Controller Forwarder** from your Steam library
2. The fullscreen app will show:
   - Your Steam Deck's IP address
   - Connection status
   - Number of events forwarded
3. Controller is now locked to the app (Deck controls won't work)

### On PC:

1. Make sure PC client is set up (see `../pc-client/README.md`)
2. Run the client:
   ```bash
   python3 pc_client.py <deck_ip> -p 9090
   ```
   Replace `<deck_ip>` with the IP shown in the app
3. PC client will register and start receiving controller events
4. The virtual Steam Deck controller will appear on your PC

### To Stop:

1. Press **Steam Button** on Deck
2. Select **Quit** from the overlay
3. App exits, controller is released back to Steam Deck

## Configuration

The app uses a config file at: `~/.config/deck-controller-forwarder.conf`

You can edit it to change the port:

```
# Steam Deck Controller Forwarder Configuration
port=9090
```

## Troubleshooting

### App won't launch
- Make sure `launch.sh` is executable: `chmod +x launch.sh`
- Check that pygame is installed: `pip install pygame`

### Controller not found
- Make sure you're not in Desktop Mode when launching
- Controller should show as "Microsoft X-Box 360 pad" in Gaming Mode

### PC not receiving events
- Check firewall allows UDP port 9090
- Verify both devices on same network
- Check IP address shown in app matches what PC client is connecting to

### Can't exit app
- Press Steam button
- If that doesn't work, use the power button menu → Exit Game

## How It Works

1. App finds the Steam Deck's gamepad device (Xbox 360 pad interface)
2. Grabs exclusive access (prevents Deck from processing button presses)
3. Starts UDP server listening on port 9090
4. Waits for PC client to register
5. Forwards all controller events to connected PC client
6. On exit, releases grab and cleans up

## Files

- `deck_controller_app.py` - Main application
- `launch.sh` - Launcher script for Steam
- `README.md` - This file

## Credits

Based on evdev event forwarding and uinput virtual device creation.
Inspired by decktation plugin's controller detection logic.

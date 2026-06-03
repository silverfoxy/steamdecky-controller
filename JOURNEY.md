# Development Journey: Steam Deck Controller Forwarding

This document chronicles the approaches tried, lessons learned, and why we ended up with USB/IP.

## The Goal

Forward the Steam Deck's physical controller inputs to a PC for game streaming and remote play scenarios.

## Approaches Tried

### 1. Direct Event Reading via Python (evdev)

**Idea:** Read controller events from `/dev/input` and forward them to the PC.

**Problems:**
- **Permission barriers:** Input devices require root access or special group membership
- **Steam Input interference:** Steam's input system actively grabs controller devices
- **Complex state management:** Would need to handle all button states, analog values, haptics
- **Reconstruction complexity:** PC side would need to recreate a virtual controller device

**Files:** `archive/decky-plugin-attempt/pc-client/pc_client.py`

**Lesson Learned:** Working around Steam Input's device ownership is fighting the system.

---

### 2. Decky Loader Plugin Approach

**Idea:** Create a Decky plugin to read controller state and send it to PC, with PC-side virtual device creation.

**What We Built:**
- Decky plugin skeleton with React frontend
- Python backend using evdev to read `/dev/input/event*`
- Attempted permission handling via `setup.sh`
- PC-side client to receive events

**Problems:**
- **Permission issues:** Even with group membership and udev rules, accessing input devices from plugin context is restricted
- **Steam Input lockout:** Steam Input grabs exclusive access to controller devices
- **Plugin isolation:** Decky plugins run in a sandboxed environment with limited system access
- **Complexity vs. value:** Building a full input forwarding system + virtual device creation is reinventing existing solutions

**Files:** See `archive/decky-plugin-attempt/`

**Key Discovery:** The `/dev/input/by-id/usb-*` symlinks revealed the Steam Deck controller is a **USB device** (VID: 28de, PID: 1205). This led to the USB/IP breakthrough.

**Lesson Learned:** Sometimes the metadata (USB device IDs) is more valuable than the data (input events).

---

### 3. USB/IP Solution (FINAL APPROACH)

**Idea:** Instead of reading events, just share the entire USB device over the network.

**Why It Works:**
- **Kernel-level solution:** No permission games, no fighting with Steam
- **Device-level sharing:** PC sees it as a real USB controller
- **Built into Linux:** No custom drivers or complex setup
- **Minimal overhead:** Direct USB protocol forwarding over TCP

**How It Works:**

1. **On Deck:**
   ```bash
   # Unbind controller from local driver
   usbip bind -b 3-3

   # Share via network
   usbipd -D
   ```

2. **On PC:**
   ```bash
   # Attach to remote USB device
   usbip attach -r <deck-ip> -b 3-3
   ```

3. **Result:** PC's kernel sees the controller as a local USB device

**Implementation Details:**

- **Device Discovery:** Use `usbip list -l` to get correct busid format (not `lsusb`)
- **Kernel Modules Required:**
  - Server (Deck): `usbip-core`, `usbip-host`
  - Client (PC): `vhci-hcd`
- **Nix Installation:** Required on Steam Deck since `usbip` isn't in default repos
- **Test Mode:** Can test locally via loopback (attach to 127.0.0.1)

**Challenges Overcome:**

1. **busid Format Mismatch:**
   - `lsusb` shows: "Bus 003 Device 002"
   - `usbip` needs: "3-3" (bus-port format)
   - **Solution:** Use `usbip list -l` for discovery

2. **sudo + Nix PATH Issues:**
   - Nix installs to `~/.nix-profile/bin/`
   - `sudo` doesn't inherit user PATH
   - **Solution:** Scripts use full paths to binaries

3. **Missing vhci-hcd Module:**
   - Client-side module not loaded by default
   - **Solution:** Added `modprobe vhci-hcd` to connection script

**Verification:**
- Tested in local loopback mode on Deck
- Controller remained functional through USB/IP tunnel
- Proves the approach works before testing PC connection

---

## Lessons Learned

### Technical

1. **Work with the kernel, not against it:** USB/IP leverages existing kernel infrastructure instead of fighting permissions
2. **Read the metadata:** The USB device IDs were hiding in plain sight in `/dev/input/by-id/`
3. **busid ≠ device number:** USB/IP uses a different addressing scheme than `lsusb`
4. **Test locally first:** Loopback testing validated the approach before network complexity

### Development Process

1. **Failed approaches teach you the domain:** The evdev and plugin attempts taught us about Steam Input, permissions, and device discovery
2. **Simplicity wins:** USB/IP is simpler than custom event forwarding + virtual device creation
3. **Use existing tools:** Don't rebuild what the kernel already provides
4. **Document the journey:** Future you (or others) will want to know why certain paths weren't taken

### Steam Deck Specific

1. **SteamOS uses immutable filesystem:** System packages reset on update, hence Nix for usbip
2. **Steam Input is aggressive:** It grabs controller devices exclusively
3. **The controller is just a USB device:** VID:28de PID:1205 - Valve Software Steam Deck Controller

---

## Why USB/IP Won

| Criteria | evdev | Decky Plugin | USB/IP |
|----------|-------|--------------|--------|
| Permissions | ❌ Root required | ❌ Sandboxed | ✅ Kernel handles it |
| Steam Input | ❌ Conflicts | ❌ Conflicts | ✅ Works below Steam |
| Complexity | ❌ High | ❌ Very High | ✅ Low |
| Latency | 🟡 Medium | 🟡 Medium | ✅ Low |
| Maintenance | ❌ Fragile | ❌ Plugin updates | ✅ Kernel stable |
| PC Setup | ❌ Virtual device | ❌ Virtual device | ✅ Native USB |

---

## Future Ideas

- **Auto-discovery:** Broadcast Deck IP via mDNS/Avahi
- **GUI control:** Simple on-screen toggle for sharing
- **Steamworks integration:** Official Steam Input forwarding API (wishful thinking)
- **Multiple controllers:** Share multiple USB devices simultaneously
- **Encryption:** USB/IP uses plain TCP, could tunnel through SSH

---

## Timeline

- **Day 1:** Direct evdev reading attempt - hit permission wall
- **Day 2:** Decky plugin approach - built skeleton, discovered USB device info
- **Day 3:** USB/IP discovery and successful local loopback test
- **Day 4:** PC scripts and documentation

---

## References

- [USB/IP Documentation](https://www.kernel.org/doc/html/latest/usb/usbip_protocol.html)
- [Steam Deck Hardware Info](https://www.steamdeck.com/en/tech)
- [Decky Loader](https://decky.xyz/)
- [Linux evdev API](https://www.kernel.org/doc/html/latest/input/input.html)

---

**TL;DR:** We tried to be clever with event reading and plugins, then realized the controller is just a USB device and the kernel already has a tool to share USB devices. Sometimes the obvious solution is the right one.

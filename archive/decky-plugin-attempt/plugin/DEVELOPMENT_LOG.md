# Steam Deck Controller Sharing Plugin - Development Log

## Original Goal
Create a Decky Loader plugin to share the Steam Deck's physical controller to a Linux PC via USB/IP over Wi-Fi.

## What We Accomplished

### 1. Fixed Plugin Loading Issues ✓
- **Root cause**: `"type": "module"` in package.json caused Decky to load the build as ES module instead of IIFE
- **Solution**: Removed `"type": "module"` field
- **Additional fixes**:
  - Downgraded Rollup v3 → v2.79 (to match working plugins)
  - Added default React import: `import React, { ... }` 
  - Updated TypeScript config with `esModuleInterop: true`
  - Changed from `resolve` to `{ nodeResolve }` import

### 2. Bundled USB/IP Binaries ✓
- Downloaded and bundled `usbip` and `usbipd` binaries from Arch package
- Bundled shared libraries (`libusbip.so*`) 
- Modified `main.py` to check plugin's `bin/` directory first
- Added `LD_LIBRARY_PATH` environment variable handling

### 3. Set Capabilities on Binaries ✓
- Used Linux capabilities instead of sudo (since Decky can't use sudo interactively)
- Set `cap_net_admin,cap_sys_admin` on binaries
- Created `setup_capabilities.sh` script

### 4. Plugin Successfully Detects Controller ✓
- Plugin finds Steam Deck controller at busid 3-3
- Vendor ID 28de (Valve) correctly detected
- `usbip list -l` works with bundled binaries

## Critical Issues Encountered

### Issue #1: Controller Unbinding Permissions
**Problem**: `usbip bind` requires unbinding device from current driver, which needs write access to `/sys/bus/usb/drivers/*/unbind`

**Attempted Solutions**:
- ❌ Sudo (Decky can't use sudo without TTY)
- ❌ Sudoers file with NOPASSWD (still requires TTY)
- ❌ Capabilities (insufficient for driver unbind)
- ⚠️ Udev rules (created but needs testing)

**Status**: Still failing with "unable to bind device on 3-3"

### Issue #2: Controller Stopped Working
**Problem**: During testing, controller became unbound and stopped functioning

**Solution**: 
- Created `restore_controller.sh` to reprobe device
- Rebooting Steam Deck restores functionality
- Demonstrates the risk of this approach

### Issue #3: UX Problem - Stopping Share
**Problem**: When controller is exported via USB/IP:
- Controller is unavailable on Steam Deck
- User can't use controller to click "Stop Sharing"

**Workaround**: Use touchscreen to stop sharing

## Key Technical Learnings

### USB/IP Architecture
```
Steam Deck Side:
1. Unbind device from current driver (e.g., xpad)
2. Bind device to usbip-host driver
3. Run usbipd daemon to listen for connections

PC Side:
1. Load vhci-hcd kernel module
2. Run: usbip attach -r <deck-ip> -b <busid>
3. Device appears as local USB device
```

### Permission Requirements
USB/IP operations need:
- `CAP_NET_ADMIN` - network operations
- `CAP_SYS_ADMIN` - system administration
- **Write access to sysfs unbind/bind files** ⚠️ (this is the blocker)

### Steam Deck Controller Architecture
- Device: busid 3-3, Vendor 28de:1205
- Not a simple USB driver binding (platform/HID driver)
- No `driver` symlink at device level (interfaces might have it)
- Unbinding affects all system controller functionality

## Alternative Design Options

### Option A: USB/IP with Touchscreen Control (Current Approach)
**Pros**:
- True USB device passthrough
- Works with any software expecting USB controller
- Clean separation (controller fully on PC or Deck)

**Cons**:
- ❌ Permission issues blocking implementation
- ⚠️ Controller unavailable on Deck while sharing
- ⚠️ Risk of breaking controller if something goes wrong
- Must use touchscreen to stop

**Remaining challenges**:
- Need to solve driver unbind permissions (udev rules or setuid wrapper)
- Need comprehensive testing to ensure controller rebinds reliably

### Option B: Input Event Forwarding
**How it works**:
```
Steam Deck:
1. Read controller events from /dev/input/eventX
2. Forward events over network (websocket/UDP)

PC:
1. Receive events
2. Create virtual uinput device
3. Inject events into virtual device
```

**Pros**:
- ✅ Controller stays functional on Deck
- ✅ No driver unbinding needed
- ✅ Safer - can't break controller
- ✅ Lower latency potential

**Cons**:
- Requires uinput on PC
- Need to handle device hotplug
- More complex event mapping
- Two controllers active simultaneously (might confuse games)

**Implementation**:
- Python backend: Use `evdev` library to read `/dev/input/eventX`
- Network: Use UDP for low latency
- PC side: Python script with `python-uinput` to create virtual device

### Option C: External USB Controllers Only
**How it works**:
- Only allow sharing externally plugged USB controllers
- Keep built-in controller untouched

**Pros**:
- ✅ Safe for built-in controller
- ✅ USB/IP works better with external devices
- ✅ Easier permission management

**Cons**:
- Requires user to have external controller
- Defeats original purpose (sharing Deck's controller)

### Option D: Hybrid Approach
**How it works**:
- Support both USB/IP (external controllers) and event forwarding (built-in)
- Auto-detect which method to use

**Pros**:
- Flexible
- Safe for built-in, powerful for external

**Cons**:
- Most complex implementation
- More code to maintain

## Scripts Created

| Script | Purpose | Status |
|--------|---------|--------|
| `download_usbip.sh` | Extract usbip binaries from Arch package | ✓ Working |
| `setup_capabilities.sh` | Set Linux capabilities on binaries | ✓ Working |
| `setup_udev.sh` | Create udev rules for USB permissions | Created, needs testing |
| `fix_permissions.sh` | Manually fix sysfs permissions | Created, needs testing |
| `restore_controller.sh` | Restore controller after unbinding | ✓ Working |
| `setup_sudo.sh` | Configure sudoers (abandoned) | ❌ Not viable |
| `cleanup_sudo.sh` | Remove sudoers config | Created |
| `copy.sh` | Deploy plugin to Decky | ✓ Working |
| `deploy.sh` | Build and deploy | ✓ Working |

## File Structure
```
plugin/
├── bin/              # Bundled usbip binaries
│   ├── usbip
│   └── usbipd
├── lib/              # Bundled shared libraries
│   ├── libusbip.so
│   ├── libusbip.so.0
│   └── libusbip.so.0.0.1
├── dist/             # Built frontend
│   └── index.js
├── src/              # Frontend source
│   └── index.tsx
├── main.py           # Backend plugin
├── plugin.json       # Plugin metadata
├── package.json      # Node dependencies (no "type": "module"!)
├── rollup.config.js  # Build config (Rollup 2.x, IIFE format)
└── tsconfig.json     # TypeScript config (esModuleInterop: true)
```

## Configuration Summary

### package.json
```json
{
  "name": "steamdecky-controller",
  "version": "1.0.0",
  // NO "type": "module" field!
  "devDependencies": {
    "rollup": "^2.79.0",
    "@rollup/plugin-commonjs": "^21.1.0",
    "@rollup/plugin-node-resolve": "^13.3.0",
    // ... version 2.x plugins
  }
}
```

### rollup.config.js
```javascript
import { nodeResolve } from "@rollup/plugin-node-resolve"; // Note: nodeResolve, not resolve

export default defineConfig({
  output: {
    format: "iife",  // Not "esm"!
    exports: "default",
    // NO "name" property
  }
});
```

### tsconfig.json
```json
{
  "compilerOptions": {
    "moduleResolution": "node",
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    // ...
  }
}
```

## Next Steps

### Short Term (Continue Current Approach)
1. Test udev rules from `setup_udev.sh`
2. If udev doesn't work, explore setuid wrapper
3. Add comprehensive error handling
4. Update UI with touchscreen instructions
5. Add auto-unbind on plugin unload

### Medium Term (Evaluate Alternatives)
1. Prototype Option B (Input Event Forwarding)
2. Benchmark latency comparison
3. User testing for both approaches
4. Decide on final design

### Long Term (Polish)
1. Add connection status indicators
2. Support multiple controllers
3. Add latency monitoring
4. Create installation guide
5. Publish to Decky Plugin Store

## Questions to Answer

1. **Permission solution**: Can we solve the unbind permission issue without root?
   - Udev rules might work
   - Setuid wrapper is risky but possible
   - Running a helper daemon as root?

2. **Design decision**: USB/IP vs Event Forwarding?
   - USB/IP: True USB passthrough, but risky for built-in controller
   - Event Forwarding: Safer, but need to handle both controllers being active

3. **User experience**: Is touchscreen control acceptable?
   - Or should we add SSH command support?
   - Web interface for PC to stop sharing?

## Resources

- Decky Loader Docs: https://github.com/SteamDeckHomebrew/decky-loader
- USB/IP Documentation: https://usbip.sourceforge.net/
- Linux Capabilities: https://man7.org/linux/man-pages/man7/capabilities.7.html
- evdev Python library: https://python-evdev.readthedocs.io/

## Conclusion

We made significant progress on the plugin infrastructure (loading, building, bundling), but hit a fundamental permission wall with USB/IP driver unbinding. The project is at a decision point: continue fighting the permission issues or pivot to a safer input forwarding approach.

**Recommendation**: Prototype Option B (Input Event Forwarding) to evaluate if it's a viable alternative before investing more time in solving USB/IP permissions.

---

## Update: Switched to evdev/uinput Approach (2026-05-30)

After hitting permission walls with USB/IP, we pivoted to **Option B: Input Event Forwarding**.

### Implementation

**Architecture**:
```
Steam Deck:                     Network (UDP)                PC:
┌──────────────────┐           ┌─────────┐         ┌──────────────────┐
│  /dev/input/eventX│──read───>│ Forward │───UDP──>│  Receive events  │
│ (real controller) │           │ events  │         │  Create uinput   │
└──────────────────┘           └─────────┘         │  virtual device  │
                                                    └──────────────────┘
```

**Files Created**:
- `controller_forwarder.py` - Deck side, reads evdev and forwards over UDP
- `pc_client.py` - PC side, receives events and creates virtual uinput device

**Advantages**:
- ✅ No driver unbinding needed
- ✅ No permission issues
- ✅ Controller stays working on Deck
- ✅ Low latency (UDP)
- ✅ Virtual device looks identical to real one

**PC Setup**:
```bash
# Install uinput support
sudo apt install python3-uinput
sudo modprobe uinput

# Run client
python3 pc_client.py
```

**Deck Side**:
```bash
# Find your PC's IP
python3 controller_forwarder.py <pc-ip>
```

### Integration Complete! (2026-05-31)

Successfully integrated evdev/uinput into the Decky plugin:

**Backend Changes** (`main.py`):
- Removed all USB/IP code (usbipd, usbip, modules, binding)
- Added process management for `controller_forwarder.py`
- New API methods:
  - `check_deps()`: Checks for evdev and forwarder script
  - `start_sharing(pc_ip, port)`: Starts forwarder subprocess
  - `stop_sharing()`: Stops forwarder gracefully
  - `get_status()`: Returns running state, IPs, port

**Frontend Changes** (`src/index.tsx`):
- Added PC IP address input field
- Added port configuration (default: 9090)
- Updated status display (removed busid, added pc_ip)
- Changed instructions from USB/IP commands to PC client setup
- Updated note: controller works on both devices!
- Fixed TypeScript issues (VFC → FC, ButtonItem label prop)

**Other Changes**:
- Updated `plugin.json`: Changed description and tags
- Updated `deploy.sh`: Copies `controller_forwarder.py`
- Created comprehensive `README.md` with setup and troubleshooting

**Build Status**:
- ✅ TypeScript compiles cleanly
- ✅ Plugin structure validated
- ✅ Ready for deployment and testing

**Next Steps**:
1. Deploy to Decky Loader
2. Test end-to-end (Deck → PC)
3. Verify controller detection on both sides
4. Test in actual games
5. Gather feedback and iterate

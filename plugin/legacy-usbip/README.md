# Legacy USB/IP Files

These files are from the original USB/IP approach, which has been **replaced** by the evdev/uinput method.

## Why We Moved Away from USB/IP

The USB/IP approach had fundamental issues:
- Required root permissions to unbind USB drivers
- Controller became unavailable on Steam Deck while sharing
- Risk of breaking the controller if something went wrong
- Complex permission management (capabilities, udev rules, etc.)

See `../DEVELOPMENT_LOG.md` for the full story.

## What's Here

### Scripts
- `download_usbip.sh` - Downloaded USB/IP binaries from Arch package
- `setup_capabilities.sh` - Set Linux capabilities on binaries
- `setup_udev.sh` - Created udev rules for USB permissions
- `fix_permissions.sh` - Manually fixed sysfs permissions
- `restore_controller.sh` - Restored controller after unbinding
- `setup_sudo.sh` - Configured sudoers (abandoned approach)

### Binaries & Libraries
- `bin/` - USB/IP tools (usbip, usbipd)
- `lib/` - Shared libraries (libusbip.so.*)

## Current Approach

We now use **evdev/uinput** instead:
- Deck: Reads controller events with evdev, forwards over UDP
- PC: Receives events, creates virtual controller with uinput
- Controller works on **both** devices simultaneously
- No permission issues, no driver unbinding

See the main README for current setup instructions.

## Should You Use These?

**No.** These files are kept only for reference and historical purposes.

If you're setting up the plugin for the first time, use the evdev approach documented in the main README.

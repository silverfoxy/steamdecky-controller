# Archive: Previous Approaches

This directory contains code from approaches that were tried but ultimately not pursued.

## Contents

### `decky-plugin-attempt/`

A Decky Loader plugin attempt to read controller events and forward them to a PC.

**What's in here:**
- `plugin/` - Decky plugin with React UI and Python backend
- `pc-client/` - PC-side client to receive and recreate controller events

**Why it didn't work:**
- Permission barriers accessing `/dev/input` devices
- Steam Input's exclusive device grabbing
- Plugin sandboxing limitations
- Unnecessary complexity compared to USB/IP solution

**What we learned:**
- Discovered the controller's USB device IDs (28de:1205)
- Understood Steam Input's device management
- Realized we were fighting the system instead of leveraging it

### `experiments/`

Various testing scripts and experimental code:
- Event monitoring scripts
- Device discovery tests
- Trackpad input tests

**Purpose:** These were used to understand how the Steam Deck's input system works.

## Why These Are Archived

These approaches were valuable learning experiences but are superseded by the USB/IP solution, which:
- Works at the kernel level (no permission issues)
- Doesn't conflict with Steam Input
- Is simpler and more maintainable
- Uses standard Linux tools

## Historical Value

Keep these around because:
1. They show the evolution of the project
2. The plugin code could be useful for other Decky projects
3. The event reading code demonstrates Steam Deck input internals
4. Future contributors can learn from what didn't work

See [JOURNEY.md](../JOURNEY.md) for the full development story.

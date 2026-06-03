#!/bin/bash
# Script to extract usbip binaries and libraries from Arch package

set -e

TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo "Downloading usbip package..."
curl -L -o usbip.pkg.tar.zst "https://archive.archlinux.org/packages/u/usbip/usbip-6.6-1-x86_64.pkg.tar.zst"

echo "Extracting package..."
tar -xf usbip.pkg.tar.zst

# Create bin and lib directories
mkdir -p "$OLDPWD/bin"
mkdir -p "$OLDPWD/lib"

# Copy binaries
cp usr/bin/usbip "$OLDPWD/bin/" 2>/dev/null || cp usr/sbin/usbip "$OLDPWD/bin/" || true
cp usr/bin/usbipd "$OLDPWD/bin/" 2>/dev/null || cp usr/sbin/usbipd "$OLDPWD/bin/" || true

# Copy shared libraries
find usr/lib -name "libusbip*.so*" -exec cp {} "$OLDPWD/lib/" \; 2>/dev/null || true

# Make executable
chmod +x "$OLDPWD/bin/"* 2>/dev/null || true
chmod +x "$OLDPWD/lib/"*.so* 2>/dev/null || true

cd "$OLDPWD"
rm -rf "$TEMP_DIR"

echo "Done! Files extracted:"
ls -lh bin/ lib/

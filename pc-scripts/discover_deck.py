#!/usr/bin/env python3
"""Find an actively sharing Steam Deck on the local network using Avahi."""

import ipaddress
import re
import shlex
import subprocess
import sys

SERVICE_TYPE = '_steamy-controller._tcp'
BUSID = re.compile(r'\d+-\d+(?:\.\d+)*\Z')


class DiscoveryError(Exception):
    pass


def parse_records(output):
    """Accept only resolved IPv4 advertisements for our USB/IP controller."""
    found = set()
    for line in output.splitlines():
        # Avahi's parsable output has semicolon-separated service columns,
        # but all quoted TXT key/value pairs share one final column.
        parts = line.split(';', 9)
        if len(parts) != 10 or parts[0] != '=' or parts[2] != 'IPv4' or parts[4] != SERVICE_TYPE:
            continue
        try:
            ip = str(ipaddress.IPv4Address(parts[7]))
        except ipaddress.AddressValueError:
            continue
        if parts[8] != '3240':
            continue
        try:
            items = shlex.split(parts[9])
        except ValueError:
            continue
        txt = dict(item.split('=', 1) for item in items if '=' in item)
        busid = txt.get('busid', '')
        if txt.get('vidpid', '').lower() != '28de:1205' or not BUSID.fullmatch(busid):
            continue
        found.add((ip, busid))
    return sorted(found)


def discover():
    try:
        result = subprocess.run(
            ['avahi-browse', '--resolve', '--terminate', '--parsable', '--no-db-lookup',
             SERVICE_TYPE], capture_output=True, text=True, timeout=10)
    except FileNotFoundError as exc:
        raise DiscoveryError('Install avahi-utils for automatic discovery, or pass a Deck IP.') from exc
    except subprocess.TimeoutExpired as exc:
        raise DiscoveryError('Avahi discovery timed out; pass a Deck IP instead.') from exc
    if result.returncode:
        raise DiscoveryError('Avahi discovery failed; check that avahi-daemon is running '
                             'or pass a Deck IP.')
    decks = parse_records(result.stdout)
    if not decks:
        raise DiscoveryError('No Steam Deck is advertising controller sharing; '
                             'start sharing on the Deck or pass its IP.')
    if len(decks) > 1:
        choices = ', '.join(f'{ip} (bus {busid})' for ip, busid in decks)
        raise DiscoveryError(f'Multiple Steam Decks found: {choices}. Pass the desired IP and bus ID.')
    return decks[0]


if __name__ == '__main__':
    try:
        print(*discover(), sep='\t')
    except DiscoveryError as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)

import os
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def executable(path, body):
    path.write_text('#!/bin/sh\n' + body)
    path.chmod(0o755)


def run_client(tmp_path, advertisement, *arguments):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    log = tmp_path / 'commands'
    executable(bin_dir / 'avahi-browse', f'printf \'%s\\n\' \'{advertisement}\'\n')
    executable(bin_dir / 'sudo', 'printf "%s\\n" "$*" >> "$TEST_COMMANDS"\n"$@"\n')
    executable(bin_dir / 'modprobe', 'exit 0\n')
    executable(bin_dir / 'usbip', '''if [ "$1" = list ]; then
  printf '%s\\n' ' - 3-3.2: Valve Software : Steam Deck Controller (28de:1205)'
  exit 0
fi
if [ "$1" = attach ]; then exit 0; fi
exit 1
''')
    env = dict(os.environ, PATH=str(bin_dir) + ':' + os.environ['PATH'], TEST_COMMANDS=str(log))
    result = subprocess.run(['bash', str(ROOT / 'pc-scripts' / 'pc-connect.sh'), *arguments],
                            capture_output=True, text=True, env=env, timeout=10)
    return result, log.read_text() if log.exists() else ''


def test_auto_discover_uses_advertised_busid(tmp_path):
    line = ('=;wlan0;IPv4;Steamy Controller;_steamy-controller._tcp;local;'
            'deck.local;192.168.1.19;3240;"busid=3-3.2" "vidpid=28de:1205"')
    result, commands = run_client(tmp_path, line)
    assert result.returncode == 0, result.stderr + result.stdout
    assert 'usbip attach -r 192.168.1.19 -b 3-3.2' in commands


def test_multiple_decks_do_not_attach_automatically(tmp_path):
    line = ('=;wlan0;IPv4;Steamy Controller;_steamy-controller._tcp;local;'
            'deck.local;192.168.1.19;3240;"busid=3-3.2" "vidpid=28de:1205"')
    other = line.replace('192.168.1.19', '192.168.1.20')
    result, commands = run_client(tmp_path, line + '\n' + other)
    assert result.returncode != 0
    assert 'Multiple Steam Decks' in result.stderr
    assert 'usbip attach' not in commands


def test_manual_ip_still_works_without_avahi(tmp_path):
    result, commands = run_client(tmp_path, '', '192.168.1.19', '3-3.2')
    assert result.returncode == 0, result.stderr + result.stdout
    assert 'usbip attach -r 192.168.1.19 -b 3-3.2' in commands


def test_remote_device_mismatch_is_not_attached(tmp_path):
    line = ('=;wlan0;IPv4;Steamy Controller;_steamy-controller._tcp;local;'
            'deck.local;192.168.1.19;3240;"busid=3-9";"vidpid=28de:1205"')
    result, commands = run_client(tmp_path, line)
    assert result.returncode != 0
    assert 'usbip attach' not in commands

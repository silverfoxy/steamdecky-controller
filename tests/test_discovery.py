import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / 'pc-scripts' / 'discover_deck.py'


def load_discovery():
    spec = importlib.util.spec_from_file_location('discover_deck', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(ip='192.168.1.10', busid='3-3', *, interface='eth0', protocol='IPv4',
           vidpid='28de:1205', port='3240'):
    return (f'=;{interface};{protocol};Steamy Controller;_steamy-controller._tcp;local;'
            f'deck.local;{ip};{port};"busid={busid}" "vidpid={vidpid}"')


def test_one_valid_deck_is_discovered():
    module = load_discovery()
    with patch.object(module.subprocess, 'run') as run:
        run.return_value.stdout = record() + '\n'
        run.return_value.returncode = 0
        assert module.discover() == ('192.168.1.10', '3-3')
        assert run.call_args.args[0][:2] == ['avahi-browse', '--resolve']


def test_duplicate_interface_does_not_create_duplicate_deck():
    module = load_discovery()
    with patch.object(module.subprocess, 'run') as run:
        run.return_value.stdout = record(interface='wlan0') + '\n' + record() + '\n'
        run.return_value.returncode = 0
        assert module.discover() == ('192.168.1.10', '3-3')


def test_multiple_decks_are_not_silently_chosen():
    module = load_discovery()
    with patch.object(module.subprocess, 'run') as run:
        run.return_value.stdout = record() + '\n' + record('192.168.1.11', '3-3.2')
        run.return_value.returncode = 0
        with pytest.raises(module.DiscoveryError, match='Multiple'):
            module.discover()


@pytest.mark.parametrize('line', [
    record(vidpid='1234:5678'), record(busid='3-3;--evil'),
    record(ip='not-an-ip'), record(port='22'), record(protocol='IPv6'),
])
def test_untrusted_or_unusable_records_are_ignored(line):
    module = load_discovery()
    with patch.object(module.subprocess, 'run') as run:
        run.return_value.stdout = line
        run.return_value.returncode = 0
        with pytest.raises(module.DiscoveryError, match='No Steam Deck'):
            module.discover()


def test_avahi_failure_has_actionable_error():
    module = load_discovery()
    with patch.object(module.subprocess, 'run', side_effect=FileNotFoundError):
        with pytest.raises(module.DiscoveryError, match='avahi-utils'):
            module.discover()

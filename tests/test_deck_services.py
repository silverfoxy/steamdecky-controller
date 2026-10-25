import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deck_services


@pytest.mark.parametrize('line, expected', [
    (' - busid 3-3.2 (28de:1205)', '3-3.2'),
    (' - busid 3-3 (28de:1205)', '3-3'),
    (' - busid 3-3.2 (1234:5678)', None),
])
def test_controller_busid_keeps_hub_port_suffix(line, expected):
    assert deck_services.parse_controller_busid(line) == expected


def test_advertisement_lives_only_while_sharing():
    process = Mock()
    process.poll.return_value = None
    with patch.object(deck_services.shutil, 'which', return_value='/usr/bin/avahi-publish-service'), \
         patch.object(deck_services.subprocess, 'Popen', return_value=process) as popen:
        advertiser = deck_services.DiscoveryAdvertiser()
        assert advertiser.start('3-3.2')
        command = popen.call_args.args[0]
        assert command[-4:] == ['_steamy-controller._tcp', '3240', 'busid=3-3.2', 'vidpid=28de:1205']
        assert advertiser.start('3-3.2')
        assert popen.call_count == 1
        advertiser.stop()
        process.terminate.assert_called_once()
        process.wait.assert_called_once()


def test_advertisement_gracefully_skips_when_avahi_absent():
    with patch.object(deck_services.shutil, 'which', return_value=None):
        assert not deck_services.DiscoveryAdvertiser().start('3-3')


def test_nix_publisher_found_even_when_steam_omits_nix_from_path(tmp_path):
    binary = tmp_path / '.nix-profile/bin/avahi-publish-service'
    binary.parent.mkdir(parents=True)
    binary.write_text('')
    binary.chmod(0o755)
    process = Mock()
    process.poll.return_value = None
    with patch.dict(os.environ, HOME=str(tmp_path)), \
         patch.object(deck_services.shutil, 'which', return_value=None), \
         patch.object(deck_services.subprocess, 'Popen', return_value=process) as popen:
        assert deck_services.DiscoveryAdvertiser().start('3-3')
        assert popen.call_args.args[0][0] == str(binary)


def test_sleep_lock_is_reacquired_if_inhibitor_exits():
    dead = Mock()
    dead.poll.return_value = 1
    live = Mock()
    live.poll.return_value = None
    with patch.object(deck_services.shutil, 'which', side_effect=lambda cmd: '/usr/bin/' + cmd), \
         patch.object(deck_services.subprocess, 'Popen', side_effect=[dead, live]) as popen, \
         patch.object(deck_services.time, 'sleep'):
        inhibitor = deck_services.SleepInhibitor()
        assert not inhibitor.start()
        assert inhibitor.ensure_active()
        assert '--what=idle:sleep' in popen.call_args.args[0]
        inhibitor.stop()
        live.terminate.assert_called_once()


def test_advertisement_recovers_after_publisher_exit():
    dead = Mock()
    dead.poll.return_value = 1
    live = Mock()
    live.poll.return_value = None
    with patch.object(deck_services.shutil, 'which', return_value='/usr/bin/avahi-publish-service'), \
         patch.object(deck_services.subprocess, 'Popen', side_effect=[dead, live]) as popen:
        advertiser = deck_services.DiscoveryAdvertiser()
        assert not advertiser.start('3-3')
        assert advertiser.ensure_active('3-3')
        assert popen.call_count == 2

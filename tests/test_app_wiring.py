"""Narrow wiring guards: the vendored Kivy lacks compiled modules on this host."""

import ast
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / 'deck-controller-gui.py'
TREE = ast.parse(SOURCE.read_text())
APP = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == 'ControllerApp')


def calls(method):
    node = next(n for n in APP.body if isinstance(n, ast.FunctionDef) and n.name == method)
    return {ast.unparse(n.func) for n in ast.walk(node) if isinstance(n, ast.Call)}


def test_deck_advertises_only_after_successful_export():
    assert 'self.discovery.start' in calls('_do_start_sharing')
    assert 'self.discovery.stop' in calls('_do_stop_sharing')


def test_sharing_rechecks_idle_sleep_lock_and_publication():
    assert 'self.sleep_inhibitor.ensure_active' in calls('check_status')
    assert 'self.discovery.ensure_active' in calls('check_status')


def test_window_close_restores_controller_and_brightness():
    assert 'self.usbip.stop_sharing' in calls('on_stop')
    assert 'self.discovery.stop' in calls('on_stop')
    assert 'self.sleep_inhibitor.stop' in calls('on_stop')
    assert 'self.brightness.restore' in calls('on_stop')

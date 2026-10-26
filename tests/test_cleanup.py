"""Exercise app cleanup methods without importing the incomplete vendored Kivy."""

import ast
import subprocess
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch


TREE = ast.parse((Path(__file__).resolve().parents[1] / 'deck-controller-gui.py').read_text())


def method(class_name, name, **globals_):
    owner = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    fn = next(n for n in owner.body if isinstance(n, ast.FunctionDef) and n.name == name)
    scope = {'logger': Mock(), **globals_}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
                 '<extracted-app-method>', 'exec'), scope)
    return scope[name]


def test_usbip_profile_symlinks_resolve_to_authorized_binaries(tmp_path):
    store = tmp_path / 'store' / 'bin'
    store.mkdir(parents=True)
    for name in ('usbip', 'usbipd'):
        (store / name).touch()
    profile = tmp_path / '.nix-profile' / 'bin'
    profile.parent.mkdir()
    profile.symlink_to(store, target_is_directory=True)
    with patch.object(Path, 'home', return_value=tmp_path):
        binary = method('USBIPController', 'find_usbip', Path=Path, Optional=str)(Mock())
    assert binary == str(store / 'usbip')
    daemon = method('USBIPController', 'find_usbipd', Path=Path, Optional=str)(
        Mock(usbip_path=binary))
    assert daemon == str(store / 'usbipd')


def test_stop_only_unbinds_this_apps_device():
    controller = Mock(current_busid='3-3.2')
    controller.get_bound_devices.return_value = ['3-3.2', '4-2']
    controller.unbind_device.return_value = True
    result = method('USBIPController', 'stop_sharing')(controller)
    assert result[0] is True
    controller.unbind_device.assert_called_once_with('3-3.2')
    controller.get_bound_devices.assert_not_called()
    controller.stop_daemon.assert_not_called()
    assert controller.current_busid is None


def test_failed_unbind_does_not_claim_restoration_or_drop_identity():
    controller = Mock(current_busid='3-3.2')
    controller.get_bound_devices.return_value = ['3-3.2']
    controller.unbind_device.return_value = False
    success, message = method('USBIPController', 'stop_sharing')(controller)
    assert not success
    assert '3-3.2' in message
    assert controller.current_busid == '3-3.2'
    controller.stop_daemon.assert_not_called()


def test_partial_restore_retries_probe_without_repeating_unbind():
    state = {'bound': True, 'probe_fail': True, 'unbind_calls': 0, 'probe_calls': 0}

    class FakePath:
        def __init__(self, value):
            self.value = value
        def __truediv__(self, name):
            return self
        def exists(self):
            return state['bound']

    def run(command, **kwargs):
        if command[-1].endswith('/unbind'):
            state['unbind_calls'] += 1
            if not state['bound']:
                raise subprocess.CalledProcessError(1, command)
            state['bound'] = False
        elif command[-1].endswith('/drivers_probe'):
            state['probe_calls'] += 1
            if state['probe_fail']:
                state['probe_fail'] = False
                raise subprocess.CalledProcessError(1, command)
        return Mock()

    restore = method('USBIPController', 'unbind_device', Path=FakePath,
                     subprocess=Mock(run=run, CalledProcessError=subprocess.CalledProcessError))
    assert not restore(Mock(), '3-3.2')
    assert restore(Mock(), '3-3.2')
    assert state['unbind_calls'] == 1
    assert state['probe_calls'] == 2


def test_failed_stop_keeps_sleep_lock_and_allows_retry():
    app = Mock(sharing=True)
    dim_timer, off_timer = app.dim_timer, app.screen_off_timer
    app.usbip.stop_sharing.return_value = (False, 'cannot restore')
    method('ControllerApp', '_do_stop_sharing')(app)
    assert app.sharing is True
    app.sleep_inhibitor.stop.assert_not_called()
    app.discovery.stop.assert_not_called()
    assert app.stop_btn.disabled is False
    dim_timer.cancel.assert_called_once()
    off_timer.cancel.assert_called_once()
    assert app.dim_timer is None and app.screen_off_timer is None


def test_exit_does_not_close_if_controller_restore_fails():
    app = Mock(sharing=True)
    app._do_stop_sharing.side_effect = lambda: None
    method('ControllerApp', 'exit_app')(app, None)
    app.stop.assert_not_called()


def test_direct_window_close_is_cancelled_if_restore_fails():
    app = Mock(sharing=True)
    assert method('ControllerApp', 'on_request_close')(app, source='keyboard') is True
    app.stop.assert_not_called()


def test_window_close_failure_does_not_release_inhibitor():
    app = Mock(sharing=True)
    app.usbip.stop_sharing.return_value = (False, 'cannot restore')
    method('ControllerApp', 'on_stop')(app)
    app.sleep_inhibitor.stop.assert_not_called()
    app.brightness.restore.assert_called_once()


def test_idle_dimming_never_switches_display_off():
    app = Mock(sharing=True)
    clock = Mock()
    method('ControllerApp', '_dim_then_schedule_off', Clock=clock)(app)
    app.brightness.dim.assert_called_once()
    app.brightness.screen_off.assert_not_called()
    clock.schedule_once.assert_not_called()
    assert app.dim_timer is None


def test_wake_redraws_even_when_app_did_not_dim_display():
    app = Mock(sharing=True, restore_error=None)
    window, clock = Mock(), Mock()
    dim_timer, off_timer = app.dim_timer, app.screen_off_timer
    method('ControllerApp', 'wake_screen', Window=window, Clock=clock)(app)
    app.brightness.restore.assert_called_once()
    app.root.canvas.ask_update.assert_called_once()
    window.canvas.ask_update.assert_called_once()
    dim_timer.cancel.assert_called_once()
    off_timer.cancel.assert_called_once()
    assert app.screen_off_timer is None
    clock.schedule_once.assert_called_once()


def test_focus_recovery_only_runs_on_focus_gain():
    app = Mock()
    focus = method('ControllerApp', 'on_window_focus')
    focus(app, None, False)
    app.wake_screen.assert_not_called()
    focus(app, None, True)
    app.wake_screen.assert_called_once()


def test_restore_failure_stays_visible_after_touch():
    app = Mock(sharing=True, restore_error='retry required')
    clock = Mock()
    method('ControllerApp', 'wake_screen', Window=Mock(), Clock=clock)(app)
    app.brightness.restore.assert_called_once()
    clock.schedule_once.assert_not_called()

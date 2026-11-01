"""Normal MPV presentation via public saved geometry and nonactivating startup.

First prove the synthetic saved offscreen position on an inactive desktop. Only
then launch that same normal binary offscreen on the input desktop, without OS
input, window movement, activation requests or a diagnostic transport.
"""
import argparse
import atexit
import ctypes
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import uuid

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / 'tools/windows-player'))
from isolated_desktop import IsolatedProcess, input_desktop, u, k

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mode', choices=['private', 'offscreen', 'private-playback'], required=True)
parser.add_argument('--case', required=True)
parser.add_argument('--fixture', type=Path, required=True)
parser.add_argument('--package', type=Path, required=True)
parser.add_argument('--scratch-root', type=Path, required=True)
parser.add_argument('--geometry-source', type=Path, required=True)
parser.add_argument('--placement-proof', type=Path, required=True)
parser.add_argument('--qt-sha256', required=True)
parser.add_argument('--verify-app-icon',action='store_true',help='Read the packaged PE icon and the actual owned native window icon')
args = parser.parse_args()
root = args.scratch_root.resolve()
assert root.parent == Path('D:/Temp') and root.name.startswith('vlc-s8-')
root.mkdir(exist_ok=True)
assert re.fullmatch(r'normal-presentation-[a-z0-9-]+', args.case)
scratch = root / args.case
assert not scratch.exists() and args.fixture.is_file()
package = args.package.resolve()
assert package.drive.upper() in ('D:', 'E:')
expected_qt = args.qt_sha256
assert re.fullmatch('[0-9a-f]{64}', expected_qt)
assert hashlib.sha256((package / 'plugins/gui/libqt_plugin.dll').read_bytes()).hexdigest() == expected_qt

geometry_source = args.geometry_source
encoded = next(line.split('=', 1)[1] for line in geometry_source.read_text(encoding='utf-8').splitlines() if line.startswith('geometry='))
# QSettings quotes the entire INI value when its binary payload has a delimiter.
if encoded.startswith('"'):
    assert encoded.endswith('"')
    encoded = encoded[1:-1]
assert encoded.startswith('@ByteArray(') and encoded.endswith(')')
data = bytearray()
payload = encoded[len('@ByteArray('):-1]
position = 0
escapes = {'0': 0, 'a': 7, 'b': 8, 'f': 12, 'n': 10, 'r': 13, 't': 9, 'v': 11, '\\': 92}
escapes['"'] = 34
while position < len(payload):
    character = payload[position]
    position += 1
    if character != '\\':
        data.extend(character.encode('latin1'))
        continue
    character = payload[position]
    position += 1
    if character == 'x':
        match = re.match('[0-9a-fA-F]+', payload[position:])
        assert match
        value = int(match.group(), 16)
        assert value <= 255
        data.append(value)
        position += len(match.group())
    else:
        data.append(escapes[character])
assert struct.unpack_from('>IBB', data) == (0x1D94200, 1, 0)
name_bytes = struct.unpack_from('>I', data, 6)[0]
screen = bytes(data[10:10 + name_bytes]).decode('utf-16-be')
offset = 10 + name_bytes + 8 + 16
assert len(data) == offset + 8 + 16 + 2
saved_geometry = bytes(data[:offset]) + struct.pack('>6iBB', 20000, 0, 20000, 0, 21279, 719, 0, 0)
geometry_hash = hashlib.sha256(saved_geometry).hexdigest()
if args.mode == 'offscreen':
    proof = json.loads(args.placement_proof.read_text())
    assert proof['geometry_verified'] and proof['qt_plugin_sha256'] == expected_qt and proof['saved_geometry_sha256'] == geometry_hash

scratch.mkdir()
runtime = scratch / 'runtime'
shutil.copytree(package, runtime)
portable = runtime / 'portable'
assert not any(portable.iterdir())
(portable / 'vlc').mkdir()
(portable / 'vlc/vlc-qt-interface.ini').write_text('[General]\ngeometry=@ByteArray('
    + ''.join('\\x%02x' % byte for byte in saved_geometry) + ')\n', encoding='ascii', newline='\n')
for name in ('tmp', 'qml', 'evidence'):
    (scratch / name).mkdir()
evidence = scratch / 'evidence'
environment = {key: value for key, value in os.environ.items() if not key.startswith('VLC_PLAYER_DIAGNOSTICS')}
environment.pop('VLC_PLUGIN_PATH', None)
environment.update(TEMP=str(scratch / 'tmp'), TMP=str(scratch / 'tmp'), VLC_DATA_PATH=str(runtime),
    VLC_USERDATA_PATH=str(portable), QML_DISK_CACHE_PATH=str(scratch / 'qml'),
    QT_DISABLE_SHADER_DISK_CACHE='1', QSG_RHI_DISABLE_SHADER_DISK_CACHE='1', QT_FORCE_STDERR_LOGGING='1',
    # The saved native fixture was recorded with this process-local DPI policy.
    # A different DPR makes QVLCTools reject its geometry and center the window.
    QSG_INFO='1', QT_ENABLE_HIGHDPI_SCALING='0', QT_FONT_DPI='96', QT_SCALE_FACTOR='1',
    QT_IM_MODULES='none', QT_IM_MODULE='none')
environment.pop('QT_SCREEN_SCALE_FACTORS', None)
command = [str(runtime / 'vlc.exe'), '--qt-playback-engine=mpv', '--intf=qt', '--no-one-instance',
    '--restore-playback-pos=0', '--no-save-recentplay', '--no-qt-privacy-ask', '--no-qt-updates-notif',
    '--no-metadata-network-access', '--no-qt-video-autoresize', '--no-video-title-show',
    '--qt-auto-raise=0', '--no-qt-system-tray', '--qt-notification=0',
    '--no-volume-save', '--mmdevice-volume=0', '--play-and-exit',
    '--file-logging', '--log-verbose=2', '--logfile=' + str(evidence / 'native-ui.log'), str(args.fixture.resolve())]

u.GetForegroundWindow.restype = W.HWND
u.GetWindowThreadProcessId.argtypes = [W.HWND, ctypes.POINTER(W.DWORD)]
u.GetWindowRect.argtypes = [W.HWND, ctypes.POINTER(W.RECT)]
u.IsWindowVisible.argtypes = [W.HWND]
u.SetThreadDpiAwarenessContext.argtypes = [W.HANDLE]
u.SetThreadDpiAwarenessContext.restype = W.HANDLE
window_callback = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
u.EnumDesktopWindows.argtypes = [W.HANDLE, window_callback, W.LPARAM]
monitor_callback = ctypes.WINFUNCTYPE(W.BOOL, W.HANDLE, W.HDC, ctypes.POINTER(W.RECT), W.LPARAM)
u.EnumDisplayMonitors.argtypes = [W.HDC, ctypes.POINTER(W.RECT), monitor_callback, W.LPARAM]
k.FindFirstChangeNotificationW.argtypes = [W.LPCWSTR, W.BOOL, W.DWORD]
k.FindFirstChangeNotificationW.restype = W.HANDLE
k.FindNextChangeNotification.argtypes = [W.HANDLE]
k.FindCloseChangeNotification.argtypes = [W.HANDLE]
k.WaitForMultipleObjects.argtypes = [W.DWORD, ctypes.POINTER(W.HANDLE), W.BOOL, W.DWORD]
k.WaitForMultipleObjects.restype = W.DWORD

monitors = []
@monitor_callback
def monitor(handle, dc, rectangle, parameter):
    value = rectangle.contents
    monitors.append([value.left, value.top, value.right, value.bottom])
    return True
previous_dpi = u.SetThreadDpiAwarenessContext(W.HANDLE(-4))
assert previous_dpi
try:
    assert u.EnumDisplayMonitors(None, None, monitor, 0)
finally:
    assert u.SetThreadDpiAwarenessContext(previous_dpi)
if args.mode == 'offscreen':
    assert monitors == proof['monitors'], 'Re-prove saved geometry after a display configuration change'
desktop_before = input_desktop()
observed_windows = []
foreground_owned = False
result = {'schema': 'vlc_redesign.s8_normal_presentation.v1', 'mode': args.mode, 'passed': False,
    'qt_plugin_sha256': expected_qt, 'saved_geometry_sha256': geometry_hash, 'saved_screen': screen,
    'monitors': monitors, 'scope': 'Public app-owned synthetic saved geometry; no desktop/input control, no diagnostic hooks',
    'test_only_input_context': 'QT_IM_MODULES=none; QT_IM_MODULE=none; process-local only, no OS input/language setting change'}
atexit.register(lambda: (scratch / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8'))
k.CreateEventW.argtypes = [W.LPVOID, W.BOOL, W.BOOL, W.LPCWSTR]
k.CreateEventW.restype = W.HANDLE
k.SetEvent.argtypes = [W.HANDLE]
identity = 'Local\\VLC-S8-' + uuid.uuid4().hex
event_names = [identity + suffix for suffix in ('-ready', '-bound', '-cancel')]
ready_event, bound_event, cancel_event = [k.CreateEventW(None, True, False, name) for name in event_names]
assert ready_event and bound_event and cancel_event
owned_desktop = None
desktop_name = None
if args.mode in {'private', 'private-playback'}:
    desktop_name = 'VLC-S2-' + uuid.uuid4().hex
    owned_desktop = u.CreateDesktopW(desktop_name, None, None, 0, 0x1FF, None)
    assert owned_desktop
observer_command = [sys.executable, '-B', str(repo / 'tools/windows-player/observe-normal-window.py'),
    '--binding', str(scratch / 'target.json'), '--result', str(scratch / 'window-events.json'),
    '--ready-event', event_names[0], '--bound-event', event_names[1], '--cancel-event', event_names[2],
    '--executable', str(runtime / 'vlc.exe')]
if args.verify_app_icon:
    from app_icon_checks import executable_icon
    result['executable_app_icon']=executable_icon(runtime/'vlc.exe',repo/'share/icons/vlc.ico')
    observer_command+=['--expected-icon',str(repo/'modules/gui/qt/pixmaps/redesign/app.png')]
observer = player = None
with (evidence / 'stdout').open('wb') as output, (evidence / 'stderr').open('wb') as error, \
        (evidence / 'observer.stdout').open('wb') as observer_output, (evidence / 'observer.stderr').open('wb') as observer_error:
    try:
        if args.mode in {'private', 'private-playback'}:
            observer = IsolatedProcess(observer_command, cwd=scratch, env=environment,
                stdout=observer_output, stderr=observer_error, desktop_name=desktop_name)
            observer_handle = observer.handle
        else:
            observer = subprocess.Popen(observer_command, cwd=scratch, env=environment,
                stdout=observer_output, stderr=observer_error, creationflags=subprocess.CREATE_NO_WINDOW)
            observer_handle = observer._handle
        readiness = (W.HANDLE * 2)(ready_event, observer_handle)
        assert k.WaitForMultipleObjects(2, readiness, False, 0xFFFFFFFF) == 0, 'Observer exited before hook readiness'
        if args.mode in {'private', 'private-playback'}:
            player = IsolatedProcess(command, cwd=runtime, env=environment, stdout=output, stderr=error,
                desktop_name=desktop_name)
        else:
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 4
            player = subprocess.Popen(command, cwd=runtime, env=environment, stdout=output, stderr=error,
                startupinfo=startup, creationflags=subprocess.CREATE_NO_WINDOW)
        result['pid'] = player.pid
        (scratch / 'target.json').write_text(json.dumps({'pid': player.pid, 'executable': str(runtime / 'vlc.exe')}))
        assert k.SetEvent(bound_event)
        result['exit_code'] = player.wait()
    finally:
        k.SetEvent(cancel_event)
        if observer:
            result['observer_exit_code'] = observer.wait()
        if owned_desktop:
            assert u.CloseDesktop(owned_desktop)
        for handle in (ready_event, bound_event, cancel_event):
            k.CloseHandle(handle)
        result['input_desktop_preserved'] = input_desktop() == desktop_before
window_events = json.loads((scratch / 'window-events.json').read_text())
observer_errors = window_events['errors']
assert result['observer_exit_code'] == 0 and not window_events.get('cancelled'), window_events
assert window_events['target_pid'] == result['pid'] and window_events['target_exit_code'] == result['exit_code']
observed_windows = list({tuple(event['bounds']) for event in window_events['events']
    if event['pid'] == result['pid'] and event['visible'] and event['bounds'][2] > event['bounds'][0]
    and event['bounds'][3] > event['bounds'][1]})
foreground_owned = any(event['foreground_owner'] for event in window_events['events'] if event['pid'] == result['pid'])
result['native_window_events'] = window_events
log = (evidence / 'native-ui.log').read_text(encoding='utf-8', errors='replace')
stderr = (evidence / 'stderr').read_text(encoding='utf-8', errors='replace')
offscreen = bool(observed_windows) and all(bounds[2] <= display[0] or bounds[0] >= display[2]
    or bounds[3] <= display[1] or bounds[1] >= display[3] for bounds in observed_windows for display in monitors)
checks = {'all_visible_owned_windows_offscreen': offscreen, 'no_observer_errors': not observer_errors, 'never_observed_foreground_owner': not foreground_owned,
    'input_desktop_preserved': result['input_desktop_preserved'], 'natural_eof': 'MPV natural EOF reached' in log,
    'resources_released': 'MPV native resources released' in log, 'qt_event_loop_finished': 'QApp exec() finished' in log,
    'no_competing_vlc_playback': not re.search(r'using (?:video |audio |spu )?decoder module|Received first picture', log),
    'no_mpv_runtime_errors': not any(re.search(r'\berror:\s+mpv/', line) for line in log.splitlines()),
    'no_qml_errors': not re.search(r'TypeError:|ReferenceError:|Binding loop detected|Cannot assign to non-existent property', log + stderr)}
if args.verify_app_icon:
    checks['native_flat_app_icon']=bool(window_events['native_window_icons'])
result['actual_picture_presented'] = 'MPV picture presented' in log
if args.mode == 'private':
    # Placement proof is confined to an inactive desktop. Qt windows must be
    # offscreen; only the identified OS input indicator may occupy another rect.
    visible = [event for event in window_events['events'] if event['visible']
        and event['bounds'][2] > event['bounds'][0] and event['bounds'][3] > event['bounds'][1]]
    player_events = [event for event in visible if event['class'].startswith('Qt')]
    others = [event for event in visible if not event['class'].startswith('Qt')]
    expected_indicator = str(Path(os.environ['SystemRoot']) / 'System32/InputSwitch.dll').lower()
    checks.pop('all_visible_owned_windows_offscreen')
    checks['all_visible_qt_windows_offscreen'] = bool(player_events) and all(
        event['bounds'][2] <= display[0] or event['bounds'][0] >= display[2]
        or event['bounds'][3] <= display[1] or event['bounds'][1] >= display[3]
        for event in player_events for display in monitors)
    checks['only_known_os_indicator_elsewhere'] = all(
        event['class'] in {'UAC Input Indicator', 'UAC_InputIndicatorOverlayWnd'}
        and event['class_module'].lower() == expected_indicator
        for event in others)
if args.mode == 'offscreen':
    checks['actual_picture_presented'] = result['actual_picture_presented']
if args.mode == 'private-playback':
    # Inactive desktops do not present a DXGI swapchain to the input desktop.
    # Verify lifecycle here; a caller must bind separate real presentation evidence
    # to identical downloaded binary hashes before claiming presentation acceptance.
    checks.pop('all_visible_owned_windows_offscreen')
    checks['inactive_desktop_owned'] = bool(desktop_name and desktop_name != desktop_before)
    result['scope'] = 'Normal playback lifecycle on an owned inactive desktop; no actual-picture claim, OS input or desktop switching'
result.update(checks=checks, observed_window_bounds=observed_windows, passed=result['exit_code'] == 0 and all(checks.values()))
(scratch / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
if args.mode == 'private' and result['passed']:
    assert not args.placement_proof.exists()
    args.placement_proof.write_text(json.dumps({'geometry_verified': True,
        'qt_plugin_sha256': expected_qt, 'saved_geometry_sha256': geometry_hash,
        'monitors': monitors, 'placement_receipt_sha256': hashlib.sha256((scratch / 'result.json').read_bytes()).hexdigest(),
        'scope': 'Only placement on an inactive desktop; actual-picture acceptance remains required offscreen'}, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'native_window_events'}), flush=True)
raise SystemExit(0 if result['passed'] else 1)

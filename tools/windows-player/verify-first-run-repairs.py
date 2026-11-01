"""M2 complete-workflow native acceptance on owned inactive Windows desktops.

Reuses the app-owned Qt event bridge and one isolated binary copy. Test profiles
are moved only after confirmed native exit; originals/delivered profiles are never
selected. No OS input, activation, desktop switching or execution-kill deadline.
"""
import argparse
import ctypes
from concurrent.futures import ThreadPoolExecutor
from ctypes import wintypes as W
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from PIL import Image
from app_icon_checks import executable_icon, window_icon
from isolated_desktop import IsolatedProcess, input_desktop, u, k

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--fixtures', type=Path, required=True)
parser.add_argument('--policies', type=Path, help='Native production-policy test executable from this same managed assembly')
parser.add_argument('--case', choices=['welcome', 'playback', 'subtitles', 'subtitles-mpv', 'preview', 'updates', 'playback-subtitles', 'seek-policy', 'integration-diagnostic', 'subtitle-tracks-diagnostic', 'all'], default='all')
args = parser.parse_args()
root, source, fixtures = args.root.resolve(), args.runtime.resolve(), args.fixtures.resolve()
assert root.parent.parent == Path('D:/Temp') and root.parent.name.startswith('vlc-s8-') and not root.exists()
assert fixtures.is_dir() and (source / 'portable').is_dir() and not any((source / 'portable').iterdir())
plugin = source / 'plugins/gui/libqt_plugin.dll'
assert b'VLC_PLAYER_DIAGNOSTICS_DIR' in plugin.read_bytes()
root.mkdir()
runtime = root / 'runtime'
shutil.copytree(source, runtime, ignore=lambda path, names: ['sdk'] if Path(path).resolve() == source else [])
portable = runtime / 'portable'
repo = Path(__file__).resolve().parents[2]
inspector = Path(__file__).with_name('inspect-player.py')
records = {'schema': 'vlc_redesign.m2_native_acceptance.v1', 'scope': args.case,
    'qt_plugin_sha256': hashlib.sha256(plugin.read_bytes()).hexdigest(), 'cases': [],
    'no_os_input_or_desktop_switching': True, 'passed': False}
records['verification_helper_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
records['source_commit']=json.loads((source/'VLC-PLUGIN-BUILDINFO.json').read_text())['source_commit']
production=subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','-z',records['source_commit'],'--',
    'include','src','lib','compat','modules','share','configure.ac','Makefile.am','extras/package/win32'])
records['production_tree_sha256']=hashlib.sha256(production).hexdigest()


def profiles():
    spec=importlib.util.spec_from_file_location('installed_profile',Path(__file__).with_name('check-installed-profile.py'))
    helper=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    result=helper.snapshot(include_nuvio=True)
    folder=Path('D:/VLC-Redesign/releases/1.1.1/Modern-VLC-Fork-1.1.1-win64-portable/portable')
    result['delivered_portable']=[helper.file_record(file) for file in sorted(folder.rglob('*')) if file.is_file()]
    return result


records['protected_profiles_before'] = profiles()
active_cases=set()

def save():
    (root / 'result.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

class Peer(BaseHTTPRequestHandler):
    mode = 'current'
    calls = []
    def do_GET(self):
        if self.path=='/english.srt':
            Peer.calls.append({'mode':'remote-subtitle','path':self.path})
            payload=(fixtures/'english.srt').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type','application/x-subrip')
            self.send_header('Content-Length',str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        assert self.path == '/releases/latest'
        Peer.calls.append({'mode': Peer.mode, 'path': self.path})
        payload = (fixtures / 'github-latest.json').read_bytes()
        status = 200
        if Peer.mode == 'unavailable': status, payload = 503, b'Unavailable test peer'
        elif Peer.mode == 'malformed': payload = b'{broken'
        elif Peer.mode == 'newer':
            item = json.loads(payload)
            old = item['tag_name'][len('redesign-v'):]
            encoded = json.dumps(item).replace('redesign-v' + old, 'redesign-v1.1.3').replace('Modern-VLC-Fork-' + old, 'Modern-VLC-Fork-1.1.3')
            payload = encoded.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def log_message(self, *values): pass

server = ThreadingHTTPServer(('127.0.0.1', 0), Peer)
server.daemon_threads = True
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

class Case:
    def __init__(self, name, *, scale='1', engine='vlc', welcome=False, media=None, updates=False, live_updates=False, reused_profile=None, extra=()):
        self.path = root / name
        assert not self.path.exists()
        self.path.mkdir()
        for name in ('evidence', 'tmp', 'qml'): (self.path / name).mkdir()
        self.evidence = self.path / 'evidence'
        self.session = self.evidence / 'session.json'
        self.record = {'name': self.path.name, 'scale': scale, 'engine': engine, 'steps': [], 'passed': False}
        records['cases'].append(self.record)
        assert portable.resolve().is_relative_to(root) and not any(portable.iterdir())
        if reused_profile:
            assert reused_profile.resolve().is_relative_to(root)
            shutil.copytree(reused_profile, portable, dirs_exist_ok=True)
        self.token = uuid.uuid4().hex + uuid.uuid4().hex
        env = {name: value for name, value in os.environ.items() if not name.startswith('VLC_PLAYER_DIAGNOSTICS')}
        for name in ('VLC_PLUGIN_PATH', 'QT_SCREEN_SCALE_FACTORS', 'LC_ALL', 'LC_MESSAGES', 'LANGUAGE'): env.pop(name, None)
        env.update(TEMP=str(self.path / 'tmp'), TMP=str(self.path / 'tmp'), VLC_DATA_PATH=str(runtime),
            VLC_USERDATA_PATH=str(portable), QML_DISK_CACHE_PATH=str(self.path / 'qml'), QT_DISABLE_SHADER_DISK_CACHE='1',
            QSG_RHI_DISABLE_SHADER_DISK_CACHE='1', QT_FORCE_STDERR_LOGGING='1', QT_ENABLE_HIGHDPI_SCALING='0',
            QT_FONT_DPI='96', QT_SCALE_FACTOR=scale, VLC_PLAYER_DIAGNOSTICS_DIR=str(self.evidence),
            VLC_PLAYER_DIAGNOSTICS_TOKEN=self.token, VLC_PLAYER_DIAGNOSTICS_BUILD=records['qt_plugin_sha256'])
        if not live_updates: env['VLC_PLAYER_DIAGNOSTICS_UPDATE_URL'] = 'http://127.0.0.1:' + str(server.server_port) + '/releases/latest'
        command = [str(runtime / 'vlc.exe'), '--intf=qt', '--language=en', '--no-one-instance', '--no-plugins-cache',
            '--no-metadata-network-access', '--restore-playback-pos=0', '--no-volume-save', '--mmdevice-volume=0',
            '--aout=mmdevice', '--mmdevice-backend=wasapi', '--no-video-title-show', '--start-paused',
            '--qt-playback-engine=' + engine, '--verbose=2', '--file-logging', '--log-verbose=2',
            '--logfile=' + str(self.evidence / 'native-ui.log')]
        if not welcome: command.append('--no-qt-privacy-ask')
        if not updates: command.append('--no-qt-updates-notif')
        command.extend(extra)
        if media: command.append(str(media))
        (self.evidence / 'launch-argv.json').write_text(json.dumps(command, indent=2) + '\n')
        self.stdout = (self.evidence / 'stdout.log').open('wb')
        self.stderr = (self.evidence / 'stderr.log').open('wb')
        self.player = IsolatedProcess(command, runtime, env, self.stdout, self.stderr)
        active_cases.add(self)
        self.session.write_text(json.dumps({'pid': self.player.pid, 'executable': str(runtime / 'vlc.exe'), 'token': self.token}))
        self.closed = False
        save()

    def inspect(self, label, op='snapshot', *options):
        if not self.record['steps'] and label != 'view-mounted' and op != 'quit':
            self.inspect('view-mounted','snapshot','--await-target','viewLoader','--await-property','status','--await-value','1')
        if op=='click' and '--name' in options:
            name=options[options.index('--name')+1]
            if name in ('Show Subtitle Timeline on Seekbar','VLC','MPV / Dolby Vision'):
                self.inspect(label+'-reveal','focus','--name',name)
        self.record['pending'] = {'label': label, 'op': op, 'options': list(map(str, options))}
        save()
        command = [sys.executable, '-B', str(inspector), '--session', str(self.session), op, *map(str, options)]
        before = time.perf_counter_ns()
        process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
        elapsed = (time.perf_counter_ns() - before) / 1000000.
        (self.evidence / (label + '.client.log')).write_text(process.stdout + process.stderr, encoding='utf-8')
        assert process.returncode == 0, (label, process.stdout, process.stderr)
        path = Path(re.search(r'^Response: (.+)$', process.stdout, re.M).group(1).strip())
        result = json.loads(path.read_text(encoding='utf-8'))
        assert not result.get('qml_errors'), (label, result.get('qml_errors'))
        assert '"before": false, "after": false' in process.stdout, 'Owned player gained OS foreground'
        self.record['steps'].append({'label': label, 'response': str(path.relative_to(root)), 'client_elapsed_ms': elapsed})
        self.record.pop('pending', None)
        save()
        print(json.dumps({'case': self.path.name, 'step': label, 'status': result['status']}), flush=True)
        return result

    def click(self, label, target, *options): return self.inspect(label, 'click', '--target', target, *options)
    def native(self, label, target, *options): return self.inspect(label, 'widget_click', '--target', target, *options)
    def key(self, label, key, *, target='playButton', modifiers=0, text='', **unused):
        self.inspect(label + '-focus', 'focus', '--target', target)
        return self.inspect(label, 'key', '--target', target, '--key', hex(key), '--modifiers', hex(modifiers), '--text', text)
    def close(self, passed=False):
        if self.closed: return
        try:
            if k.WaitForSingleObject(self.player.handle, 0) != 0: self.inspect('quit', 'quit')
        finally:
            self.record['exit_code'] = self.player.wait()
            active_cases.remove(self)
            self.closed = True
            self.stdout.close(); self.stderr.close()
            assert self.record['exit_code'] == 0, self.record
            target = self.path / 'profile'
            assert not target.exists() and portable.resolve().is_relative_to(root) and target.resolve().is_relative_to(root)
            portable.rename(target)
            portable.mkdir()
            self.record['input_desktop_preserved'] = True
            self.record['passed'] = passed
            save()

def nodes(snapshot, identity): return [node for node in snapshot['tree'] if node['id'] == identity and node['visible']]
def service(snapshot, name='redesignMediaTools'): return snapshot['media_tools'][name]


def verify_executable_icon():
    records['executable_icon']=executable_icon(runtime/'vlc.exe',repo/'share/icons/vlc.ico')


def owned_main_window(case, snapshot):
    u.GetAncestor.argtypes=[W.HWND,W.UINT]
    u.GetAncestor.restype=W.HWND
    hwnd=u.GetAncestor(W.HWND(int(snapshot['window']['native_id_hex'],16)),2)
    assert hwnd, 'Qt surface has no native root window'
    pid=W.DWORD()
    u.GetWindowThreadProcessId(W.HWND(hwnd),ctypes.byref(pid))
    assert pid.value==case.player.pid, 'Native root belongs to a different process'
    return W.HWND(hwnd)


def owned_native_read(case, reader):
    """Bind a new reader thread to the owned inactive desktop, without switching it."""
    before=input_desktop()
    u.GetThreadDesktop.argtypes=[W.DWORD]
    u.GetThreadDesktop.restype=W.HANDLE
    u.SetThreadDesktop.argtypes=[W.HANDLE]
    u.SetThreadDesktop.restype=W.BOOL
    def read():
        original=u.GetThreadDesktop(k.GetCurrentThreadId())
        assert original and u.SetThreadDesktop(case.player.desktop),ctypes.WinError(ctypes.get_last_error())
        try:return reader()
        finally:assert u.SetThreadDesktop(original),ctypes.WinError(ctypes.get_last_error())
    with ThreadPoolExecutor(max_workers=1) as worker:
        result=worker.submit(read).result()
    assert input_desktop()==before
    return result


def verify_window_icon(case, snapshot):
    case.record['native_window_icon']=owned_native_read(case,lambda:window_icon(owned_main_window(case,snapshot),case.player.pid,
        repo/'modules/gui/qt/pixmaps/redesign/app.png',case.evidence/'native-window-icon.png'))

def assert_window(case, snapshot):
    return owned_native_read(case,lambda:assert_window_on_desktop(case,snapshot))


def assert_window_on_desktop(case, snapshot):
    window = snapshot['window']
    hwnd = owned_main_window(case,snapshot)
    actual_pid = W.DWORD()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(actual_pid))
    assert actual_pid.value == case.player.pid
    # These read-only calls use physical pixels for both rectangles. They do
    # not change the app's DPI mode or any global Windows display setting.
    u.SetThreadDpiAwarenessContext.argtypes = [W.HANDLE]
    u.SetThreadDpiAwarenessContext.restype = W.HANDLE
    original = u.SetThreadDpiAwarenessContext(W.HANDLE(-4))
    class MonitorInfo(ctypes.Structure):
        _fields_ = [('size', W.DWORD), ('monitor', W.RECT), ('work', W.RECT), ('flags', W.DWORD)]
    u.MonitorFromWindow.argtypes = [W.HWND, W.DWORD]
    u.MonitorFromWindow.restype = W.HANDLE
    u.GetWindowRect.argtypes = [W.HWND, ctypes.POINTER(W.RECT)]
    u.GetMonitorInfoW.argtypes = [W.HANDLE, ctypes.POINTER(MonitorInfo)]
    rect, visible, monitor = W.RECT(), W.RECT(), MonitorInfo()
    monitor.size = ctypes.sizeof(monitor)
    try:
        assert u.GetWindowRect(hwnd, ctypes.byref(rect))
        dwm=ctypes.WinDLL('dwmapi',use_last_error=True)
        dwm.DwmGetWindowAttribute.argtypes=[W.HWND,W.DWORD,ctypes.c_void_p,W.DWORD]
        dwm.DwmGetWindowAttribute.restype=ctypes.c_long
        assert dwm.DwmGetWindowAttribute(hwnd,9,ctypes.byref(visible),ctypes.sizeof(visible))==0
        handle = u.MonitorFromWindow(hwnd, 2)
        assert u.GetMonitorInfoW(handle, ctypes.byref(monitor))
        # GetWindowRect includes Windows' invisible resize borders. The DWM
        # extended frame is the visible frame/chrome required to fit the screen.
        assert visible.left >= monitor.work.left and visible.top >= monitor.work.top and visible.right <= monitor.work.right and visible.bottom <= monitor.work.bottom, (list((visible.left,visible.top,visible.right,visible.bottom)), list((monitor.work.left,monitor.work.top,monitor.work.right,monitor.work.bottom)))
    finally:
        if original: u.SetThreadDpiAwarenessContext(original)
    case.record.setdefault('window_checks', []).append({'qt': window, 'physical': [rect.left,rect.top,rect.right,rect.bottom],
        'visible_physical':[visible.left,visible.top,visible.right,visible.bottom],
        'work': [monitor.work.left,monitor.work.top,monitor.work.right,monitor.work.bottom]})

def welcome():
    for scale in ('1', '1.5', '2'):
        case = Case('welcome-' + scale.replace('.', ''), scale=scale, welcome=True)
        try:
            initial = case.inspect('welcome', 'snapshot', '--capture')
            assert initial['customization']['onboardingVisible']
            assert_window(case, initial)
            verify_window_icon(case, initial)
            for identity in ('onboardingNext','onboardingSkip'):
                control = nodes(initial, identity)
                assert len(control) == 1 and control[0]['width'] > 0 and control[0]['height'] > 0
                assert control[0]['x'] >= 0 and control[0]['y'] >= 0 and control[0]['x']+control[0]['width'] <= initial['window']['width']+1 and control[0]['y']+control[0]['height'] <= initial['window']['height']+1
            case.inspect('reveal-optional-folder','focus','--target','onboardingFolder','--capture')
            case.click('theme-page', 'onboardingNext')
            case.click('font-page', 'onboardingNext')
            case.inspect('reveal-font-choice','focus','--target','onboardingFontFallback')
            shortcuts = case.click('shortcut-page', 'onboardingFontFallback', '--capture')
            assert nodes(shortcuts,'onboardingNext')[0]['text']=='Finish'
            assert not any(n['visible'] for n in nodes(shortcuts,'onboardingSkip'))
            face=nodes(shortcuts,'onboardingKeyFace_key-play-pause_0')[0]
            shadow=nodes(shortcuts,'onboardingKeyShadow_key-play-pause_0')[0]
            key_scale=face['height']/42
            assert abs(shadow['y']-face['y']-6*key_scale)<0.1
            caption=nodes(shortcuts,'onboardingShortcutCaption_key-play-pause')[0]
            if nodes(shortcuts,'playerOnboarding')[0]['width']>=1000*key_scale:
                assert abs(face['x']-caption['x']-240*key_scale)<0.1, 'The label must not stretch and push keycaps right'
            assert nodes(shortcuts,'onboardingKeyLabel_key-toggle-fullscreen_0')[0]['text']=='F'
            left=nodes(shortcuts,'onboardingShortcut_key-jump-short')[0]
            right=nodes(shortcuts,'onboardingShortcut_key-jump+short')[0]
            assert abs(left['y']-right['y'])<0.1 and right['x']>left['x']+left['width']
            assert nodes(shortcuts,'onboardingKeyLabel_key-jump-short_1')[0]['text']=='←'
            assert nodes(shortcuts,'onboardingKeyLabel_key-snapshot_0')[0]['text']=='SHIFT'
            assert nodes(shortcuts,'onboardingKeyLabel_key-snapshot_1')[0]['text']=='S'
            case.record['shortcut_visual_contract']={'key_face':face,'lower_edge':shadow,'paired_left':left,'paired_right':right,
                'reference_frame':'1902:6770','rendered_comparison_required':True}
            for option in ('key-toggle-fullscreen','qt-key-toggle-browser','qt-key-toggle-queue'):
                assert len(nodes(shortcuts, 'onboardingShortcut_' + option)) == 1
                revealed=case.inspect('reveal-shortcut-'+option,'focus','--target','onboardingShortcut_'+option,'--capture')
                item=nodes(revealed,'onboardingShortcut_'+option)[0]
                assert 0<=item['y'] and item['y']+item['height']<=revealed['window']['height']
            if scale == '1':
                case.inspect('reveal-fullscreen', 'focus', '--target', 'onboardingShortcut_key-toggle-fullscreen')
                case.click('edit-fullscreen', 'onboardingShortcut_key-toggle-fullscreen')
                case.inspect('capture-fullscreen', 'widget_key', '--target', 'shortcutCapture', '--key', '0x39', '--modifiers', '0xe000000', '--text', '9')
                case.native('assign-fullscreen', 'assignShortcut')
                case.native('save-fullscreen', 'preferencesSave')
                case.click('unset-browser', 'onboardingShortcut_qt-key-toggle-browser')
                case.native('unset-browser-key', 'unsetShortcut')
                case.native('save-unset', 'preferencesSave')
                unassigned = case.inspect('unassigned-is-editable')
                assert any(node['visible'] and node.get('text') == 'Unassigned' for node in unassigned['tree'])
                case.click('assign-unassigned-browser', 'onboardingShortcut_qt-key-toggle-browser')
                case.inspect('capture-browser', 'widget_key', '--target', 'shortcutCapture', '--key', '0x38', '--modifiers', '0xe000000', '--text', '8')
                case.native('assign-browser', 'assignShortcut')
                case.native('save-browser', 'preferencesSave')
                case.click('conflicting-browser', 'onboardingShortcut_qt-key-toggle-browser')
                conflict = case.inspect('conflict-fullscreen', 'widget_key', '--target', 'shortcutCapture', '--key', '0x39', '--modifiers', '0xe000000', '--text', '9')
                assert any(widget['id'] == 'keyConflictWarning' and widget.get('text') for widget in conflict['widgets'])
                case.native('cancel-conflict', 'cancelShortcut')
                case.native('cancel-draft', 'preferencesCancel')
            case.click('finish-without-root', 'onboardingNext')
            case.close(True)
            profile = case.path / 'profile'
            for dbfile in profile.rglob('*.db'):
                with sqlite3.connect(dbfile.as_uri() + '?mode=ro', uri=True) as db:
                    tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    if 'Folder' in tables: assert db.execute('SELECT COUNT(*) FROM Folder').fetchone()[0] == 0
            restarted = Case('restart-empty-' + scale.replace('.', ''), scale=scale, welcome=True, reused_profile=profile)
            try:
                result = restarted.inspect('second-start', 'snapshot', '--await-target', 'fullLibrary', '--await-property', 'ready', '--await-value', 'true', '--capture')
                verify_window_icon(restarted, result)
                assert not result['customization']['onboardingVisible']
                assert not result['library']['indexing']
                if scale == '1':
                    drop_fixture(restarted,'shortcut-playback','control.mkv')
                    restarted.inspect('shortcut-key-focus','focus','--target','playButton')
                    restarted.inspect('saved-fullscreen-shortcut','key','--key','0x39','--modifiers','0xe000000','--text','9',
                        '--await-core','fullscreen','--await-value','true')
                    restarted.inspect('leave-fullscreen','key','--key','0x1000000','--await-core','fullscreen','--await-value','false')
                    restarted.inspect('saved-browser-shortcut','key','--key','0x38','--modifiers','0xe000000','--text','8')
                    restarted.inspect('browser-ready','snapshot','--await-target','compactLibrary','--await-property','ready','--await-value','true','--capture')
                    closed=restarted.inspect('close-browser-shortcut','key','--key','0x38','--modifiers','0xe000000','--text','8')
                    assert not any(node['id']=='compactLibrary' and node['visible'] for node in closed['tree'])
                    restarted.inspect('queue-shortcut','key','--key','0x4c','--modifiers','0x4000000','--text','l',
                        '--await-target','playqueueToggle','--await-property','checked','--await-value','true')
                    restarted.inspect('close-queue-shortcut','key','--key','0x4c','--modifiers','0x4000000','--text','l',
                        '--await-target','playqueueToggle','--await-property','checked','--await-value','false')
                restarted.close(True)
            finally: restarted.close()
        finally: case.close()
    skipped = Case('skip-empty', welcome=True)
    try:
        skipped.inspect('welcome-ready')
        skipped.click('skip-without-root', 'onboardingSkip')
        empty = skipped.inspect('empty-idle', 'snapshot', '--await-target', 'fullLibrary', '--await-property', 'ready', '--await-value', 'true', '--capture')
        assert not empty['library']['indexing']
        skipped.click('add-root-menu', 'libraryAddItem')
        skipped.inspect('index-folder-dialog', 'click', '--name', 'Index library folder…')
        skipped.inspect('enter-synthetic-root', 'key', '--target', 'libraryDialogInput', '--key', '0', '--text', str(fixtures))
        skipped.click('submit-root', 'libraryDialogSubmit','--await-target','fullLibrary','--await-property','indexing','--await-value','true')
        skipped.click('all-videos-menu', 'libraryAddItem')
        skipped.inspect('all-videos', 'click', '--name', 'All videos')
        indexed = skipped.inspect('discovered-videos', 'snapshot', '--await-target', 'fullLibrary', '--await-property', 'itemCount', '--await-value', '8', '--await-comparison', 'at_least')
        skipped.inspect('discovery-idle', 'snapshot', '--await-target', 'fullLibrary', '--await-property', 'indexing', '--await-value', 'false', '--capture')
        skipped.record['indexed_videos'] = indexed['library']['indexed_model_count']
        skipped.record['busy_to_idle_observed']=True
        skipped.close(True)
    finally: skipped.close()

def playback():
    for engine in ('vlc','mpv'):
        for name in ('wide.mkv','portrait.mkv','preview-4k-long-gop.mkv'):
            case=Case('drop-' + engine + '-' + name.split('.')[0], engine=engine)
            try:
                case.inspect('full-library-viewport','resize','--width','1280','--height','800')
                case.inspect('library-ready', 'snapshot', '--await-target','fullLibrary','--await-property','ready','--await-value','true')
                drop_fixture(case,'drop-video',name)
                result=case.inspect('main-player-visible','snapshot','--await-target','playerView','--await-property','visible','--await-value','true','--capture')
                try:assert_window(case,result)
                except AssertionError as failure:
                    if args.case!='integration-diagnostic':raise
                    case.record['known_geometry_failure']=repr(failure)
                    case.close(False)
                    continue
                case.record['source']=name
                case.close(True)
            finally: case.close()
        fixed=Case('fixed-size-'+engine,engine=engine,extra=['--no-qt-video-autoresize'])
        try:
            fixed.inspect('full-library-viewport','resize','--width','1280','--height','800')
            before=fixed.inspect('library-ready','snapshot','--await-target','fullLibrary','--await-property','ready','--await-value','true')
            drop_fixture(fixed,'fixed-size-video','wide.mkv')
            after=fixed.inspect('fixed-main-view','snapshot','--await-target','playerView','--await-property','visible','--await-value','true','--capture')
            assert (before['window']['width'],before['window']['height'])==(after['window']['width'],after['window']['height'])
            fixed.click('fullscreen','fullscreenButton','--await-core','fullscreen','--await-value','true')
            replacement=drop_fixture(fixed,'fullscreen-new-input','portrait.mkv')
            assert replacement['core']['fullscreen'] and replacement['window']['visibility']==5
            windowed=fixed.inspect('restore-windowed','key','--key','0x1000000','--await-core','fullscreen','--await-value','false')
            assert (windowed['window']['width'],windowed['window']['height'])==(before['window']['width'],before['window']['height'])
            fixed.inspect('intentional-library-view','click','--name','Back to media','--await-target','viewLoader',
                '--await-property','source','--await-value',json.dumps('qrc:///qt/qml/VLC/Player/PlayerLibraryDisplay.qml'))
            library=fixed.inspect('intentional-mini-player','snapshot','--await-target','viewLoader','--await-property','status','--await-value','1','--capture')
            assert nodes(library,'libraryReturnToPlayer'),'Intentional library browsing lost the mini player'
            drop_fixture(fixed,'fresh-video-from-library','wide.mkv')
            if engine=='mpv':
                fixed.inspect('library-before-audio','click','--name','Back to media','--await-target','viewLoader',
                    '--await-property','source','--await-value',json.dumps('qrc:///qt/qml/VLC/Player/PlayerLibraryDisplay.qml'))
                fixed.inspect('replace-with-audio','drop','--target','mainInterface','--url',(fixtures/'audio-only.mka').as_uri(),
                    '--await-core','url','--await-value',json.dumps((fixtures/'audio-only.mka').as_uri()))
                audio=fixed.inspect('audio-input-ready','snapshot','--await-core','mpv_history_ready','--await-value','true')
                assert audio['core']['audio_tracks'] and not audio['core']['video_tracks'] and not audio['core']['mpv_video_ready']
                fixed.inspect('audio-library-preserved','snapshot','--await-target','viewLoader','--await-property','source',
                    '--await-value',json.dumps('qrc:///qt/qml/VLC/Player/PlayerLibraryDisplay.qml'))
                drop_fixture(fixed,'video-after-audio','portrait.mkv')
            fixed.close(True)
        finally: fixed.close()
    for engine,scale in (('vlc','1.5'),('mpv','2')):
        case=Case('scaled-video-'+engine,engine=engine,scale=scale)
        try:
            case.inspect('full-library-viewport','resize','--width','1280','--height','800')
            case.inspect('library-ready','snapshot','--await-target','fullLibrary','--await-property','ready','--await-value','true')
            drop_fixture(case,'scaled-video','wide.mkv')
            result=case.inspect('scaled-main-view','snapshot','--await-target','playerView','--await-property','visible','--await-value','true','--capture')
            try:assert_window(case,result)
            except AssertionError as failure:
                if args.case!='integration-diagnostic':raise
                case.record['known_geometry_failure']=repr(failure)
                case.close(False)
                continue
            case.close(True)
        finally: case.close()

def subtitle_menu(case, label, enabled):
    case.inspect(label + '-open','click','--name','Main menu')
    result=case.inspect(label + '-submenu', 'widget_click', '--menu-action', 'Subtitle', '--capture')
    actions=[action for widget in result['widgets'] for action in widget.get('actions', [])]
    tracks=[action for action in actions if action['text'].replace('&','').split('\t')[0]=='Sub Track']
    assert len(tracks)==1 and tracks[0]['enabled']==enabled, tracks
    assert any(action['enabled'] and action['text'].replace('&','').startswith('Add Subtitle File') for action in actions)
    case.inspect(label + '-dismiss','key','--key','0x1000000')
    case.inspect(label + '-dismiss-root','key','--key','0x1000000')


def subtitle_choices(snapshot):
    tree={node['node']:node for node in snapshot['tree']}
    def inside(node):
        while node['parent'] >= 0:
            node=tree[node['parent']]
            if node['id']=='subtitleTracksBody': return True
        return False
    return [node for node in snapshot['tree'] if node['visible'] and node['enabled'] and node.get('actions') and node.get('role') in (44,45) and 'selected' in node and inside(node)]


def cue_result(case, label, count):
    result=case.inspect(label,'snapshot','--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps(str(count)+' embedded source cues; positions follow the selected track and subtitle delay.'))
    assert len(service(result)['cues'])==count
    return result


def select_available_subtitle(case, label, snapshot):
    tracks=snapshot['core']['subtitle_tracks']
    assert tracks,'Fixture has no native subtitle track'
    if any(track['selected'] for track in tracks):return snapshot
    case.inspect(label+'-track-viewport','resize','--width','960','--height','720')
    choices=case.click(label+'-track-choice','subtitleButton')
    rows=[node for node in subtitle_choices(choices) if node.get('name')!='None']
    assert len(rows)==len(tracks),rows
    selected=case.inspect(label+'-select-track','click','--name',rows[0]['name'],
        '--await-property','selected','--await-value','true')
    case.inspect(label+'-close-track-choice','key','--key','0x1000000')
    return selected


def drop_fixture(case, label, file):
    case.inspect(label,'drop','--target','mainInterface','--url',(fixtures/file).as_uri(),
        '--await-core','url','--await-value',json.dumps((fixtures/file).as_uri()))
    case.inspect(label+'-seekable','snapshot','--await-core','seekable','--await-value','true')
    case.inspect(label+'-main-source','snapshot','--await-target','viewLoader','--await-property','source',
        '--await-value',json.dumps('qrc:///qt/qml/VLC/Player/Player.qml'))
    ready=case.inspect(label+'-main-ready','snapshot','--await-target','viewLoader','--await-property','status','--await-value','1')
    # --start-paused applies only to the first input. Pause replacement items
    # through the real control rather than waiting for an impossible state.
    if ready['core']['state']==2:
        if ready['core']['fullscreen']:
            # Dropping a replacement focuses the player itself. Use its real
            # Space shortcut when the fullscreen toolbar is auto-hidden.
            return case.inspect(label+'-pause','key','--key','0x20','--text',' ',
                '--await-core','state','--await-value','3')
        return case.click(label+'-pause','playButton','--await-core','state','--await-value','3')
    return case.inspect(label+'-paused','snapshot','--await-core','state','--await-value','3')


def subtitles(verify_navigation=True, engines=('vlc','mpv')):
    for engine in engines:
        case=Case('timeline-' + engine, engine=engine, media=fixtures/'embedded-text.mkv')
        try:
            case.inspect('paused','snapshot','--await-core','state','--await-value','3')
            case.click('open-playback-tools','toolsButton')
            timeline=case.inspect('enable-timeline','click','--name','Show Subtitle Timeline on Seekbar',
                '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('3 embedded source cues; positions follow the selected track and subtitle delay.'))
            assert len(service(timeline)['cues'])==3
            case.inspect('close-settings','key','--key','0x1000000')
            shown=case.inspect('timeline-controls','snapshot','--capture')
            for identity in ('previousSubtitleCue','nextSubtitleCue','subtitleDelayEarlier','subtitleDelayLater'):
                assert len(nodes(shown,identity))==1
            buttons=[nodes(shown,identity)[0] for identity in ('previousSubtitleCue','subtitleDelayEarlier','subtitleDelayLater','nextSubtitleCue')]
            assert all(left['x']+left['width']<=right['x']+.5 for left,right in zip(buttons,buttons[1:]))
            graph=nodes(shown,'subtitleTimelineOffset')[0]
            assert graph['width']>0 and 0<=graph['x'] and graph['x']+graph['width']<=shown['window']['width']
            assert 0<=graph['y'] and graph['y']+graph['height']<=shown['window']['height']
            base=shown['core']['subtitle_delay_ms']
            case.click('delay-later','subtitleDelayLater','--await-core','subtitle_delay_ms','--await-value',base+50,'--await-tolerance','0.001')
            case.click('delay-earlier','subtitleDelayEarlier','--await-core','subtitle_delay_ms','--await-value',base,'--await-tolerance','0.001')
            # Allow the native paused clock's precision on this12fps fixture;
            # a one-second buffering offset must fail this bound.
            if verify_navigation:
                case.click('next-cue','nextSubtitleCue','--await-core','time_seconds','--await-value','1','--await-tolerance','0.2')
                case.click('next-cue-again','nextSubtitleCue','--await-core','time_seconds','--await-value','4','--await-tolerance','0.2')
                case.click('previous-cue','previousSubtitleCue','--await-core','time_seconds','--await-value','1','--await-tolerance','0.2')
            # The narrow case above proves the cue row fits. Use a full popup
            # viewport for the separate multi-track and native file workflows.
            case.inspect('track-selection-viewport','resize','--width','960','--height','720')
            subtitle_menu(case,'embedded-track-menu',True)
            tracks=case.click('open-track-choice','subtitleButton')
            alternate=[node for node in subtitle_choices(tracks) if node.get('name')!='None' and not node['selected']]
            assert len(alternate)==1, alternate
            case.inspect('select-second-track','click','--name',alternate[0]['name'],'--await-property','selected','--await-value','true')
            second=cue_result(case,'second-track-cues',2)
            assert service(second)['cues'][0]['start']==2000
            disabled=case.inspect('disable-selected-track','click','--name','None','--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('No subtitle track selected.'))
            assert not service(disabled)['cues'] and not any(track['selected'] for track in disabled['core']['subtitle_tracks'])
            case.inspect('restore-second-track','click','--name',alternate[0]['name'],'--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('2 embedded source cues; positions follow the selected track and subtitle delay.'))
            case.inspect('dismiss-track-popup','key','--key','0x1000000')
            other='mpv' if engine=='vlc' else 'vlc'
            for target in (other,engine):
                case.click('switch-tools-'+target,'toolsButton')
                case.inspect('choose-engine-'+target,'click','--name','MPV / Dolby Vision' if target=='mpv' else 'VLC')
                settled=case.inspect('engine-settled-'+target,'snapshot','--await-core','engine_switching','--await-value','false')
                assert settled['core']['engine']==target and settled['core']['state']==3
                # Track ids/default selections belong to each backend. R82
                # requires the timeline to follow the incoming selected track,
                # while R67 preserves position and pause across the switch.
                selected=[track for track in settled['core']['subtitle_tracks'] if track['selected']]
                assert len(selected)==1 and selected[0]['language'] in ('eng','deu'),selected
                german=selected[0]['language']=='deu'
                handover=cue_result(case,'handover-cues-'+target,2 if german else 3)
                assert service(handover)['cues'][0]['start']==(2000 if german else 1000)
                case.inspect('dismiss-engine-tools-'+target,'key','--key','0x1000000')
                subtitle_menu(case,'handover-menu-'+target,True)
            for file in ('embedded-ass.mkv','embedded-text.mp4'):
                opened=drop_fixture(case,'open-'+file,file)
                select_available_subtitle(case,'open-'+file,opened)
                decoded=cue_result(case,'native-cues-'+file,3)
                assert service(decoded)['cues'][0]['start']==1000
            opened=drop_fixture(case,'open-image','embedded-image.mkv')
            select_available_subtitle(case,'open-image',opened)
            image=case.inspect('image-limit','snapshot','--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('Image subtitles keep playing normally; a text cue timeline is unavailable.'))
            assert not service(image)['cues'] and image['core']['subtitle_tracks']
            drop_fixture(case,'open-no-track','control.mkv')
            no_track=case.inspect('no-track-cues','snapshot','--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('No subtitle track selected.'))
            assert not service(no_track)['cues']
            subtitle_menu(case,'no-track-menu',False)
            case.inspect('drop-external-subtitle','drop','--target','mainInterface','--url',(fixtures/'english.srt').as_uri(),
                '--await-service','redesignMediaTools','--await-property','subtitleLoaded','--await-value','true')
            external=case.inspect('external-cues','snapshot','--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('3 source cues; positions follow subtitle FPS and track delay. Duration filters can extend the displayed cue ends.'))
            assert len(service(external)['cues'])==3
            subtitle_menu(case,'external-track-menu',True)
            case.inspect('native-add-subtitle-menu','click','--name','Main menu')
            case.inspect('native-subtitle-submenu','widget_click','--menu-action','Subtitle')
            case.inspect('native-add-subtitle-dialog','widget_click','--menu-action','Add Subtitle File...')
            case.native('native-file-name-focus','fileNameEdit')
            case.inspect('select-file-name','widget_key','--target','fileNameEdit','--key','0x41','--modifiers','0x4000000','--text','a')
            case.inspect('enter-native-subtitle-file','widget_key','--target','fileNameEdit','--key','0','--text',str(fixtures/'german.srt'))
            chosen=case.inspect('accept-native-subtitle-file','widget_key','--target','fileNameEdit','--key','0x1000004',
                '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('2 source cues; positions follow subtitle FPS and track delay. Duration filters can extend the displayed cue ends.'))
            assert service(chosen)['subtitleLoaded'] and len(service(chosen)['cues'])==2
            case.inspect('external-track-viewport','resize','--width','960','--height','720')
            available=case.click('reopen-external-track-choice','subtitleButton')
            earlier=[node for node in subtitle_choices(available) if node.get('name')!='None' and not node['selected']]
            assert len(earlier)==1,earlier
            restored=case.inspect('select-earlier-external-track','click','--name',earlier[0]['name'],
                '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('3 source cues; positions follow subtitle FPS and track delay. Duration filters can extend the displayed cue ends.'))
            assert 'English first' in service(restored)['cues'][0]['text']
            case.inspect('dismiss-external-track-choice','key','--key','0x1000000')
            remote=case.inspect('preserve-remote-subtitle-drop','drop','--target','mainInterface','--url','http://127.0.0.1:'+str(server.server_port)+'/english.srt',
                '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('Text cue timelines require a local subtitle file; subtitle playback is unchanged.'))
            assert remote['core']['state']==3 and service(remote)['subtitleLoaded'] and not service(remote)['cues']
            case.close(True)
            restarted=Case('timeline-restart-'+engine,engine=engine,media=fixtures/'embedded-text.mkv',reused_profile=case.path/'profile')
            try:
                initial=restarted.inspect('paused','snapshot','--await-core','state','--await-value','3')
                assert service(initial)['timelineVisible'], 'Timeline preference did not survive restart'
                select_available_subtitle(restarted,'restart-subtitle',initial)
                observed=restarted.inspect('restart-track-observed')
                selected=[track for track in observed['core']['subtitle_tracks'] if track['selected']]
                assert len(selected)==1 and selected[0]['language'] in ('eng','deu'),selected
                restored=cue_result(restarted,'restored-timeline',2 if selected[0]['language']=='deu' else 3)
                assert service(restored)['timelineVisible'] and len(nodes(restored,'subtitleDelayLater'))==1
                restarted.close(True)
            finally: restarted.close()
        finally: case.close()

def preview():
    case=Case('seek-preview',media=fixtures/'preview-4k-long-gop.mkv')
    try:
        case.inspect('paused','snapshot','--await-core','state','--await-value','3')
        cold=case.inspect('cold-preview','move','--target','progressSlider','--fraction-x','0.55',
            '--await-service','redesignMediaAnalysis','--await-property','previewStatus','--await-value','""','--capture')
        first=service(cold,'redesignMediaAnalysis')
        assert first['previewSource'] and abs(first['previewPosition']-.55)<.02
        case.inspect('leave-preview','move','--target','playButton')
        warm=case.inspect('cached-preview','move','--target','progressSlider','--fraction-x','0.55',
            '--await-service','redesignMediaAnalysis','--await-property','previewStatus','--await-value','""','--capture')
        cached=service(warm,'redesignMediaAnalysis')
        assert cached['previewLatencyMS']<16.7, cached
        case.record['cold_decode_ms']=first['previewLatencyMS']
        case.record['cached_publication_ms']=cached['previewLatencyMS']
        assert first['previewLatencyMS']<1000, 'Uncached local preview still takes several seconds'
        for position in (.1,.2,.3,.4,.5,.6,.7,.8,.9):
            case.inspect('continuous-' + str(position),'move','--target','progressSlider','--fraction-x',position)
        latest=case.inspect('latest-preview','snapshot','--await-service','redesignMediaAnalysis','--await-property','previewPosition','--await-value','0.9','--await-tolerance','.02','--capture')
        case.record['latest_preview']=service(latest,'redesignMediaAnalysis')
        assert abs(case.record['latest_preview']['previewPosition']-.9)<.02
        cleared=drop_fixture(case,'change-preview-input','control.mkv')
        assert not service(cleared,'redesignMediaAnalysis')['previewSource'], 'Previous input preview survived invalidation'
        case.inspect('leave-old-preview','move','--target','playButton')
        blue=case.inspect('fresh-input-preview','move','--target','progressSlider','--fraction-x','.55',
            '--await-service','redesignMediaAnalysis','--await-property','previewStatus','--await-value','""','--capture')
        frame=nodes(blue,'seekPreviewImage')
        assert len(frame)==1
        picture=Image.open((root/case.record['steps'][-1]['response']).with_suffix('.png')).convert('RGB')
        ratio=picture.width/blue['window']['width']
        item=frame[0]
        center=picture.getpixel((round((item['x']+item['width']/2)*ratio),round((item['y']+item['height']/2)*ratio)))
        assert max(abs(actual-expected) for actual,expected in zip(center,(32,64,128)))<16, ('New input preview does not show its actual blue frame',center)
        case.record['new_input_preview_rgb']=center
        case.click('preview-engine-tools','toolsButton')
        case.inspect('preview-switch-mpv','click','--name','MPV / Dolby Vision')
        switched=case.inspect('preview-engine-settled','snapshot','--await-core','engine_switching','--await-value','false')
        assert switched['core']['engine']=='mpv'
        case.inspect('close-preview-tools','key','--key','0x1000000')
        unavailable=case.inspect('mpv-preview-disclosure','move','--target','progressSlider','--fraction-x','.55','--capture')
        disclosure=service(unavailable,'redesignMediaAnalysis')
        assert not disclosure['previewSource'] and 'require VLC playback' in disclosure['previewStatus']
        case.close(True)
    finally: case.close()

def seek_policy():
    """Diagnostic comparison of VLC's public absolute-time seek and cue position seek."""
    case=Case('absolute-time-seek-probe',media=fixtures/'embedded-text.mkv')
    try:
        case.inspect('paused','snapshot','--await-core','state','--await-value','3')
        case.click('open-playback-tools','toolsButton')
        case.inspect('enable-timeline','click','--name','Show Subtitle Timeline on Seekbar',
            '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('3 embedded source cues; positions follow the selected track and subtitle delay.'))
        case.inspect('close-settings','key','--key','0x1000000')
        base=case.inspect('before-delay')['core']['subtitle_delay_ms']
        case.click('delay-later','subtitleDelayLater','--await-core','subtitle_delay_ms','--await-value',base+50)
        case.click('delay-earlier','subtitleDelayEarlier','--await-core','subtitle_delay_ms','--await-value',base)
        case.key('open-goto-time',0x54,modifiers=0x4000000,text='t')
        snapshot=case.inspect('time-editor')
        editors=[widget for widget in snapshot['widgets'] if widget['type']=='QTimeEdit']
        assert len(editors)==1,editors
        node=editors[0]['node']
        case.inspect('focus-time-editor','widget_click','--node',node)
        case.inspect('select-seconds','widget_key','--node',node,'--key','0x1000011')
        edited=case.inspect('one-second','widget_key','--node',node,'--key','0x1000013')
        assert any(widget['type']=='QTimeEdit' and widget.get('text')=='00H:00m:01s' for widget in edited['widgets']), 'Go to Time diagnostic did not enter one second'
        case.inspect('absolute-time-result','widget_click','--widget-text','Go','--await-core','time_seconds','--await-value','1','--await-tolerance','0.2')
        case.close(True)
    finally:case.close()


def updates():
    for mode, expected in [('unavailable',4),('malformed',4),('current',2),('newer',3)]:
        Peer.mode=mode
        reused=None
        if mode=='unavailable':
            first=Case('updates-first-welcome',welcome=True,updates=True)
            calls_before=len(Peer.calls)
            try:
                initial=first.inspect('first-welcome')
                assert initial['customization']['onboardingVisible']
                for page in ('theme','font'): first.click('next-'+page,'onboardingNext')
                first.inspect('reveal-free-font','focus','--target','onboardingFontFallback')
                first.click('shortcut-page','onboardingFontFallback')
                first.click('finish-first-start','onboardingNext')
                first.close(True)
                assert len(Peer.calls)==calls_before, 'Privacy setup did not defer the automatic request'
                reused=first.path/'profile'
            finally: first.close()
        case=Case('updates-' + mode,updates=True,welcome=reused is not None,reused_profile=reused)
        try:
            result=case.inspect('automatic-result','snapshot','--await-service','forkUpdateModel','--await-property','updateStatus','--await-value',expected,'--capture')
            if reused: assert not result['customization']['onboardingVisible']
            if expected!=3:
                assert not any(node.get('name') in ('Re-check','Open release page') and node['visible'] for node in result['tree'])
                assert not any(widget['type']=='UpdateDialog' for widget in result['widgets'])
            case.record['observed_status']=result['update']['status']
            if expected==3:
                assert result['update']['url']=='https://github.com/Darkaxt/vlc/releases/tag/redesign-v1.1.3'
                assert any(node.get('name')=='Open release page' and node['visible'] for node in result['tree']) or any(
                    widget.get('text','').replace('&','')=='Open release page' for widget in result['widgets'])
            if mode == 'unavailable':
                case.inspect('manual-check-library-ready','snapshot','--await-target','fullLibrary','--await-property','ready','--await-value','true')
                case.inspect('open-main-menu','click','--name','Main menu')
                case.inspect('open-help','widget_click','--menu-action','Help')
                failure=case.inspect('explicit-check-error','widget_click','--menu-action','Check for Updates...', '--await-service','forkUpdateModel','--await-property','updateStatus','--await-value','4','--capture')
                assert any(node.get('name')=='Re-check' and node['visible'] for node in failure['tree']) or any(widget.get('text')=='&Recheck version' for widget in failure['widgets'])
                Peer.mode='current'
                if any(node.get('name')=='Re-check' and node['visible'] for node in failure['tree']):
                    retried=case.inspect('manual-retry','click','--name','Re-check','--await-service','forkUpdateModel','--await-property','updateStatus','--await-value','2','--capture')
                else:
                    retried=case.inspect('manual-retry','widget_click','--widget-text','Recheck version','--await-service','forkUpdateModel','--await-property','updateStatus','--await-value','2','--capture')
                assert retried['update']['status']==2
                labels=[node.get('text','') for node in retried['tree'] if node['visible'] and 'You have the latest version' in node.get('text','')]
                labels += [widget.get('text','') for widget in retried['widgets'] if 'latest available Modern VLC Fork release' in widget.get('text','')]
                case.record['manual_current_version_labels']=labels
                assert labels and all('1.1.2' in text for text in labels), 'Update result does not show the fork version'
            case.close(True)
        finally: case.close()
    live=Case('updates-real-https',updates=True,live_updates=True)
    try:
        result=live.inspect('actual-https-result','snapshot','--await-service','forkUpdateModel','--await-property','updateStatus','--await-value','2')
        live.record['actual_https_status']=result['update']['status']
        live.close(True)
    finally: live.close()

try:
    if args.policies:
        assert args.policies.is_file()
        with (root / 'policies.stdout.json').open('wb') as output, (root / 'policies.stderr.log').open('wb') as errors:
            environment = dict(os.environ, TEMP=str(root), TMP=str(root))
            process = IsolatedProcess([str(args.policies.resolve()), str(fixtures)], root, environment, output, errors)
            policy_exit=process.wait()
        records['native_policy_exit_code']=policy_exit
        records['native_policy_executable_sha256']=hashlib.sha256(args.policies.read_bytes()).hexdigest()
        if policy_exit!=0:
            records.setdefault('failures',{})['native_policies']='Native production-policy executable exited '+str(policy_exit)+'; inspect policies.stdout.json and policies.stderr.log'
        else:
            records['native_policies'] = json.loads((root / 'policies.stdout.json').read_text())
            if not records['native_policies']['passed']:
                records.setdefault('failures',{})['native_policies']='Native policy result did not pass'
        save()
    try:
        verify_executable_icon()
    except AssertionError as failure:
        records.setdefault('failures',{})['executable_icon']=repr(failure)
        save()
    for name, operation in [('welcome',welcome),('playback',playback),('subtitles',subtitles),('preview',preview),('updates',updates),('seek-policy',seek_policy)]:
        if args.case=='subtitles-mpv':
            if name!='subtitles':continue
            operation=lambda:subtitles(engines=('mpv',))
        if args.case=='playback-subtitles' and name not in ('playback','subtitles'):continue
        if args.case=='subtitle-tracks-diagnostic':
            if name!='subtitles':continue
            operation=lambda:subtitles(False)
        if args.case=='integration-diagnostic':
            if name not in ('welcome','playback','subtitles'):continue
            if name=='subtitles':operation=lambda:subtitles(False)
        if name=='seek-policy' and args.case!='seek-policy':continue
        if args.case not in ('all','subtitles-mpv','playback-subtitles','integration-diagnostic','subtitle-tracks-diagnostic',name): continue
        try:
            operation()
        except Exception as failure:
            records.setdefault('failures',{})[name]=repr(failure)
            save()
            print(json.dumps({'workflow':name,'failure':repr(failure)}),flush=True)
            # Collect independent acceptance failures from this one complete
            # assembly, but never start another consumer after uncertain exit.
            assert not active_cases and not any(portable.iterdir()), 'Original native consumer/profile has not been released'
    records['passed']=not records.get('failures')
finally:
    records['http_peer_calls']=Peer.calls
    server.shutdown();server.server_close();thread.join()
    records['protected_profiles_after'] = profiles()
    records['protected_profiles_unchanged'] = records['protected_profiles_before'] == records['protected_profiles_after']
    if not records['protected_profiles_unchanged']:
        records.setdefault('failures',{})['protected_profiles']='Protected settings changed during observation; attribute the writer before accepting preservation'
        records['passed']=False
    save()
print(json.dumps({'passed':records['passed'],'result':str(root/'result.json')}),flush=True)
raise SystemExit(0 if records['passed'] else 1)

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
parser.add_argument('--case', choices=['welcome', 'playback', 'subtitles', 'subtitles-mpv', 'preview', 'icons', 'sidebar', 'menus', 'settings', 'preview-icons', 'correction', 'updates', 'playback-subtitles', 'seek-policy', 'integration-diagnostic', 'subtitle-tracks-diagnostic', 'all'], default='all')
parser.add_argument('--preview-media', type=Path, help='Read-only actual reported media for preview acceptance')
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
version_header=subprocess.check_output(['git','-C',str(repo),'show',records['source_commit']+':modules/gui/qt/dialogs/help/fork_release.hpp'],text=True)
fork_version=re.search(r'currentVersion\[\] = "([0-9.]+)"',version_header).group(1)
newer_version='.'.join(map(str,(*map(int,fork_version.split('.')[:2]),int(fork_version.split('.')[2])+1)))
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
        item=json.loads(payload)
        old=item['tag_name'][len('redesign-v'):]
        payload=json.dumps(item).replace('redesign-v'+old,'redesign-v'+fork_version).replace('Modern-VLC-Fork-'+old,'Modern-VLC-Fork-'+fork_version).encode('utf-8')
        status = 200
        if Peer.mode == 'unavailable': status, payload = 503, b'Unavailable test peer'
        elif Peer.mode == 'malformed': payload = b'{broken'
        elif Peer.mode == 'newer':
            item = json.loads(payload)
            old = item['tag_name'][len('redesign-v'):]
            encoded = json.dumps(item).replace('redesign-v' + old, 'redesign-v'+newer_version).replace('Modern-VLC-Fork-' + old, 'Modern-VLC-Fork-'+newer_version)
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
            if name in ('Show Subtitle Timeline on Seekbar','VLC','MPV'):
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
    def reveal(self,label,target,scroll):
        snapshot=self.inspect(label+'-locate','snapshot')
        seen=set()
        while True:
            widgets={item['node']:item for item in snapshot['widgets']}
            found=[item for item in widgets.values() if item['id']==target]
            assert len(found)==1,(target,found)
            if found[0]['center_visible']:return snapshot
            area=next(item for item in widgets.values() if item['id']==scroll)
            state=area['scroll_value']
            assert state not in seen,('native control cannot be revealed',target,area)
            seen.add(state)
            def y(item):
                result=item['y']
                while item['parent']>=0:
                    item=widgets[item['parent']];result+=item['y']
                return result
            delta=120 if y(found[0])<y(area) else -120
            snapshot=self.inspect(label+'-scroll-'+str(len(seen)),'widget_scroll','--target',scroll,'--delta',str(delta))
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


def settings_window_region(case, dialog):
    """Read Windows' actual clipping region, beyond the Qt paint capture."""
    def read():
        hwnd=W.HWND(int(dialog['native_id'],16))
        pid=W.DWORD()
        u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        assert pid.value==case.player.pid
        gdi=ctypes.WinDLL('gdi32',use_last_error=True)
        gdi.CreateRectRgn.argtypes=[ctypes.c_int]*4
        gdi.CreateRectRgn.restype=W.HANDLE
        gdi.PtInRegion.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_int]
        gdi.PtInRegion.restype=W.BOOL
        gdi.GetRgnBox.argtypes=[W.HANDLE,ctypes.POINTER(W.RECT)]
        gdi.DeleteObject.argtypes=[W.HANDLE]
        u.GetWindowRgn.argtypes=[W.HWND,W.HANDLE]
        region=gdi.CreateRectRgn(0,0,0,0)
        assert region
        try:
            assert u.GetWindowRgn(hwnd,region)==3,'Settings native window has no rounded clipping region'
            bounds=W.RECT()
            assert gdi.GetRgnBox(region,ctypes.byref(bounds))==3
            width,height=bounds.right,bounds.bottom
            assert bounds.left==0 and bounds.top==0 and width>0 and height>0
            corners=[bool(gdi.PtInRegion(region,x,y)) for x,y in
                ((0,0),(width-1,0),(0,height-1),(width-1,height-1))]
            assert not any(corners),('Native backdrop includes exterior corners',corners)
            assert gdi.PtInRegion(region,width//2,height//2)
            return {'native_id':dialog['native_id'],'region':'COMPLEXREGION',
                'bounds':[width,height],'exterior_corners_clipped':True}
        finally:gdi.DeleteObject(region)
    return owned_native_read(case,read)


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
            # Popup itself is a QObject; only its rendered children are in
            # the QQuickItem tree. Its 40px window inset determines the width.
            if shortcuts['window']['width']>=1040*key_scale:
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
                initial=case.inspect('library-ready', 'snapshot', '--await-target','fullLibrary','--await-property','ready','--await-value','true')
                drop_fixture(case,'drop-video',name)
                result=case.inspect('main-player-visible','snapshot','--await-target','playerView','--await-property','visible','--await-value','true','--capture')
                assert (initial['window']['width'],initial['window']['height'])==(result['window']['width'],result['window']['height']), 'Default video open resized the chosen window'
                try:assert_window(case,result)
                except AssertionError as failure:
                    if args.case!='integration-diagnostic':raise
                    case.record['known_geometry_failure']=repr(failure)
                    case.close(False)
                    continue
                case.record['source']=name
                case.close(True)
            finally: case.close()
        fixed=Case('fixed-size-'+engine,engine=engine)
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
        opted=Case('opt-in-video-size-'+engine,engine=engine,extra=['--qt-video-autoresize'])
        try:
            opted.inspect('library-ready','snapshot','--await-target','compactLibrary','--await-property','ready','--await-value','true')
            drop_fixture(opted,'opt-in-wide-video','wide.mkv')
            resized=opted.inspect('opt-in-main-view','snapshot','--await-target','playerView','--await-property','visible','--await-value','true','--capture')
            assert_window(opted,resized)
            opted.close(True)
        finally: opted.close()
    for engine,scale in (('vlc','1.5'),('mpv','2')):
        case=Case('scaled-video-'+engine,engine=engine,scale=scale)
        try:
            case.inspect('library-ready','snapshot','--await-target','compactLibrary','--await-property','ready','--await-value','true')
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

def open_vlc_commands(case,label):
    case.inspect(label+'-main-menu','click','--name','Main menu')
    case.click(label+'-settings','mainMenuGlobalSettings')
    case.reveal(label+'-reveal-advanced','preferencesAdvanced0','preferencesScroll0')
    case.native(label+'-advanced','preferencesAdvanced0')
    case.reveal(label+'-reveal-commands','preferencesAction-vlc-commands','preferencesScroll0')
    return case.native(label+'-commands','preferencesAction-vlc-commands')

def subtitle_menu(case, label, enabled):
    open_vlc_commands(case,label)
    result=case.inspect(label + '-submenu', 'widget_click', '--menu-action', 'Subtitles', '--capture')
    actions=[action for widget in result['widgets'] for action in widget.get('actions', [])]
    tracks=[action for action in actions if action['text'].replace('&','').split('\t')[0]=='Sub Track']
    assert len(tracks)==1 and tracks[0]['enabled']==enabled, tracks
    assert any(action['enabled'] and action['text'].replace('&','').startswith('Add Subtitle File') for action in actions)
    case.inspect(label + '-dismiss','key','--key','0x1000000')
    case.inspect(label + '-dismiss-root','key','--key','0x1000000')
    case.native(label+'-close-settings','preferencesClose')


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
                case.inspect('choose-engine-'+target,'click','--name','MPV' if target=='mpv' else 'VLC')
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
            open_vlc_commands(case,'native-add-subtitle')
            case.inspect('native-subtitle-submenu','widget_click','--menu-action','Subtitles')
            case.inspect('native-add-subtitle-dialog','widget_click','--menu-action','Add Subtitle File...')
            case.native('native-file-name-focus','fileNameEdit')
            case.inspect('select-file-name','widget_key','--target','fileNameEdit','--key','0x41','--modifiers','0x4000000','--text','a')
            case.inspect('enter-native-subtitle-file','widget_key','--target','fileNameEdit','--key','0','--text',str(fixtures/'german.srt'))
            chosen=case.inspect('accept-native-subtitle-file','widget_key','--target','fileNameEdit','--key','0x1000004',
                '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('2 source cues; positions follow subtitle FPS and track delay. Duration filters can extend the displayed cue ends.'))
            assert service(chosen)['subtitleLoaded'] and len(service(chosen)['cues'])==2
            case.native('close-native-subtitle-settings','preferencesClose')
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
    media=args.preview_media.resolve() if args.preview_media else fixtures/'preview-4k-long-gop.mkv'
    assert media.is_file()
    case=Case('seek-preview',media=media)
    try:
        paused=case.inspect('paused','snapshot','--await-core','state','--await-value','3')
        position=311/paused['core']['length_seconds'] if args.preview_media else .55
        case.record['input_sha256']=hashlib.file_digest(media.open('rb'),'sha256').hexdigest()
        def popup_pixels(snapshot):
            frame=nodes(snapshot,'seekPreviewImage')
            assert len(frame)==1 and frame[0]['status']=='Ready', frame
            picture=Image.open((root/case.record['steps'][-1]['response']).with_suffix('.png')).convert('RGB')
            ratio=picture.width/snapshot['window']['width']
            item=frame[0]
            bounds=tuple(round(value*ratio) for value in (item['x'],item['y'],item['x']+item['width'],item['y']+item['height']))
            pixels=picture.crop(bounds).resize((160,90)).convert('RGB')
            values=list(pixels.getdata())
            # The reported 5:11 frame is a dark menu on a mostly black video.
            # Reject blank output from luminance variation, not an assumption
            # that a large part of every legitimate frame must be bright.
            levels=[max(rgb) for rgb in values]
            assert max(levels)-min(levels)>32 and len(set(levels))>32, 'Rendered popup is blank/black'
            return pixels
        cold=case.inspect('cold-preview','move','--target','progressSlider','--fraction-x',position,
            '--await-service','redesignMediaAnalysis','--await-property','previewStatus','--await-value','""','--capture')
        first=service(cold,'redesignMediaAnalysis')
        assert first['previewSource'] and abs(first['previewPosition']-position)<.02
        first_pixels=popup_pixels(cold)
        case.inspect('leave-preview','move','--target','playButton')
        warm=case.inspect('cached-preview','move','--target','progressSlider','--fraction-x',position,
            '--await-service','redesignMediaAnalysis','--await-property','previewStatus','--await-value','""','--capture')
        cached=service(warm,'redesignMediaAnalysis')
        assert cached['previewLatencyMS']<16.7, cached
        case.record['cold_decode_ms']=first['previewLatencyMS']
        case.record['cached_publication_ms']=cached['previewLatencyMS']
        assert first['previewLatencyMS']<1000, 'Uncached local preview still takes several seconds'
        assert popup_pixels(warm).tobytes()==first_pixels.tobytes(), 'Cached rendered frame changed'
        if args.preview_media:
            second=case.inspect('distinct-actual-frame','move','--target','progressSlider','--fraction-x',693/paused['core']['length_seconds'],
                '--await-service','redesignMediaAnalysis','--await-property','previewPosition',
                '--await-value',693/paused['core']['length_seconds'],'--await-tolerance','0.001','--capture')
            second_pixels=popup_pixels(second)
            difference=sum(abs(a-b) for a,b in zip(first_pixels.tobytes(),second_pixels.tobytes()))/len(first_pixels.tobytes())
            assert difference>10, ('Different source positions returned the same/incorrect frame',difference)
            case.record['actual_frame_mean_difference']=difference
        for position in (.1,.2,.3,.4,.5,.6,.7,.8,.9):
            case.inspect('continuous-' + str(position),'move','--target','progressSlider','--fraction-x',position)
        latest=case.inspect('latest-preview','snapshot','--await-service','redesignMediaAnalysis','--await-property','previewPosition','--await-value','0.9','--await-tolerance','.02','--capture')
        case.record['latest_preview']=service(latest,'redesignMediaAnalysis')
        assert abs(case.record['latest_preview']['previewPosition']-.9)<.02
        cleared=drop_fixture(case,'change-preview-input','control.mkv')
        # A stationary hover may already request and publish the new input's
        # frame while the drop finishes. Its revision must replace the old
        # input; the actual new blue pixels are checked below.
        assert service(cleared,'redesignMediaAnalysis')['previewSource']!=case.record['latest_preview']['previewSource'], 'Previous input preview survived invalidation'
        case.inspect('leave-old-preview','move','--target','playButton')
        blue=case.inspect('fresh-input-preview','move','--target','progressSlider','--fraction-x','.55',
            '--await-service','redesignMediaAnalysis','--await-property','previewPosition','--await-value','0.55','--await-tolerance','0.001','--capture')
        frame=nodes(blue,'seekPreviewImage')
        assert len(frame)==1
        picture=Image.open((root/case.record['steps'][-1]['response']).with_suffix('.png')).convert('RGB')
        ratio=picture.width/blue['window']['width']
        item=frame[0]
        center=picture.getpixel((round((item['x']+item['width']/2)*ratio),round((item['y']+item['height']/2)*ratio)))
        assert max(abs(actual-expected) for actual,expected in zip(center,(32,64,128)))<16, ('New input preview does not show its actual blue frame',center)
        case.record['new_input_preview_rgb']=center
        case.click('preview-engine-tools','toolsButton')
        case.inspect('preview-switch-mpv','click','--name','MPV')
        switched=case.inspect('preview-engine-settled','snapshot','--await-core','engine_switching','--await-value','false')
        assert switched['core']['engine']=='mpv'
        case.inspect('close-preview-tools','key','--key','0x1000000')
        unavailable=case.inspect('mpv-preview-disclosure','move','--target','progressSlider','--fraction-x','.55','--capture')
        disclosure=service(unavailable,'redesignMediaAnalysis')
        assert not disclosure['previewSource'] and 'require VLC playback' in disclosure['previewStatus']
        case.close(True)
    finally: case.close()

def icons():
    for scale in ('1','1.25','1.5','2'):
        case=Case('transport-icons-'+scale,scale=scale,media=fixtures/'control.mkv',
            extra=(str(fixtures/'control.mkv'),str(fixtures/'embedded-text.mkv')))
        try:
            case.inspect('paused','snapshot','--await-core','state','--await-value','3')
            case.inspect('middle-item','click','--name','Next','--await-core','url',
                '--await-value',json.dumps((fixtures/'embedded-text.mkv').as_uri()))
            case.inspect('middle-item-playing','snapshot','--await-core','state','--await-value','2')
            case.click('pause-middle-item','playButton','--await-core','state','--await-value','3')
            for state in ('play','pause'):
                case.inspect(state+'-controls','move','--target','playButton')
                snapshot=case.inspect(state+'-native-sampling','snapshot','--capture')
                glyphs=[node for node in snapshot['tree'] if node['visible'] and node['id'].startswith('playerGlyph-')]
                assert any(node['id']=='playerGlyph-'+state for node in glyphs)
                for node in glyphs:
                    assert not node['mipmap'] and not node['smooth'], node
                if state=='play':
                    case.click('play-action','playButton','--await-core','state','--await-value','2')
            case.click('pause-action','playButton','--await-core','state','--await-value','3')
            case.inspect('main-menu-viewport','resize','--width','1280','--height','800')
            menu=case.inspect('main-menu-native-scale','click','--name','Main menu','--capture')
            assert nodes(menu,'mainMenuGlobalSettings'), 'Direct Settings entry missing at this display scale'
            case.inspect('close-main-menu-native-scale','key','--key','0x1000000')
            case.close(True)
        finally: case.close()

def sidebar():
    for engine in ('vlc','mpv'):
        case=Case('sidebar-transition-'+engine,engine=engine,media=fixtures/'control.mkv')
        try:
            case.inspect('paused','snapshot','--await-core','state','--await-value','3')
            for playing in (False,True):
                if playing:
                    case.click('start-playing','playButton','--await-core','state','--await-value','2')
                state='playing' if playing else 'paused'
                for opened in (True,False):
                    label=state+('-open' if opened else '-collapse')
                    snapshot=case.inspect(label,'click','--name','Media browser','--capture')
                    surfaces=nodes(snapshot,'playerVideoSurface')
                    assert len(surfaces)==1
                    surface=surfaces[0]
                    dpr=snapshot['window']['dpr']
                    actual=snapshot['video_backdrop']['surface_at_placement_px']
                    assert abs(actual['width']-surface['width']*dpr)<=1, (label,actual,surface)
                    assert abs(actual['height']-surface['height']*dpr)<=1, (label,actual,surface)
                    if opened: assert surface['x']>0
                    else: assert abs(surface['x'])<1 and abs(surface['width']-snapshot['window']['width'])<1
                    case.record.setdefault('surface_transitions',[]).append({
                        'state':state,'opened':opened,'surface_at_placement_px':actual,
                        'qml_viewport':{key:surface[key] for key in ('x','y','width','height')}})
            case.close(True)
        finally: case.close()

def menus():
    """Reference menu, real Settings route and Playback controls as one workflow."""
    case=Case('figma-player-menus',media=fixtures/'control.mkv')
    try:
        case.inspect('reference-viewport','resize','--width','1280','--height','900')
        snapshot=case.inspect('paused','snapshot','--await-core','state','--await-value','3')
        elapsed=nodes(snapshot,'playerElapsedTime')
        assert len(elapsed)==1 and re.fullmatch(r'\d{2,}:\d{2}:\d{2}',elapsed[0]['text']), elapsed
        opened=case.inspect('main-menu','click','--name','Main menu','--capture')
        expected=['Open File(s)','Open Folder','Open Network Stream','Open Disc','Open Capture Device',
            'Convert','Open Recent','Profile','Keyboard Shortcuts','Customize Player','Settings','About VLC']
        rows=[]
        for label in expected:
            matches=[item for item in opened['tree'] if item['visible'] and item.get('name')==label and item.get('actions')]
            assert len(matches)==1, (label,matches)
            rows.append(matches[0])
        assert [item['y'] for item in rows]==sorted(item['y'] for item in rows)
        assert all(abs(item['height']-48)<1 for item in rows), rows
        assert max(item['x'] for item in rows)-min(item['x'] for item in rows)<1
        primary=[item for item in opened['tree'] if item['visible'] and item.get('actions') and
                 abs(item.get('x',-1000)-rows[0]['x'])<1 and item.get('height',0)>24]
        assert len(primary)==12, primary
        case.record['reference_menu_rows']=rows
        case.inspect('recent-submenu','click','--name','Open Recent','--capture')
        case.inspect('close-recent-submenu','key','--key','0x1000000')
        settings=case.click('direct-global-settings','mainMenuGlobalSettings','--capture')
        assert any(widget['id']=='redesignPreferences' for widget in settings['widgets'])
        assert any(widget['id']=='preferencesHeading' and widget.get('text')=='Global Settings' for widget in settings['widgets'])
        case.native('cancel-global-settings','preferencesClose')
        case.inspect('keyboard-main-menu-focus','focus','--name','Main menu')
        # Accessibility SetFocus uses OtherFocusReason, which intentionally
        # preserves player hotkeys. Traverse with Tab to establish keyboard
        # visual focus through the real Qt navigation path before Space.
        case.inspect('keyboard-main-menu-backtab','key','--key','0x1000002','--modifiers','0x2000000')
        focused=case.inspect('keyboard-main-menu-tab','key','--key','0x1000001')
        assert any(item.get('name')=='Main menu' and item.get('focused') and item['visible'] for item in focused['tree'])
        reopened=case.inspect('reopen-main-menu','key','--key','0x20','--text',' ')
        assert nodes(reopened,'mainMenuGlobalSettings'), 'Keyboard did not open the main menu'
        case.inspect('profile-keyboard-focus','focus','--name','Profile')
        profile=case.inspect('profile-submenu','key','--key','0x1000014','--capture')
        assert any(item['visible'] and item.get('name')=='New / Manage Profiles…' for item in profile['tree'])
        case.inspect('close-profile-submenu','key','--key','0x1000000')
        case.inspect('close-main-menu','key','--key','0x1000000')
        playback=case.click('playback-panel','toolsButton','--capture')
        labels=['Show Subtitle Timeline on Seekbar','Show Statistics','Reverse','Sleep Timer','Audio Visualizer','Speed']
        positions=[]
        for label in labels:
            matches=[item for item in playback['tree'] if item['visible'] and item.get('text')==label]
            assert matches, label
            positions.append(min(item['y'] for item in matches))
        assert positions==sorted(positions), positions
        timer=case.inspect('timer-focus','focus','--name','Sleep timer')
        case.inspect('timer-arm','key','--key','0x1000015','--await-service','redesignMediaTools','--await-property','sleepMinutes','--await-value','1')
        case.inspect('timer-cancel','key','--key','0x1000010','--await-service','redesignMediaTools','--await-property','sleepMinutes','--await-value','0')
        case.inspect('speed-value-focus','focus','--name','Playback speed value')
        case.inspect('speed-value-select','key','--key','0x41','--modifiers','0x4000000','--text','a')
        case.inspect('speed-value-input','key','--key','0','--text','1.25x')
        edited=case.inspect('speed-value-apply','key','--key','0x1000004','--await-core','rate','--await-value','1.25','--await-tolerance','.001')
        slider=nodes(edited,'speedSlider')[0]
        fraction=(4+(slider['width']-8)*(.75-.25)/1.75)/slider['width']
        case.inspect('speed-slider-apply','click','--target','speedSlider','--fraction-x',fraction,'--await-core','rate','--await-value','0.75','--await-tolerance','.011')
        case.inspect('speed-reset-focus','focus','--name','Playback speed value')
        case.inspect('speed-reset-select','key','--key','0x41','--modifiers','0x4000000','--text','a')
        case.inspect('speed-reset-input','key','--key','0','--text','1x')
        case.inspect('speed-reset-apply','key','--key','0x1000004','--await-core','rate','--await-value','1','--await-tolerance','.001')
        case.inspect('close-playback-panel','key','--key','0x1000000')
        case.inspect('library-menu-route','click','--name','Back to media','--await-target','viewLoader',
            '--await-property','source','--await-value',json.dumps('qrc:///qt/qml/VLC/Player/PlayerLibraryDisplay.qml'))
        case.inspect('library-menu-ready','snapshot','--await-target','viewLoader','--await-property','status','--await-value','1')
        library_menu=case.inspect('library-main-menu','click','--name','Main menu','--capture')
        assert nodes(library_menu,'mainMenuGlobalSettings')
        library_settings=case.click('library-direct-global-settings','mainMenuGlobalSettings','--capture')
        assert any(widget['id']=='redesignPreferences' for widget in library_settings['widgets'])
        case.native('cancel-library-global-settings','preferencesClose')
        case.close(True)
    finally: case.close()


def settings():
    """All reference categories, real scrolling, DPI/theme and retained edits."""
    reference=json.loads((repo/'doc/redesign/resources/m4-settings-reference.json').read_text())
    corrections={key.casefold():value for key,value in reference['copy_corrections'].items()}
    categories=reference['categories']
    def text(value):
        value=value.strip().rstrip(':').casefold()
        return corrections.get(value,value).casefold()
    def widget(snapshot,identity):
        matches=[row for row in snapshot['widgets'] if row['id']==identity]
        assert len(matches)==1,(identity,matches)
        return matches[0]
    def select(case,index,label):
        case.native(label+'-nav','preferencesCategories')
        result=case.inspect(label+'-home','widget_key','--target','preferencesCategories','--key','0x1000010')
        for step in range(index):
            result=case.inspect(label+'-down-'+str(step),'widget_key','--target','preferencesCategories','--key','0x1000015')
        selected=[row['columns'][0] for row in widget(result,'preferencesCategories')['rendered_rows'] if row['selected']]
        assert selected==[categories[index]['category']],selected
        return result
    def check_labels(snapshot,index,expanded):
        frames=categories[index]['frames']
        widgets={row['node']:row for row in snapshot['widgets']}
        area=widget(snapshot,'preferencesScroll'+str(index))
        def belongs(row):
            while row['parent']>=0:
                row=widgets[row['parent']]
                if row['node']==area['node']:return True
            return False
        def y(row):
            result=row['y']
            while row['parent']>=0:
                row=widgets[row['parent']];result+=row['y']
            return result
        rows=[row for row in widgets.values() if belongs(row)]
        # Lazy hidden sections are not substitutes for the category under test.
        label_rows=[row for row in sorted(rows,key=lambda row:(y(row),row['x']))
                if row['type']=='QLabel' and not row['id'].startswith(('description-','equalizerValue'))
                and (not row['id'].startswith('equalizerFrequency') or row['id']=='equalizerFrequencyPreamp')]
        labels=[text(row.get('text','')) for row in label_rows]
        for frame in frames[:2 if expanded else 1]:
            information={text(row['text']):row['information'] for row in frame['labels']}
            if index==2:information['last.fm password']=information.get('last.fm username',True)
            expected=[row['text'] for row in frame['labels']]
            if not expanded and categories[index]['category']=='Performance':expected=expected[:expected.index('Developer')]
            expected=[text(label) for label in expected if label not in ('Search','12.0 dB')]
            if index==2:
                names=[i for i,label in enumerate(expected) if label=='last.fm username']
                if len(names)==2:expected[names[1]]='last.fm password'
            if index==3:
                # The prototype repeats its wheel controls under Remotes.
                expected=list(dict.fromkeys(expected))
            position=0
            for label in expected:
                assert label in labels[position:],(categories[index]['category'],frame['source_frame'],label,labels[position:])
                position=labels.index(label,position)
                caption=label_rows[position]
                owner=caption
                while owner['parent']>=0 and not owner['id'].startswith('preference-'):
                    owner=widgets[owner['parent']]
                if owner['id'].startswith('preference-'):
                    observed=any(row['id'].startswith('help-') and row['parent']==caption['parent'] for row in rows)
                    assert observed==information[label],('Reference information glyph differs',categories[index]['category'],label,observed,information[label])
                position+=1
        ids=[row['id'] for row in snapshot['widgets'] if row['id'].startswith(('preference-','value-'))]
        assert len(ids)==len(set(ids)),('duplicate settings view identities',ids)
        if index==2:
            password=widget(snapshot,'value-lastfm-password')
            assert password.get('text')=='[redacted]'
    def capture(case,label,index,dark):
        result=case.inspect(label,'snapshot','--capture')
        dialog=widget(result,'redesignPreferences')
        assert abs(dialog['dpr']-float(case.record['scale']))<0.01
        native_region=settings_window_region(case,dialog)
        file=next(row for row in result['widget_captures'] if row['widget']==dialog['node'])
        assert file['saved']
        with Image.open(case.evidence/file['file']) as original:
            image=original.convert('RGBA')
            assert image.getpixel((0,0))[3]==0,('opaque outside rounded settings card',label)
            rgb=image.getpixel((round(image.width*0.7),round(30*dialog['dpr'])))[:3]
            expected=(7,7,7) if dark else (213,213,213)
            assert max(abs(a-b) for a,b in zip(rgb,expected))<=1,('header band',label,rgb)
        case.record.setdefault('settings_views',[]).append({'label':label,'category':categories[index]['category'],'capture':file['file'],'dpr':dialog['dpr'],'native_region':native_region})
        return result
    def edit(case,label,target,value,scroll):
        case.reveal(label+'-reveal',target,scroll)
        case.native(label+'-focus',target)
        case.inspect(label+'-select','widget_key','--target',target,'--key','0x41','--modifiers','0x4000000')
        case.inspect(label+'-type','widget_key','--target',target,'--key','0','--text',str(value))
        return case.inspect(label+'-commit','widget_key','--target',target,'--key','0x1000001')
    def behaviour(case):
        opened=case.inspect('behaviour-open','key','--key','0x50','--modifiers','0x4000000')
        original_config=opened['settings_config']
        first=select(case,2,'behaviour-privacy')
        assert widget(first,'value-save-playback-position')['checked']
        case.reveal('scrobbler-reveal','value-extraintf-audioscrobbler','preferencesScroll2')
        scoped=case.native('scrobbler-stage','value-extraintf-audioscrobbler')
        assert widget(scoped,'value-lastfm-username')['enabled']
        select(case,3,'behaviour-controls')
        case.reveal('remote-reveal','value-extraintf-http','preferencesScroll3')
        scoped=case.native('remote-stage','value-extraintf-http')
        assert widget(scoped,'value-http-port')['enabled']
        # Search exercises the native module route, not a second configuration
        # owner. Both presentation switches must track edits to that same key.
        case.native('search-shared-focus','preferencesSearch')
        case.inspect('search-shared-type','widget_key','--target','preferencesSearch','--key','0','--text','extraintf')
        case.native('search-shared-results','preferencesResults')
        case.inspect('search-shared-first','widget_key','--target','preferencesResults','--key','0x1000010')
        shared=case.inspect('search-shared-open','widget_key','--target','preferencesResults','--key','0x1000004')
        modules=widget(shared,'value-native-extraintf')['text'].split(':')
        assert 'audioscrobbler' in modules and 'http' in modules,modules
        edit(case,'shared-native-edit','value-native-extraintf','gestures','preferencesScroll2')
        scoped=select(case,2,'shared-privacy')
        assert not widget(scoped,'value-extraintf-audioscrobbler')['checked']
        scoped=select(case,3,'shared-controls')
        assert not widget(scoped,'value-extraintf-http')['checked']
        case.native('cancel-shared-draft','preferencesCancel')
        case.inspect('reopen-after-cancel','key','--key','0x50','--modifiers','0x4000000')
        scoped=select(case,2,'cancelled-privacy')
        assert not widget(scoped,'value-extraintf-audioscrobbler')['checked']
        edit(case,'history-exclusion','value-history-exclude','private-*;*.secret','preferencesScroll2')
        case.reveal('position-off-reveal','value-save-playback-position','preferencesScroll2')
        case.native('position-off','value-save-playback-position')
        select(case,3,'save-controls')
        edit(case,'short-jump','value-short-jump-size','7','preferencesScroll3')
        select(case,6,'save-audio')
        case.reveal('equalizer-reveal','preferencesAction-equalizer','preferencesScroll6')
        case.native('equalizer-open','preferencesAction-equalizer')
        edit(case,'equalizer-band','equalizerValue0','2.5','preferencesScroll6')
        select(case,1,'save-interface')
        case.reveal('tree-view-reveal','value-playlist-tree','preferencesScroll1')
        case.native('tree-view-stage','value-playlist-tree')
        select(case,0,'save-general')
        case.reveal('save-advanced-reveal','preferencesAdvanced0','preferencesScroll0')
        case.native('save-advanced','preferencesAdvanced0')
        edit(case,'invalid-extra','value-extra-options','--m4-invalid-option=1','preferencesScroll0')
        failed=case.native('reject-invalid-save','preferencesSave')
        assert any('m4-invalid-option' in row.get('text','') for row in failed['widgets'])
        case.inspect('dismiss-invalid-save','widget_click','--widget-text','OK')
        scoped=select(case,2,'failed-save-retains-draft')
        assert widget(scoped,'value-history-exclude')['text']=='private-*;*.secret'
        select(case,0,'correct-extra-general')
        edit(case,'valid-extra','value-extra-options','--rate=1.5','preferencesScroll0')
        config_file=portable/'vlcrc'
        original_file=hashlib.sha256(config_file.read_bytes()).hexdigest()
        k.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,W.LPVOID,W.DWORD,W.DWORD,W.HANDLE]
        k.CreateFileW.restype=W.HANDLE
        held=k.CreateFileW(str(config_file),0x80000000,1,None,3,0x80,None)
        assert held and held!=ctypes.c_void_p(-1).value,ctypes.WinError(ctypes.get_last_error())
        try:
            failed=case.native('locked-save-rejected','preferencesSave')
            assert any('staged edits remain' in row.get('text','') for row in failed['widgets'])
            assert failed['settings_config']==original_config,('Native configuration was not rolled back',failed['settings_config'],original_config)
            assert hashlib.sha256(config_file.read_bytes()).hexdigest()==original_file
        finally:assert k.CloseHandle(held)
        case.inspect('locked-save-dismiss','widget_click','--widget-text','OK')
        retained=select(case,2,'locked-save-retains-privacy-draft')
        assert widget(retained,'value-history-exclude')['text']=='private-*;*.secret'
        assert not widget(retained,'value-save-playback-position')['checked']
        saved=case.native('save-settings-draft','preferencesSave')
        assert saved['settings_config']=={'save-playback-position':0,'short-jump-size':7,'playlist-tree':1}
        case.click('tree-queue-open','playqueueToggle')
        queue=case.inspect('tree-queue-ready','snapshot','--await-target','playlistpopup','--await-property','width',
            '--await-value','300','--await-comparison','at_least','--capture')
        folders=[row for row in queue['tree'] if row['id'].startswith('queueFolder-') and row['visible']]
        assert len(folders)==1,folders
        folder=folders[0]['id']
        collapsed=case.click('tree-folder-collapse',folder,'--capture')
        assert not any(row['visible'] and row['id']=='delegate' and row.get('url')==(fixtures/'control.mkv').as_uri()
                       for row in collapsed['tree'])
        expanded=case.click('tree-folder-expand',folder,'--capture')
        assert any(row['visible'] and row['id']=='delegate' and row.get('url')==(fixtures/'control.mkv').as_uri()
                   for row in expanded['tree'])
        case.click('tree-queue-close','playqueueToggle')
        case.inspect('readback-saved-settings','key','--key','0x50','--modifiers','0x4000000')
        scoped=select(case,2,'saved-privacy')
        assert widget(scoped,'value-history-exclude')['text']=='private-*;*.secret'
        assert not widget(scoped,'value-save-playback-position')['checked']
        scoped=select(case,3,'saved-controls')
        assert widget(scoped,'value-short-jump-size')['value']==7
        select(case,6,'saved-audio')
        case.reveal('saved-equalizer-reveal','preferencesAction-equalizer','preferencesScroll6')
        scoped=case.native('saved-equalizer-open','preferencesAction-equalizer')
        assert widget(scoped,'equalizerValue0')['value']==2.5
        select(case,10,'plugin-rescan-performance')
        case.reveal('plugin-rescan-reveal','preferencesAction-rescan-plugins','preferencesScroll10')
        scanned=case.native('plugin-rescan','preferencesAction-rescan-plugins','--await-service','redesignPreferences',
            '--await-property','pluginScanActive','--await-value','false')
        assert any('plugin cache has been rebuilt' in row.get('text','') for row in scanned['widgets'])
        case.inspect('plugin-rescan-dismiss','widget_click','--widget-text','OK')
        case.native('behaviour-close','preferencesClose')
        case.record['settings_behaviour']={'shared_native_and_reference_draft':True,'cancel':True,
            'invalid_save_preserves_draft':True,'locked_save_rolls_back_native_memory_and_file':True,
            'failed_save_preserves_draft_for_retry':True,'typed_save_readback':True,'equalizer':True,'native_plugin_rescan':True}
    for scale in ('1','1.5','2'):
        case=Case('settings-'+scale.replace('.','-'),scale=scale,media=fixtures/'control.mkv')
        try:
            for dark in (True,False):
                case.inspect('open-theme-'+str(dark),'key','--key','0x50','--modifiers','0x4000000')
                select(case,0,'theme-general-'+str(dark))
                case.native('stage-theme-'+str(dark),'preferencesTheme'+('2' if dark else '1'))
                case.native('save-theme-'+str(dark),'preferencesSave')
                case.inspect('reopen-theme-'+str(dark),'key','--key','0x50','--modifiers','0x4000000')
                for narrow in (False,True):
                    case.inspect('viewport-'+str(dark)+'-'+str(narrow),'widget_resize','--target','redesignPreferences',
                                 '--width','740' if narrow else '1048','--height','700' if narrow else '865')
                    for index,category in enumerate(categories):
                        label=('dark' if dark else 'light')+('-narrow-' if narrow else '-normal-')+str(index)
                        snapshot=select(case,index,label)
                        button=widget(snapshot,'preferencesAdvanced'+str(index))
                        if button.get('checked'):
                            case.reveal(label+'-reveal-collapse',button['id'],'preferencesScroll'+str(index))
                            case.native(label+'-collapse',button['id'])
                        if index==6:
                            eq=widget(snapshot,'preferencesAction-equalizer')
                            if eq.get('checked'):
                                case.reveal(label+'-reveal-close-equalizer',eq['id'],'preferencesScroll6')
                                case.native(label+'-close-equalizer',eq['id'])
                        case.inspect(label+'-top','widget_scroll','--target','preferencesScroll'+str(index),'--delta','24000')
                        snapshot=capture(case,label+'-basic',index,dark)
                        check_labels(snapshot,index,False)
                        case.reveal(label+'-reveal-advanced','preferencesAdvanced'+str(index),'preferencesScroll'+str(index))
                        expanded=case.native(label+'-expand','preferencesAdvanced'+str(index))
                        if index==6:
                            eq=widget(expanded,'preferencesAction-equalizer')
                            if not eq.get('checked'):
                                case.reveal(label+'-reveal-equalizer',eq['id'],'preferencesScroll6')
                                case.native(label+'-equalizer',eq['id'])
                        snapshot=capture(case,label+'-expanded',index,dark)
                        check_labels(snapshot,index,True)
                        case.inspect(label+'-expanded-top','widget_scroll','--target','preferencesScroll'+str(index),'--delta','24000')
                        seen=set()
                        while True:
                            snapshot=capture(case,label+'-page-'+str(len(seen)),index,dark)
                            area=widget(snapshot,'preferencesScroll'+str(index))
                            state=area['scroll_value']
                            if state==area['scroll_maximum']:break
                            assert state not in seen,('settings page cannot scroll to end',label,area)
                            seen.add(state)
                            # A real wheel event advances the owned Qt viewport;
                            # observed scrollbar state, not elapsed time, ends it.
                            case.inspect(label+'-scroll-'+str(len(seen)),'widget_scroll','--target',area['id'],'--delta','-480')
                case.native('close-settings-'+str(dark),'preferencesClose')
            if scale=='1':behaviour(case)
            case.close(True)
        finally:case.close()
        if scale=='1':
            for name,engine,extra,rate in [(name+'-'+engine,engine,extra,rate) for engine in ('vlc','mpv')
                    for name,extra,rate in [('saved-extra-startup',(),1.5),('explicit-extra-priority',('--rate=1.75',),1.75)]]:
                restarted=Case(name,engine=engine,media=fixtures/'control.mkv',reused_profile=case.path/'profile',extra=extra)
                try:
                    result=restarted.inspect('saved-rate-effective','snapshot','--await-core','rate','--await-value',str(rate))
                    assert abs(result['core']['rate']-rate)<0.001
                    restarted.inspect('restart-settings','key','--key','0x50','--modifiers','0x4000000')
                    result=select(restarted,2,'restart-privacy')
                    assert widget(result,'value-history-exclude')['text']=='private-*;*.secret'
                    assert not widget(result,'value-save-playback-position')['checked']
                    restarted.native('restart-close-settings','preferencesClose')
                    restarted.close(True)
                finally:restarted.close()

    # A displayed font fallback must not replace the user's unavailable font
    # when the new menu saves an unrelated native setting.
    seed=root/'settings-missing-font-seed'
    seed.mkdir()
    families={'freetype-font':'M4 Missing Family 20261103',
              'freetype-monofont':'M4 Missing Mono Family 20261103'}
    (seed/'vlcrc').write_text('metadata-network-access=0\n'+
        ''.join(key+'='+value+'\n' for key,value in families.items()),encoding='utf-8')
    legacy=Case('settings-missing-font-preservation',media=fixtures/'control.mkv',reused_profile=seed)
    try:
        legacy.inspect('legacy-font-open','key','--key','0x50','--modifiers','0x4000000')
        select(legacy,7,'legacy-font-subtitles')
        legacy.reveal('legacy-font-advanced-reveal','preferencesAdvanced7','preferencesScroll7')
        legacy.native('legacy-font-advanced','preferencesAdvanced7')
        select(legacy,2,'legacy-font-unrelated-privacy')
        legacy.reveal('legacy-font-position-reveal','value-save-playback-position','preferencesScroll2')
        legacy.native('legacy-font-unrelated-edit','value-save-playback-position')
        legacy.native('legacy-font-save','preferencesSave')
        legacy.close(True)
        saved=(legacy.path/'profile/vlcrc').read_text(encoding='utf-8')
        for key,value in families.items():
            found=re.search(r'^'+re.escape(key)+r'=(.*)$',saved,re.M)
            assert found and found.group(1).strip()==value,('Missing font was replaced',key,found.group(1) if found else None)
        legacy.record['missing_native_fonts_preserved']=families
        save()
    finally:legacy.close()


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
                assert result['update']['url']=='https://github.com/Darkaxt/vlc/releases/tag/redesign-v'+newer_version
                assert any(node.get('name')=='Open release page' and node['visible'] for node in result['tree']) or any(
                    widget.get('text','').replace('&','')=='Open release page' for widget in result['widgets'])
            if mode == 'unavailable':
                case.inspect('manual-check-library-ready','snapshot','--await-target','fullLibrary','--await-property','ready','--await-value','true')
                open_vlc_commands(case,'retained-vlc')
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
                assert labels and all(fork_version in text for text in labels), 'Update result does not show the fork version'
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
    for name, operation in [('settings',settings),('menus',menus),('welcome',welcome),('playback',playback),('subtitles',subtitles),('preview',preview),('icons',icons),('sidebar',sidebar),('updates',updates),('seek-policy',seek_policy)]:
        if args.case=='preview-icons' and name not in ('preview','icons','sidebar'):continue
        if args.case=='correction' and name not in ('playback','preview','icons','sidebar','menus','updates'):continue
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
        if args.case not in ('all','subtitles-mpv','playback-subtitles','integration-diagnostic','subtitle-tracks-diagnostic','preview-icons','correction',name): continue
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

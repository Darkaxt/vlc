"""Check actual composed Qt/MPV SDR pixels against a pinned software reference.

The fixture/reference are private evaluation inputs. Neither is bundled with a
release. WGC needs the input desktop, so use the existing capture-only offscreen
mode with activation disabled. Interactive/seek acceptance uses the separate
inactive-desktop workflow; this case compares the same paused first frame.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True
from isolated_desktop import input_desktop
from PIL import Image, ImageChops, ImageStat


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    parser.add_argument('--fixture', required=True, type=Path)
    parser.add_argument('--reference', required=True, type=Path)
    parser.add_argument('--negative', type=Path)
    parser.add_argument('--capture-tool', required=True, type=Path)
    args = parser.parse_args()
    source, fixture, reference, capture = (path.resolve(strict=True) for path in
        (args.runtime, args.fixture, args.reference, args.capture_tool))
    root = Path('D:/Temp/vlc-s8-20261029')
    scratch = args.scratch.resolve()
    assert scratch.parent == root and not scratch.exists()
    assert all(path.is_relative_to(root) for path in (source, fixture, reference, capture))
    reference_info = json.loads(reference.with_suffix('.json').read_text())
    assert reference_info['passed'] and not reference_info['strip_dovi']
    assert reference_info['input_sha256'] == digest(fixture)
    assert abs(reference_info['requested_time']) < 0.000001
    assert reference_info['library_sha256'] == digest(source / 'libmpv-2.dll')
    assert reference_info['image_sha256'] == digest(reference)
    if args.negative:
        negative = args.negative.resolve(strict=True)
        negative_info = json.loads(negative.with_suffix('.json').read_text())
        assert negative_info['passed'] and negative_info['strip_dovi']
        assert negative_info['image_sha256'] == digest(negative)
        for key in ('input_sha256', 'library_sha256', 'requested_time'):
            assert negative_info[key] == reference_info[key], key
        assert negative_info['properties']['time-pos'] == reference_info['properties']['time-pos']
    plugin = source / 'plugins/gui/libqt_plugin.dll'
    assert b'VLC_PLAYER_DIAGNOSTICS_DIR' in plugin.read_bytes()
    scratch.mkdir()
    runtime, evidence = scratch / 'runtime', scratch / 'evidence'
    shutil.copytree(source, runtime, ignore=lambda directory, names: ['sdk'] if Path(directory).resolve() == source else [])
    assert not any((runtime / 'portable').iterdir())
    evidence.mkdir()
    temporary = scratch / 'tmp'
    temporary.mkdir()
    token = uuid.uuid4().hex + uuid.uuid4().hex
    session = evidence / 'session.json'
    env = {key: value for key, value in os.environ.items() if not key.startswith('VLC_PLAYER_DIAGNOSTICS')}
    for key in ('VLC_PLUGIN_PATH', 'QT_SCREEN_SCALE_FACTORS', 'LC_ALL', 'LC_MESSAGES', 'LANGUAGE'):
        env.pop(key, None)
    env.update(TEMP=str(temporary), TMP=str(temporary), VLC_DATA_PATH=str(runtime),
        VLC_USERDATA_PATH=str(runtime / 'portable'), QML_DISK_CACHE_PATH=str(scratch / 'qml-cache'),
        QT_DISABLE_SHADER_DISK_CACHE='1', QSG_RHI_DISABLE_SHADER_DISK_CACHE='1',
        QT_FORCE_STDERR_LOGGING='1', QT_ENABLE_HIGHDPI_SCALING='0', QT_FONT_DPI='96', QT_SCALE_FACTOR='1',
        VLC_PLAYER_DIAGNOSTICS_DIR=str(evidence), VLC_PLAYER_DIAGNOSTICS_TOKEN=token,
        VLC_PLAYER_DIAGNOSTICS_OFFSCREEN='1',
        VLC_PLAYER_DIAGNOSTICS_BUILD=digest(plugin))
    command = [str(runtime / 'vlc.exe'), '--language=en', '--intf=qt', '--no-one-instance',
        '--qt-playback-engine=mpv', '--start-paused', '--no-media-library', '--no-plugins-cache',
        '--restore-playback-pos=0', '--no-save-recentplay', '--no-qt-privacy-ask',
        '--no-qt-updates-notif', '--no-metadata-network-access', '--no-qt-video-autoresize',
        '--no-video-title-show', '--no-volume-save', '--mmdevice-volume=0',
        '--verbose=2', '--file-logging', '--log-verbose=2', '--logfile=' + str(evidence / 'native-ui.log'), str(fixture)]
    (evidence / 'launch-argv.json').write_text(json.dumps(command, indent=2) + '\n')
    result = {'schema': 'vlc_redesign.s8_integrated_sdr_color.v1', 'passed': False,
        'fixture_sha256': digest(fixture), 'reference_sha256': digest(reference),
        'qt_plugin_sha256': digest(plugin), 'mpv_sha256': digest(runtime / 'libmpv-2.dll'),
        'scope': 'Actual WGC-composed native player pixels in capture-only offscreen mode, without activation or OS input; paused first frame, SDR conversion, not native DV display output',
        'steps': []}
    inspector = Path(__file__).with_name('inspect-player.py')

    def inspect(label, operation, *options):
        completed = subprocess.run([sys.executable, '-B', str(inspector), '--session', str(session),
            operation, *map(str, options)], capture_output=True, text=True, encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW)
        (evidence / (label + '.client.log')).write_text(completed.stdout + completed.stderr, encoding='utf-8')
        assert completed.returncode == 0, (label, completed.stdout, completed.stderr)
        response = Path(re.search(r'^Response: (.+)$', completed.stdout, re.M).group(1).strip())
        snapshot = json.loads(response.read_text(encoding='utf-8'))
        assert not snapshot.get('qml_errors'), (label, snapshot.get('qml_errors'))
        assert '"before": false, "after": false' in completed.stdout
        result['steps'].append({'name': label, 'response': response.name, 'core': snapshot.get('core')})
        return snapshot

    with (evidence / 'stdout.log').open('wb') as out, (evidence / 'stderr.log').open('wb') as err:
        desktop_before = input_desktop()
        player = subprocess.Popen(command, cwd=runtime, env=env, stdout=out, stderr=err,
            creationflags=subprocess.CREATE_NO_WINDOW)
        session.write_text(json.dumps({'pid': player.pid, 'executable': str(runtime / 'vlc.exe'), 'token': token}))
        try:
            inspect('loaded-paused', 'snapshot', '--await-core', 'state', '--await-value', 3)
            inspect('decoded-output-ready', 'snapshot', '--await-core', 'mpv_video_ready', '--await-value', 'true')
            reference_time = float(reference_info['properties']['time-pos'])
            inspect('paused-reference-clock', 'snapshot', '--await-core', 'time_seconds',
                '--await-value', reference_time, '--await-comparison', 'at_least')
            inspect('reference-size', 'resize', '--width', 1920, '--height', 1080)
            snapshot = inspect('composed-source', 'snapshot', '--capture')
            core = snapshot['core']
            assert abs(core['time_seconds'] - reference_time) < 0.005, (core, reference_time)
            assert core['engine'] == 'mpv' and core['observation'] == 'native_mpv_events'
            assert core['native_vlc']['state'] == 0, core['native_vlc']
            assert core['hwdec-current'] == 'd3d11va-copy', core
            assert core['video-out-params']['primaries'] == 'bt.709', core['video-out-params']
            assert core['video-out-params']['gamma'] == 'srgb', core['video-out-params']
            result['observed_native_core'] = core
            # Check the actual native window, not only Qt's logical position.
            user = ctypes.WinDLL('user32', use_last_error=True)
            user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
            user.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
            user.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
            user.SetThreadDpiAwarenessContext.argtypes = [wintypes.HANDLE]
            user.SetThreadDpiAwarenessContext.restype = wintypes.HANDLE
            # GetWindowRect is DPI-virtualized for the Python observer. WGC
            # reports physical DWM frame pixels. Measure both in the same native
            # coordinate space, without changing any application/OS DPI setting.
            previous_dpi = user.SetThreadDpiAwarenessContext(wintypes.HANDLE(-4))
            assert previous_dpi, ctypes.WinError(ctypes.get_last_error())
            bounds, frame, client_bounds, origin = wintypes.RECT(), wintypes.RECT(), wintypes.RECT(), wintypes.POINT()
            hwnd = int(snapshot['window']['native_id_hex'], 16)
            try:
                assert user.GetWindowRect(hwnd, ctypes.byref(bounds))
                assert user.GetClientRect(hwnd, ctypes.byref(client_bounds))
                assert user.ClientToScreen(hwnd, ctypes.byref(origin))
                dwm = ctypes.WinDLL('dwmapi', use_last_error=True)
                dwm.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
                assert dwm.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(frame), ctypes.sizeof(frame)) == 0
                x, y = user.GetSystemMetrics(76), user.GetSystemMetrics(77)
                right, bottom = x + user.GetSystemMetrics(78), y + user.GetSystemMetrics(79)
                assert bounds.right <= x or bounds.left >= right or bounds.bottom <= y or bounds.top >= bottom
            finally:
                assert user.SetThreadDpiAwarenessContext(previous_dpi)
            result['offscreen_native_bounds'] = [bounds.left, bounds.top, bounds.right, bounds.bottom]
            width, height = client_bounds.right, client_bounds.bottom
            inset_x, inset_y = origin.x - frame.left, origin.y - frame.top
            result['native_capture_geometry'] = {
                'dwm_frame': [frame.left, frame.top, frame.right, frame.bottom],
                'client_origin': [origin.x, origin.y], 'client_size': [width, height],
                'capture_client_origin': [inset_x, inset_y], 'observer_dpi_context': 'PER_MONITOR_AWARE_V2'}
            composed = evidence / 'composed.png'
            subprocess.run([str(capture), str(player.pid), snapshot['window']['native_id_hex'],
                str(runtime / 'vlc.exe'), str(composed)], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            with Image.open(composed) as image:
                image = image.convert('RGB')
                assert image.size == (frame.right - frame.left, frame.bottom - frame.top), (image.size, result['native_capture_geometry'])
                assert (width, height) == tuple(round(snapshot['window'][key] * snapshot['window']['dpr']) for key in ('width', 'height'))
                assert abs(width / height - 16 / 9) < 0.005, snapshot['window']
                assert 0 <= inset_x <= image.width - width and 0 <= inset_y <= image.height - height
                client = image.crop((inset_x, inset_y, inset_x + width, inset_y + height))
            with Image.open(reference) as expected:
                expected = expected.convert('RGB').resize(client.size, Image.Resampling.BILINEAR)
            # Exclude the designed title/control chrome and native borders.
            interior = (80, 140, client.width - 80, client.height - 160)
            actual = client.crop(interior)
            error = ImageStat.Stat(ImageChops.difference(actual, expected.crop(interior))).mean
            result['mean_absolute_rgb_error_0_255'] = error
            assert max(error) < 3., error
            if args.negative:
                negative = args.negative.resolve(strict=True)
                with Image.open(negative) as rejected:
                    rejected = rejected.convert('RGB').resize(client.size, Image.Resampling.BILINEAR).crop(interior)
                negative_error = ImageStat.Stat(ImageChops.difference(actual, rejected)).mean
                result['mapping_disabled_rgb_error_0_255'] = negative_error
                assert sum(negative_error) > 8 * max(sum(error), 1.), (error, negative_error)
            result['composed_sha256'] = digest(composed)
            result['passed'] = True
        except Exception as error:
            result['failure'] = repr(error)
            raise
        finally:
            try:
                inspect('quit', 'quit')
            finally:
                result['exit_code'] = player.wait()
                assert input_desktop() == desktop_before
                result['input_desktop_preserved'] = True
                result['passed'] &= result['exit_code'] == 0
                (scratch / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
                print(json.dumps({key: value for key, value in result.items() if key != 'steps'}), flush=True)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

"""Verify real embedded PGS pixels against a video-only negative control.

Uses native libVLC output callbacks and lifecycle completion. No Qt or desktop
capture substitutes for rendered bitmap evidence, and no elapsed deadline ends playback.
"""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading


def worker(args):
    runtime = args.runtime.resolve()
    C.windll.kernel32.SetErrorMode(0x8003)
    C.CDLL('msvcrt')._set_error_mode(2)
    directory = os.add_dll_directory(str(runtime))
    api = C.CDLL(str(runtime / 'libvlc.dll'))
    ptr = C.c_void_p

    def function(name, result, *parameters):
        call = getattr(api, name)
        call.restype, call.argtypes = result, list(parameters)
        return call

    new = function('libvlc_new', ptr, C.c_int, C.POINTER(C.c_char_p))
    media_new = function('libvlc_media_new_path', ptr, C.c_char_p)
    player_new = function('libvlc_media_player_new', ptr, ptr, ptr, ptr)
    set_media = function('libvlc_media_player_set_media', None, ptr, ptr)
    play = function('libvlc_media_player_play', C.c_int, ptr)
    release_player = function('libvlc_media_player_release', None, ptr)
    release_media = function('libvlc_media_release', None, ptr)
    release = function('libvlc_release', None, ptr)
    video_callbacks = function('libvlc_video_set_callbacks', None, ptr, ptr, ptr, ptr, ptr)
    video_format = function('libvlc_video_set_format', None, ptr, C.c_char_p, C.c_uint, C.c_uint, C.c_uint)
    repo = Path(__file__).resolve().parents[2]
    header = subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:include/vlc/libvlc_media_player.h'],
        text=True, encoding='utf-8')
    body = header.split('struct libvlc_media_player_cbs\n{', 1)[1].split('\n};', 1)[0]
    members = re.findall(r'void\s*\(\*(on_\w+)\)', body)

    class Callbacks(C.Structure):
        _fields_ = [('version', C.c_uint32)] + [(name, ptr) for name in members]

    finished = threading.Event()
    pixels_lock = threading.Lock()
    pixels = C.create_string_buffer(320 * 180 * 4)
    observed = {'opened': False, 'states': [], 'stopping_reasons': [],
        'displayed_frames': 0, 'white_bitmap_frames': 0, 'white_background_frames': 0}

    @C.CFUNCTYPE(None, ptr, C.c_int)
    def state_changed(opaque, state):
        observed['states'].append(state)
        observed['opened'] |= state in (1, 2, 3)
        if state == 6 or (state == 4 and observed['opened']):
            finished.set()

    @C.CFUNCTYPE(None, ptr, ptr, C.c_int)
    def media_stopping(opaque, media, reason):
        observed['stopping_reasons'].append(reason)

    @C.CFUNCTYPE(ptr, ptr, C.POINTER(ptr))
    def lock(opaque, planes):
        pixels_lock.acquire()
        planes[0] = C.addressof(pixels)
        return None

    @C.CFUNCTYPE(None, ptr, ptr, C.POINTER(ptr))
    def unlock(opaque, picture, planes):
        pixels_lock.release()

    @C.CFUNCTYPE(None, ptr, ptr)
    def display(opaque, picture):
        with pixels_lock:
            data = pixels.raw
        white = 0
        for y in range(80, 96):
            for x in range(100, 148):
                offset = (y * 320 + x) * 4
                white += all(channel >= 240 for channel in data[offset:offset + 3])
        observed['white_bitmap_frames'] += white >= 700
        background = (10 * 320 + 10) * 4
        observed['white_background_frames'] += all(channel >= 240 for channel in data[background:background + 3])
        observed['displayed_frames'] += 1

    callbacks = Callbacks()
    callbacks.on_state_changed = C.cast(state_changed, ptr).value
    callbacks.on_media_stopping = C.cast(media_stopping, ptr).value
    options = [b'--ignore-config', b'--no-media-library', b'--no-plugins-cache',
        b'--no-osd', b'--aout=dummy', b'--avcodec-hw=none', b'--sub-language=eng']
    instance = new(len(options), (C.c_char_p * len(options))(*options))
    assert instance
    fixture = args.fixtures / ('control.mkv' if args.case == 'control' else 'embedded-image.mkv')
    media = media_new(os.fsencode(fixture.resolve()))
    assert media
    player = player_new(instance, C.byref(callbacks), None)
    assert player
    video_callbacks(player, C.cast(lock, ptr), C.cast(unlock, ptr), C.cast(display, ptr), None)
    video_format(player, b'RV32', 320, 180, 320 * 4)
    set_media(player, media)
    try:
        assert play(player) == 0
        finished.wait()
    finally:
        release_player(player)
        release_media(media)
        release(instance)
        directory.close()
    assert observed['states'][-1] == 4 and 1 in observed['stopping_reasons'], observed
    assert observed['displayed_frames'] >= 100 and observed['white_background_frames'] == 0, observed
    if args.case == 'embedded':
        assert observed['white_bitmap_frames'] >= 20, observed
    else:
        assert observed['white_bitmap_frames'] == 0, observed
    print(json.dumps(dict(case=args.case, passed=True, observed=observed)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--case', choices=['control', 'embedded'])
    args = parser.parse_args()
    if args.worker:
        worker(args)
        return
    source, scratch = args.runtime.resolve(), args.scratch.resolve()
    assert scratch.drive.upper() == 'D:' and scratch.parent.name.startswith('vlc-s7-') and not scratch.exists()
    assert (args.fixtures / 'embedded-image.mkv').is_file()
    scratch.mkdir()
    (scratch / 'tmp').mkdir()
    runtime = scratch / 'runtime'
    shutil.copytree(source, runtime, ignore=lambda directory, names: ['sdk'] if Path(directory).resolve() == source else [])
    env = dict(os.environ, TEMP=str(scratch / 'tmp'), TMP=str(scratch / 'tmp'), VLC_DATA_PATH=str(runtime))
    env.pop('VLC_PLUGIN_PATH', None)
    records = []
    for case in ('control', 'embedded'):
        with (scratch / (case + '.stdout')).open('wb') as out, (scratch / (case + '.stderr')).open('wb') as err:
            result = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), '--worker',
                '--runtime', str(runtime), '--fixtures', str(args.fixtures.resolve()), '--scratch', str(scratch), '--case', case],
                cwd=runtime, env=env, stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
        record = {'case': case, 'exit_code': result.returncode}
        if result.returncode == 0:
            record.update(json.loads((scratch / (case + '.stdout')).read_text(encoding='utf-8')))
        records.append(record)
        print(json.dumps(record), flush=True)
    summary = {'schema': 'vlc_redesign.s7_embedded_image_pixels.v1', 'cases': records,
        'codec_plugin_sha256': hashlib.sha256((runtime / 'plugins/codec/libavcodec_plugin.dll').read_bytes()).hexdigest(),
        'libvlccore_sha256': hashlib.sha256((runtime / 'libvlccore.dll').read_bytes()).hexdigest(),
        'passed': all(record.get('passed') and record['exit_code'] == 0 for record in records),
        'scope': 'Native VLC rendered bitmap pixels with a video-only control, EOF and release. No desktop input or physical-display claim.'}
    (scratch / 'result.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2), flush=True)
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

"""Native libVLC/WASAPI startup and pause regression, with real state events.

Runs each case in an isolated child because the known upstream failure aborts.
No GUI, OS input, application deadline, synthetic clock or audio callbacks replace
the real MMDevice/WASAPI output. Audio is muted through the isolated VLC session.
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


def worker(options):
    runtime = options.runtime.resolve()
    C.windll.kernel32.SetErrorMode(0x8003)
    C.CDLL('msvcrt')._set_error_mode(2)
    dll_directory = os.add_dll_directory(str(runtime))
    api = C.CDLL(str(runtime / 'libvlc.dll'))

    def function(name, result, *arguments):
        call = getattr(api, name)
        call.restype, call.argtypes = result, list(arguments)
        return call

    pointer = C.c_void_p
    new = function('libvlc_new', pointer, C.c_int, C.POINTER(C.c_char_p))
    media_new = function('libvlc_media_new_path', pointer, C.c_char_p)
    add_option = function('libvlc_media_add_option', None, pointer, C.c_char_p)
    player_new = function('libvlc_media_player_new', pointer, pointer, pointer, pointer)
    set_media = function('libvlc_media_player_set_media', None, pointer, pointer)
    play = function('libvlc_media_player_play', C.c_int, pointer)
    pause = function('libvlc_media_player_set_pause', None, pointer, C.c_int)
    stop = function('libvlc_media_player_stop_async', C.c_int, pointer)
    release_player = function('libvlc_media_player_release', None, pointer)
    release_media = function('libvlc_media_release', None, pointer)
    release = function('libvlc_release', None, pointer)
    log_set = function('libvlc_log_set', None, pointer, pointer, pointer)

    # Derive the callback layout from this pinned source header, not an installed
    # python-vlc binding for another libVLC ABI. Every member after version is a
    # native callback pointer; retain all slots, including callbacks not observed.
    repo = Path(__file__).resolve().parents[2]
    header = subprocess.check_output(['git', '-C', str(repo), 'show',
        'HEAD:include/vlc/libvlc_media_player.h'], text=True, encoding='utf-8')
    body = header.split('struct libvlc_media_player_cbs\n{', 1)[1].split('\n};', 1)[0]
    members = re.findall(r'void\s*\(\*(on_\w+)\)', body)
    assert members[:3] == ['on_media_changed', 'on_media_stopping', 'on_state_changed']

    class Callbacks(C.Structure):
        _fields_ = [('version', C.c_uint32)] + [(name, pointer) for name in members]

    condition = threading.Condition()
    observed = {'state': 0, 'time_us': 0, 'opened': False, 'states': [], 'stopping_reasons': []}
    hardware_started = threading.Event()
    formatter = C.CDLL('msvcrt')._vsnprintf
    formatter.argtypes = [pointer, C.c_size_t, C.c_char_p, pointer]
    formatter.restype = C.c_int

    @C.CFUNCTYPE(None, pointer, C.c_int, pointer, C.c_char_p, pointer)
    def log_message(opaque, level, context, template, arguments):
        buffer = C.create_string_buffer(8192)
        formatter(buffer, len(buffer) - 1, template, arguments)
        message = buffer.value.decode('utf-8', errors='replace')
        print(message, file=sys.stderr, flush=True)
        if message == 'state changed: 1':
            hardware_started.set()

    @C.CFUNCTYPE(None, pointer, C.c_int)
    def state_changed(opaque, state):
        with condition:
            observed['state'] = state
            observed['states'].append(state)
            observed['opened'] |= state in (1, 2, 3)
            print(json.dumps({'event': 'state', 'value': state}), flush=True)
            condition.notify_all()

    @C.CFUNCTYPE(None, pointer, C.c_int64, C.c_double)
    def position_changed(opaque, time_us, position):
        with condition:
            observed['time_us'] = time_us
            condition.notify_all()

    @C.CFUNCTYPE(None, pointer, pointer, C.c_int)
    def media_stopping(opaque, media, reason):
        with condition:
            observed['stopping_reasons'].append(reason)
            condition.notify_all()

    callbacks = Callbacks()
    for name, callback in [('on_state_changed', state_changed),
                           ('on_position_changed', position_changed),
                           ('on_media_stopping', media_stopping)]:
        setattr(callbacks, name, C.cast(callback, pointer).value)

    def ended():
        return observed['state'] == 6 or (observed['opened'] and observed['state'] == 4)

    def await_observation(predicate):
        with condition:
            condition.wait_for(lambda: predicate() or ended())
            if not predicate():
                raise RuntimeError('Playback ended before required observation: ' + json.dumps(observed))

    arguments = [b'--ignore-config', b'--no-media-library', b'--no-plugins-cache',
        b'--no-osd', b'--aout=mmdevice', b'--mmdevice-backend=wasapi',
        b'--no-volume-save', b'--mmdevice-volume=0', b'--vout=dummy', b'-vv']
    instance = new(len(arguments), (C.c_char_p * len(arguments))(*arguments))
    assert instance, 'libvlc_new failed'
    if options.resume_on_hardware_start:
        log_set(instance, C.cast(log_message, pointer), None)
    media = media_new(os.fsencode(options.fixture.resolve()))
    assert media, 'media creation failed'
    if options.case == 'startup-paused':
        add_option(media, b':start-paused')
    player = player_new(instance, C.byref(callbacks), None)
    assert player, 'player creation failed'
    set_media(player, media)
    try:
        assert play(player) == 0
        if options.case == 'startup-paused':
            await_observation(lambda: observed['state'] == 3)
            if options.resume_on_hardware_start:
                print('Waiting for the actual WASAPI session-start callback while input is paused', flush=True)
                hardware_started.wait()
            print('Resuming startup-paused input', flush=True)
            pause(player, 0)
        await_observation(lambda: observed['state'] == 2 and observed['time_us'] >= 1_000_000)
        for threshold in (2_000_000, 3_000_000):
            pause(player, 1)
            await_observation(lambda: observed['state'] == 3)
            pause(player, 0)
            await_observation(lambda: observed['state'] == 2 and observed['time_us'] >= threshold)
        with condition:
            condition.wait_for(ended)
        assert observed['state'] == 4 and observed['time_us'] >= 3_000_000, observed
        print(json.dumps({'passed': True, 'case': options.case, 'observed': observed}), flush=True)
    finally:
        if not ended():
            stop(player)
            with condition:
                condition.wait_for(ended)
        release_player(player)
        release_media(media)
        release(instance)
        dll_directory.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    parser.add_argument('--fixture', type=Path)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--case', choices=['normal', 'startup-paused'])
    parser.add_argument('--resume-on-hardware-start', action='store_true',
        help='Diagnostic: resume only after the real initial deferred WASAPI start event')
    options = parser.parse_args()
    if options.worker:
        worker(options)
        return
    scratch = options.scratch.resolve()
    if scratch.drive.upper() not in ('D:', 'E:') or 'Temp' not in scratch.parts:
        parser.error('Use exact registered task-owned D:/E:/Temp scratch')
    scratch.mkdir(parents=True, exist_ok=True)
    runtime = scratch / 'runtime-audio'
    if not runtime.exists():
        shutil.copytree(options.runtime, runtime)
    profile = scratch / 'profile-audio'
    temporary = scratch / 'tmp'
    profile.mkdir(exist_ok=True)
    temporary.mkdir(exist_ok=True)
    fixture = options.fixture or scratch / 'audio-fixture.wav'
    if not fixture.exists():
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi',
            '-i', 'sine=frequency=440:sample_rate=48000', '-t', '8', '-c:a', 'pcm_s16le',
            str(fixture)], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
    environment = dict(os.environ, TEMP=str(temporary), TMP=str(temporary),
        VLC_USERDATA_PATH=str(profile), VLC_DATA_PATH=str(runtime))
    environment.pop('VLC_PLUGIN_PATH', None)
    results = []
    for case in ([options.case] if options.case else ['normal', 'startup-paused']):
        label = case + ('-deferred' if options.resume_on_hardware_start else '')
        with (scratch / f'{label}.stdout').open('wb') as stdout, (scratch / f'{label}.stderr').open('wb') as stderr:
            process = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()),
                '--worker', '--case', case, '--runtime', str(runtime), '--scratch', str(scratch),
                '--fixture', str(fixture), *(['--resume-on-hardware-start'] if options.resume_on_hardware_start else [])], cwd=runtime, env=environment,
                stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
        output = (scratch / f'{label}.stdout').read_text(encoding='utf-8', errors='replace')
        log = (scratch / f'{label}.stderr').read_text(encoding='utf-8', errors='replace')
        result = {'case': case, 'exit_code': process.returncode, 'passed': process.returncode == 0 and '"passed": true' in output,
            'wasapi_selected': 'using aout stream module "wasapi"' in log,
            'errors': [line for line in log.splitlines() if any(term in line for term in ['Assertion', 'assertion', 'stream failed to start', 'cannot resume'])]}
        results.append(result)
        print(json.dumps(result), flush=True)
    record = {'runtime': str(options.runtime.resolve()), 'tested_copy': str(runtime),
        'wasapi_sha256': hashlib.sha256((runtime / 'plugins/audio_output/libwasapi_plugin.dll').read_bytes()).hexdigest(),
        'cases': results, 'passed': all(item['passed'] and item['wasapi_selected'] for item in results),
        'scope': 'Real native audio output, no GUI or OS input; session muted; no physical-listening claim.'}
    record_name = 'deferred-result.json' if options.resume_on_hardware_start else 'result.json'
    (scratch / record_name).write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(0 if record['passed'] else 1)


if __name__ == '__main__':
    main()

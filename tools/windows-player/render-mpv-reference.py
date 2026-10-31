"""Produce a native D3D11 SDR color reference from the pinned Windows MPV.

This is the independent renderer side of S8's integrated pixel comparison, not
Qt feature acceptance. The render thread owns the device, context and textures;
the calling thread owns MPV commands/events. Actual events and GPU Map completion
drive capture and teardown. No window, installed settings or playback audio.
"""
import argparse
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import threading
from PIL import Image


class Param(c.Structure):
    _fields_ = [('type', c.c_int), ('data', c.c_void_p)]


class Event(c.Structure):
    _fields_ = [('type', c.c_int), ('error', c.c_int), ('request', c.c_uint64), ('data', c.c_void_p)]


class Log(c.Structure):
    _fields_ = [('prefix', c.c_char_p), ('level', c.c_char_p), ('text', c.c_char_p), ('number', c.c_int)]


class TextureDesc(c.Structure):
    _fields_ = [(name, w.UINT) for name in ('width', 'height', 'mips', 'arrays', 'format',
                  'samples', 'quality', 'usage', 'bind', 'cpu', 'misc')]


class Mapped(c.Structure):
    _fields_ = [('data', c.c_void_p), ('row_pitch', w.UINT), ('depth_pitch', w.UINT)]


def method(pointer, index, result, *args):
    table = c.cast(pointer, c.POINTER(c.POINTER(c.c_void_p))).contents
    return c.WINFUNCTYPE(result, c.c_void_p, *args)(table[index])


def release(pointer):
    if pointer:
        method(pointer, 2, w.ULONG)(pointer)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--expect-sha256', default='04e4d27dc385dc18ddd93fbe69c75e635b864f3c6ec53a9122df54c2f7842f4a')
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New PNG under this task scratch')
    parser.add_argument('--time', type=float, default=15.)
    parser.add_argument('--hwdec', default='no', choices=('no', 'auto-safe', 'd3d11va-copy'))
    parser.add_argument('--strip-dovi', action='store_true', help='Negative control: disable libplacebo Dolby Vision metadata mapping')
    parser.add_argument('--vf', help='Explicit filter under investigation; recorded in the reference result')
    parser.add_argument('--demuxer', help='Explicit demuxer for a bounded media-entry diagnostic')
    args = parser.parse_args()
    root = Path('D:/Temp/vlc-s8-20261029')
    library, source, output = args.library.resolve(strict=True), args.input.resolve(strict=True), args.output.resolve()
    assert os.name == 'nt' and c.sizeof(c.c_void_p) == 8
    assert source.is_relative_to(root) and output.is_relative_to(root) and output.suffix == '.png'
    assert not output.exists() and not output.with_suffix('.json').exists()
    output.parent.mkdir(parents=True, exist_ok=True)
    with library.open('rb') as stream:
        library_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert library_hash == args.expect_sha256
    with source.open('rb') as stream:
        input_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    result = {'schema': 'vlc_redesign.mpv_color_reference.v1', 'passed': False,
              'scope': 'Independent renderer reference; integrated Qt acceptance remains required',
              'input': str(source), 'input_sha256': input_hash, 'library_sha256': library_hash,
              'requested_time': args.time, 'strip_dovi': args.strip_dovi, 'logs': []}
    result['vf'] = args.vf
    mpv = c.CDLL(str(library), winmode=0x100 | 0x1000)

    def bind(name, restype, *arguments):
        function = getattr(mpv, 'mpv_' + name)
        function.restype, function.argtypes = restype, list(arguments)
        return function

    create = bind('create', c.c_void_p)
    option = bind('set_option_string', c.c_int, c.c_void_p, c.c_char_p, c.c_char_p)
    initialize = bind('initialize', c.c_int, c.c_void_p)
    command = bind('command_async', c.c_int, c.c_void_p, c.c_uint64, c.POINTER(c.c_char_p))
    get_string = bind('get_property_string', c.c_void_p, c.c_void_p, c.c_char_p)
    free = bind('free', None, c.c_void_p)
    request_log = bind('request_log_messages', c.c_int, c.c_void_p, c.c_char_p)
    wait = bind('wait_event', c.POINTER(Event), c.c_void_p, c.c_double)
    wake_player = bind('wakeup', None, c.c_void_p)
    destroy = bind('terminate_destroy', None, c.c_void_p)
    render_create = bind('render_context_create', c.c_int, c.POINTER(c.c_void_p), c.c_void_p, c.POINTER(Param))
    render_free = bind('render_context_free', None, c.c_void_p)
    update = bind('render_context_update', c.c_uint64, c.c_void_p)
    render = bind('render_context_render', c.c_int, c.c_void_p, c.POINTER(Param))
    report_swap = bind('render_context_report_swap', None, c.c_void_p)
    callback_type = c.CFUNCTYPE(None, c.c_void_p)
    set_callback = bind('render_context_set_update_callback', None, c.c_void_p, c.c_void_p, c.c_void_p)
    player = create()
    assert player
    ready, wake, capture, captured, stop = [threading.Event() for _ in range(5)]
    render_errors = []
    worker = None

    def draw_thread():
        device, context, texture, staging, handle = [c.c_void_p() for _ in range(5)]
        callback = callback_type(lambda _: wake.set())
        try:
            d3d = c.WinDLL('d3d11.dll')
            new_device = d3d.D3D11CreateDevice
            new_device.restype = c.c_long
            new_device.argtypes = [c.c_void_p, c.c_int, c.c_void_p, w.UINT, c.POINTER(c.c_int),
                                  w.UINT, w.UINT, c.POINTER(c.c_void_p), c.POINTER(c.c_int), c.POINTER(c.c_void_p)]
            level = c.c_int()
            code = new_device(None, 1, None, 0x20, None, 0, 7, c.byref(device), c.byref(level), c.byref(context))
            assert code >= 0, ('D3D11CreateDevice', hex(code & 0xffffffff))
            result['feature_level'] = hex(level.value)
            descriptor = TextureDesc(960, 540, 1, 1, 87, 1, 0, 0, 0x28, 0, 0)
            new_texture = method(device, 5, c.c_long, c.POINTER(TextureDesc), c.c_void_p, c.POINTER(c.c_void_p))
            assert new_texture(device, c.byref(descriptor), None, c.byref(texture)) >= 0
            descriptor.usage, descriptor.bind, descriptor.cpu = 3, 0, 0x20000
            assert new_texture(device, c.byref(descriptor), None, c.byref(staging)) >= 0
            advanced = c.c_int(1)
            api = c.create_string_buffer(b'd3d11')
            params = (Param * 4)(Param(1, c.cast(api, c.c_void_p)), Param(21, c.cast(c.pointer(device), c.c_void_p)),
                                  Param(10, c.cast(c.pointer(advanced), c.c_void_p)), Param(0, None))
            assert render_create(c.byref(handle), player, params) >= 0
            set_callback(handle, c.cast(callback, c.c_void_p), None)
            ready.set()
            while True:
                wake.wait()
                wake.clear()
                if stop.is_set():
                    break
                flags = update(handle)
                requested = capture.is_set()
                if not (flags & 1) and not requested:
                    continue
                frame = (Param * 2)(Param(22, c.cast(c.pointer(texture), c.c_void_p)), Param(0, None))
                assert render(handle, frame) >= 0
                report_swap(handle)
                if requested:
                    method(context, 47, None, c.c_void_p, c.c_void_p)(context, staging, texture)
                    mapped = Mapped()
                    code = method(context, 14, c.c_long, c.c_void_p, w.UINT, c.c_int, w.UINT, c.POINTER(Mapped))(
                        context, staging, 0, 1, 0, c.byref(mapped))
                    assert code >= 0, ('Map', hex(code & 0xffffffff))
                    try:
                        pixels = b''.join(c.string_at(mapped.data + row * mapped.row_pitch, 960 * 4) for row in range(540))
                    finally:
                        method(context, 15, None, c.c_void_p, w.UINT)(context, staging, 0)
                    Image.frombytes('RGBA', (960, 540), pixels, 'raw', 'BGRA').convert('RGB').save(output)
                    result['image_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
                    result['pixels'] = [960, 540]
                    captured.set()
                    capture.clear()
        except BaseException as error:
            render_errors.append(repr(error))
            ready.set(); captured.set()
            wake_player(player)
        finally:
            if handle:
                set_callback(handle, None, None)
                render_free(handle)
                result['render_freed_before_player'] = True
            for pointer in (staging, texture, context, device):
                release(pointer)

    def property_string(name):
        pointer = get_string(player, name.encode())
        if not pointer:
            return None
        try:
            return c.string_at(pointer).decode('utf-8', errors='replace')
        finally:
            free(pointer)

    try:
        options = {'config': 'no', 'vo': 'libmpv', 'ao': 'null', 'terminal': 'no',
                   'input-default-bindings': 'no', 'pause': 'yes',
                   'hwdec': args.hwdec, 'vd-lavc-threads': '1', 'target-prim': 'bt.709', 'target-trc': 'srgb', 'target-peak': '100',
                   'vf': 'lavfi=[libplacebo=apply_dolbyvision=1:colorspace=bt709:color_primaries=bt709:color_trc=iec61966-2-1:range=pc:format=rgba]',
                   'gpu-shader-cache': 'no'}
        if args.strip_dovi:
            options['vf'] = options['vf'].replace('apply_dolbyvision=1', 'apply_dolbyvision=0')
        if args.vf:
            assert not args.strip_dovi
            options['vf'] = args.vf
        if args.demuxer:
            options['demuxer'] = args.demuxer
        result['effective_options'] = options
        for name, value in options.items():
            code = option(player, name.encode(), value.encode())
            assert code >= 0, (name, code)
        assert request_log(player, b'v') >= 0
        assert initialize(player) >= 0
        worker = threading.Thread(target=draw_thread, name='S8-D3D11-reference')
        worker.start(); ready.wait()
        assert not render_errors, render_errors
        arguments = (c.c_char_p * 4)(b'loadfile', str(source).encode('utf-8'), b'replace', None)
        assert command(player, 1, arguments) >= 0
        phase = 'load'
        seek_started = False
        while True:
            event = wait(player, -1).contents
            assert not render_errors, render_errors
            if event.error < 0:
                raise RuntimeError(('MPV event error', event.type, event.error))
            if event.type == 2:
                message = c.cast(event.data, c.POINTER(Log)).contents
                result['logs'].append({key: (getattr(message, key) or b'').decode('utf-8', errors='replace').strip()
                                       for key in ('prefix', 'level', 'text')})
            elif event.type in (1, 7):
                raise RuntimeError(('Playback ended before reference capture', event.type, event.error))
            elif event.type == 20 and phase == 'seek':
                seek_started = True
            elif event.type == 21:
                if phase == 'load' and args.time > 0:
                    arguments = (c.c_char_p * 5)(b'seek', str(args.time).encode(), b'absolute+exact', None, None)
                    assert command(player, 2, arguments) >= 0
                    phase = 'seek'
                elif phase == 'load' or seek_started:
                    break
        result['properties'] = {key: property_string(key) for key in ('mpv-version', 'ffmpeg-version', 'libplacebo-version',
            'video-params', 'video-dec-params', 'video-out-params', 'video-params/colormatrix', 'video-params/gamma', 'video-params/primaries',
            'video-params/dolbyvision', 'video-pts', 'time-pos', 'hwdec-current')}
        assert result['properties']['video-params'] and result['properties']['video-out-params'], \
            ('Reference has no decoded video', result['logs'])
        assert not any(item['level'] in ('fatal', 'error') for item in result['logs']), result['logs']
        capture.set(); wake.set(); captured.wait()
        assert not render_errors, render_errors
        assert output.is_file()
        result['passed'] = True
    finally:
        stop.set(); wake.set()
        if worker:
            worker.join()
        destroy(player)
        result['player_destroyed'] = True
        result['render_errors'] = render_errors
        output.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'captured': result['passed'], 'output': str(output), 'sha256': result.get('image_sha256'),
                      'time': result.get('properties', {}).get('time-pos'), 'hwdec': result.get('properties', {}).get('hwdec-current'),
                      'render_errors': render_errors, 'player_destroyed': result['player_destroyed']}))


if __name__ == '__main__':
    main()

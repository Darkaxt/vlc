"""Diagnostic: verify an exact Windows libmpv and its native D3D11 render API.

Creates no windows and opens no media. Successful initialization is a capability
probe, not playback, Dolby Vision, output-color or integrated-feature acceptance.
"""
import argparse
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
import re
from pathlib import Path
import sys


class Param(c.Structure):
    _fields_ = [('type', c.c_int), ('data', c.c_void_p)]


class InitD3D(c.Structure):
    _fields_ = [('device', c.c_void_p)]


class Event(c.Structure):
    _fields_ = [('event_id', c.c_int), ('error', c.c_int),
                ('reply_userdata', c.c_uint64), ('data', c.c_void_p)]


class Log(c.Structure):
    _fields_ = [('prefix', c.c_char_p), ('level', c.c_char_p),
                ('text', c.c_char_p), ('log_level', c.c_int)]


def release(pointer):
    if pointer:
        table = c.cast(pointer, c.POINTER(c.POINTER(c.c_void_p))).contents
        c.WINFUNCTYPE(w.ULONG, c.c_void_p)(table[2])(pointer)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--expect-sha256', default='04e4d27dc385dc18ddd93fbe69c75e635b864f3c6ec53a9122df54c2f7842f4a')
    parser.add_argument('--controller-options', action='store_true', help='Probe controller literals and the selected configuration scenario below')
    parser.add_argument('--volume-save', choices=('yes', 'no'), default='yes')
    parser.add_argument('--qt-max-volume', type=int, default=125)
    parser.add_argument('--audio-device', default='', help='Native endpoint ID; empty uses the controller default console device')
    args = parser.parse_args()
    assert os.name == 'nt' and c.sizeof(c.c_void_p) == 8
    library = args.library.resolve(strict=True)
    output = args.output.resolve()
    assert output.is_relative_to(Path('D:/Temp/vlc-s8-20261029'))
    assert not output.exists(), 'Preserve an existing diagnostic result'
    output.parent.mkdir(parents=True, exist_ok=True)
    with library.open('rb') as stream:
        actual_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert actual_hash == args.expect_sha256
    result = {'schema': 'vlc_redesign.mpv_runtime_probe.v1', 'library_sha256': actual_hash,
        'scope': 'Exact native DLL and D3D11 render initialization only; no playback or DV acceptance',
        'passed': False, 'logs': []}
    device, context = c.c_void_p(), c.c_void_p()
    player, render = None, c.c_void_p()
    d3d = c.WinDLL('d3d11.dll')
    create = d3d.D3D11CreateDevice
    create.restype = c.c_long
    create.argtypes = [c.c_void_p, c.c_int, c.c_void_p, w.UINT,
        c.POINTER(c.c_int), w.UINT, w.UINT, c.POINTER(c.c_void_p),
        c.POINTER(c.c_int), c.POINTER(c.c_void_p)]
    level = c.c_int()
    with os.add_dll_directory(str(library.parent)):
        # The dependent DLL search is restricted to this DLL's directory and
        # Windows system directories; do not select another installed player.
        mpv = c.CDLL(str(library), winmode=0x100 | 0x1000)
        def bind(name, restype, arguments):
            fun = getattr(mpv, name)
            fun.restype, fun.argtypes = restype, arguments
            return fun
        new = bind('mpv_create', c.c_void_p, [])
        option = bind('mpv_set_option_string', c.c_int, [c.c_void_p, c.c_char_p, c.c_char_p])
        initialize = bind('mpv_initialize', c.c_int, [c.c_void_p])
        request_log = bind('mpv_request_log_messages', c.c_int, [c.c_void_p, c.c_char_p])
        wait_event = bind('mpv_wait_event', c.POINTER(Event), [c.c_void_p, c.c_double])
        get_string = bind('mpv_get_property_string', c.c_void_p, [c.c_void_p, c.c_char_p])
        free = bind('mpv_free', None, [c.c_void_p])
        version = bind('mpv_client_api_version', c.c_ulong, [])
        render_create = bind('mpv_render_context_create', c.c_int,
            [c.POINTER(c.c_void_p), c.c_void_p, c.POINTER(Param)])
        render_free = bind('mpv_render_context_free', None, [c.c_void_p])
        destroy = bind('mpv_terminate_destroy', None, [c.c_void_p])
        try:
            result['client_api_version'] = int(version())
            player = new()
            assert player, 'mpv_create returned NULL'
            options = {'config': 'no', 'vo': 'libmpv', 'ao': 'null',
                    'terminal': 'no', 'input-default-bindings': 'no',
                    'gpu-shader-cache': 'no'}
            if args.controller_options:
                controller = Path(__file__).resolve().parents[2] / 'modules/gui/qt/player/mpv_playback.cpp'
                text = controller.read_text(encoding='utf-8')
                array = text.split('const std::pair<const char *, const char *> options[] = ', 1)[1].split('int code = 0;', 1)[0]
                options = dict(re.findall(r'\{"([^"]+)", "([^"]*)"\}', array))
                assert {'config', 'vo', 'ao', 'audio-exclusive', 'wasapi-device-role',
                        'hwdec', 'vf', 'target-prim', 'target-trc', 'target-peak'} <= options.keys(), \
                        'Initialization array extraction failed'
                maximum = max(1., args.qt_max_volume / 100.)
                options['volume-max'] = str(100. * maximum ** 3)
                session = re.search(r'const char \*session = var_InheritBool\(intf, "volume-save"\)\s*'
                                    r'\? "([^"]+)" : "";', text)
                assert session, 'Persisted native session extraction failed'
                options['wasapi-session-id'] = session.group(1) if args.volume_save == 'yes' else ''
                if args.audio_device:
                    options['audio-device'] = 'wasapi/' + args.audio_device
                result['configuration_scenario'] = {'volume_save': args.volume_save,
                    'qt_max_volume': args.qt_max_volume, 'audio_device': args.audio_device,
                    'scope': 'Chosen initialization inputs; no native session level or persistence test'}
                result['controller_sha256'] = hashlib.sha256(controller.read_bytes()).hexdigest()
            result['options'] = options
            result['option_results'] = {}
            for key, value in options.items():
                code = option(player, key.encode(), value.encode())
                result['option_results'][key] = code
                assert code >= 0, (key, code)
            assert request_log(player, b'v') >= 0
            code = initialize(player)
            result['initialize_code'] = code
            assert code >= 0, code
            for key in ('mpv-version', 'ffmpeg-version', 'libplacebo-version'):
                pointer = get_string(player, key.encode())
                result[key] = c.string_at(pointer).decode('utf-8', errors='replace') if pointer else None
                if pointer:
                    free(pointer)
            hr = create(None, 1, None, 0x20, None, 0, 7, c.byref(device), c.byref(level), c.byref(context))
            result['d3d11_hardware_create_hresult'] = f'0x{hr & 0xffffffff:08x}'
            assert hr >= 0, hr
            result['d3d_feature_level'] = hex(level.value)
            init = InitD3D(device.value)
            api = c.create_string_buffer(b'd3d11')
            params = (Param * 3)(Param(1, c.cast(api, c.c_void_p)),
                Param(21, c.cast(c.pointer(init), c.c_void_p)), Param(0, None))
            code = render_create(c.byref(render), player, params)
            result['d3d11_render_context_create_code'] = code
            assert code >= 0 and render.value, code
            result['passed'] = True
        finally:
            if render.value:
                render_free(render)
                result['render_context_freed_before_player'] = True
            if player:
                while True:
                    event = wait_event(player, 0).contents
                    if event.event_id == 0:
                        break
                    if event.event_id == 2:
                        message = c.cast(event.data, c.POINTER(Log)).contents
                        result['logs'].append({key: (getattr(message, key) or b'').decode('utf-8', errors='replace').strip()
                            for key in ('prefix', 'level', 'text')})
                destroy(player)
                result['player_destroyed'] = True
            release(context)
            release(device)
            result['d3d_context_and_device_released'] = True
            output.write_bytes((json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps({key: value for key, value in result.items() if key != 'logs'}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())

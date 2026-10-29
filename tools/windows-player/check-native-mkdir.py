"""Check native recursive Windows directory creation with both separator styles."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--scratch', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root, runtime = args.scratch.resolve(), args.runtime.resolve()
assert os.name == 'nt' and root.parent.parent == Path('D:/Temp') and root.parent.name.startswith('vlc-s7-')
assert not root.exists() and not args.output.exists()
root.mkdir()
records = []
with os.add_dll_directory(str(runtime)):
    core = ctypes.CDLL(str(runtime / 'libvlccore.dll'))
    core.vlc_mkdir_parent.argtypes = [ctypes.c_char_p, ctypes.c_ushort]
    core.vlc_mkdir_parent.restype = ctypes.c_int
    core.vlc_mkdir.argtypes = [ctypes.c_char_p, ctypes.c_ushort]
    core.vlc_mkdir.restype = ctypes.c_int
    crt = ctypes.CDLL('msvcrt.dll')
    crt._errno.restype = ctypes.POINTER(ctypes.c_int)
    assert Path(root.drive + '\\').is_dir()
    crt._errno()[0] = 0
    root_result = core.vlc_mkdir(root.drive.encode(), 0o775)
    root_probe = {'existing_drive': root.drive, 'mkdir_drive_colon_result': root_result,
        'errno': crt._errno()[0], 'purpose': 'Diagnose why attempting to create the drive prefix interrupts recursion.'}
    for style in ('native', 'mixed'):
        path = root / style / 'parent' / 'leaf Ω'
        native = str(path)
        supplied = native if style == 'native' else str(root) + '/mixed/parent/leaf Ω'
        crt._errno()[0] = 0
        result = core.vlc_mkdir_parent(supplied.encode('utf-8'), 0o775)
        records.append({'style': style, 'return_code': result, 'errno': crt._errno()[0],
            'directory_exists': path.is_dir()})
report = {'schema': 'vlc_redesign.native_recursive_mkdir.v1', 'cases': records,
    'drive_root_probe': root_probe,
    'core_sha256': hashlib.sha256((runtime / 'libvlccore.dll').read_bytes()).hexdigest(),
    'passed': all(item['return_code'] == 0 and item['directory_exists'] for item in records)}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
raise SystemExit(0 if report['passed'] else 1)

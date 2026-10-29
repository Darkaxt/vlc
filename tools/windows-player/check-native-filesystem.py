"""Check actual Windows core missing-file errno without changing any files."""
import argparse
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--missing', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
assert os.name == 'nt' and not args.missing.exists()
runtime = args.runtime.resolve()
with os.add_dll_directory(str(runtime)):
    assert b'msvcrt.dll' in (runtime / 'libvlccore.dll').read_bytes().lower()
    core = ctypes.CDLL(str(runtime / 'libvlccore.dll'))
    # Python uses UCRT; this pinned MinGW target uses msvcrt. Observe the
    # target's actual errno rather than ctypes' Python-runtime errno copy.
    crt = ctypes.CDLL('msvcrt.dll')
    crt._errno.restype = ctypes.POINTER(ctypes.c_int)
    core.vlc_fopen.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    core.vlc_fopen.restype = ctypes.c_void_p
    crt._errno()[0] = 0
    result = core.vlc_fopen(str(args.missing).encode('utf-8'), b'rb')
    observed = crt._errno()[0]
report = {'schema': 'vlc_redesign.native_filesystem_errno.v1',
    'core_sha256': hashlib.sha256((runtime / 'libvlccore.dll').read_bytes()).hexdigest(),
    'missing_file_returned_null': result is None, 'errno': observed,
    'observed_crt': 'msvcrt.dll, the actual pinned MinGW target CRT',
    'passed': result is None and observed == errno.ENOENT}
args.output.parent.mkdir(parents=True, exist_ok=True)
assert not args.output.exists()
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
raise SystemExit(0 if report['passed'] else 1)

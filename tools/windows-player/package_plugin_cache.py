"""Bind the native module index to the portable ZIP's exact plugin cohort."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import time
import zipfile

# A single UTC instant, also represented in ZIP's NTFS and extended-time fields.
# DLL mtimes must match the values read by the native generator after extraction.
PACKAGE_EPOCH = 1793232000  # 2026-10-29 00:00:00 UTC


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def archive_info(name):
    info = zipfile.ZipInfo(name, date_time=time.localtime(PACKAGE_EPOCH)[:6])
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    filetime = (PACKAGE_EPOCH + 11644473600) * 10000000
    ntfs = struct.pack('<IHHQQQ', 0, 1, 24, filetime, filetime, filetime)
    info.extra = struct.pack('<HHBI', 0x5455, 5, 1, PACKAGE_EPOCH)
    info.extra += struct.pack('<HH', 0x000a, len(ntfs)) + ntfs
    return info


def generate(package):
    package = Path(package).resolve()
    cache = package / 'plugins/plugins.dat'
    assert not cache.exists(), 'Generate from the fresh stripped package, never copy a prior index'
    plugins = sorted((package / 'plugins').rglob('*.dll'))
    assert plugins
    records = []
    for plugin in plugins:
        assert plugin.is_file() and not plugin.is_symlink()
        os.utime(plugin, (PACKAGE_EPOCH, PACKAGE_EPOCH))
        records.append({'file': plugin.relative_to(package).as_posix(),
            'mtime': int(plugin.stat().st_mtime), 'bytes': plugin.stat().st_size,
            'sha256': digest(plugin)})
    # cachegen uses libvlc's ignore-config default, not the Windows GUI launcher.
    env = dict(os.environ, TEMP=str(package), TMP=str(package))
    env.pop('VLC_PLUGIN_PATH', None)
    process = subprocess.run([str(package / 'vlc-cache-gen.exe'), str(package / 'plugins')],
        cwd=package, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW)
    assert process.returncode == 0, process.stderr.decode('utf-8', errors='replace')
    data = cache.read_bytes()
    assert len(data) > 100
    for encoding in ('utf-8', 'utf-16le'):
        assert str(package).encode(encoding) not in data, 'Module index must use relative paths'
    record = {'schema': 'vlc_redesign.packaged_plugin_cache.v1',
        'generator_sha256': digest(package / 'vlc-cache-gen.exe'),
        'cache_sha256': hashlib.sha256(data).hexdigest(), 'plugin_count': len(records),
        'plugin_mtime_utc': PACKAGE_EPOCH, 'plugins': records,
        'zip_time_fields': 'DOS local time, extended UTC time and NTFS UTC FILETIME',
        'validation': 'Native relative-path, size, mtime and format checks remain enabled; changed or timestamp-reset files are rescanned.'}
    (package / 'VLC-PLUGIN-CACHE.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return record

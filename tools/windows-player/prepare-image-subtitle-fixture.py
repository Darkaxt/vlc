"""Make a tiny CC0 PGS bitmap fixture and an otherwise identical control.

Segment layout follows the pinned FFmpeg 9.0 pgssubdec.c parser. The white
48x16 rectangle at (100,80) is an image subtitle, not a video-overlay filter.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = args.output.resolve()
assert root.drive.upper() == 'D:' and root.parent.name.startswith('vlc-s7-') and not root.exists()
root.mkdir()
(root / 'tmp').mkdir()
env = dict(os.environ, TEMP=str(root / 'tmp'), TMP=str(root / 'tmp'))


def segment(time, kind, payload):
    return b'PG' + struct.pack('>IIBH', time * 90000, 0, kind, len(payload)) + payload


def presentation(number, state, count):
    return struct.pack('>HHBHBBBB', 320, 180, 0x10, number, state, 0, 0, count)


width, height, x, y = 48, 16, 100, 80
rle = (bytes([1]) * width + b'\0\0') * height
object_data = struct.pack('>HBB', 0, 0, 0xC0) + (len(rle) + 4).to_bytes(3, 'big') + struct.pack('>HH', width, height) + rle
blob = b''.join([
    segment(1, 0x16, presentation(0, 0x80, 1) + struct.pack('>HBBHH', 0, 0, 0, x, y)),
    segment(1, 0x17, struct.pack('>BBHHHH', 1, 0, x, y, width, height)),
    segment(1, 0x14, bytes([0, 0, 1, 235, 128, 128, 255])),
    segment(1, 0x15, object_data), segment(1, 0x80, b''),
    segment(8, 0x16, presentation(1, 0, 0)), segment(8, 0x80, b'')])
(root / 'bitmap.sup').write_bytes(blob)
commands = [
    ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=0x204080:size=320x180:rate=12',
        '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '12',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-threads', '1',
        '-c:a', 'aac', '-b:a', '64k', str(root / 'control.mkv')],
    ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(root / 'control.mkv'), '-i', str(root / 'bitmap.sup'),
        '-map', '0:v', '-map', '0:a', '-map', '1:s', '-c', 'copy', '-metadata:s:s:0', 'language=eng',
        '-disposition:s:0', 'default', str(root / 'embedded-image.mkv')]]
for index, command in enumerate(commands):
    with (root / ('ffmpeg-' + str(index) + '.log')).open('wb') as log:
        subprocess.run(command, env=env, stdout=log, stderr=log, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
probe = subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(root / 'embedded-image.mkv')],
    env=env, creationflags=subprocess.CREATE_NO_WINDOW)
metadata = json.loads(probe)
assert any(stream['codec_name'] == 'hdmv_pgs_subtitle' for stream in metadata['streams']), metadata
(root / 'streams.json').write_bytes(probe)
record = {'source': 'Locally authored PGS display segments and FFmpeg synthetic blue video/sine audio.',
    'license': 'CC0-1.0 for these generated fixtures', 'user_media_read': False,
    'bitmap': {'x': x, 'y': y, 'width': width, 'height': height, 'color': 'white', 'from_seconds': 1, 'to_seconds': 8},
    'files': [{'file': path.name, 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(root.iterdir()) if path.is_file() and path.suffix in ('.sup', '.mkv')]}
(root / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, indent=2), flush=True)

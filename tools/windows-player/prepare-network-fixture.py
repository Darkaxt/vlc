"""Remux the already-generated S7 video for a nonseekable HTTP test."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
assert args.input.is_file() and args.output.drive.upper() == 'D:'
assert args.output.parent.name.startswith('vlc-s7-') and not args.output.exists()
args.output.mkdir()
(args.output / 'tmp').mkdir()
environment = dict(os.environ, TEMP=str(args.output / 'tmp'), TMP=str(args.output / 'tmp'))
command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(args.input),
    '-map', '0:v', '-map', '0:a:0', '-c', 'copy', '-f', 'mpegts', str(args.output / 'stream-long.ts')]
with (args.output / 'ffmpeg.log').open('wb') as log:
    subprocess.run(command, env=environment, stdout=log, stderr=log, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
with (args.output / 'stream-long.ts').open('rb') as source:
    digest = hashlib.file_digest(source, 'sha256').hexdigest()
result = {'source': str(args.input), 'source_sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
    'file': 'stream-long.ts', 'sha256': digest, 'bytes': (args.output / 'stream-long.ts').stat().st_size,
    'operation': 'Lossless remux of existing synthetic S7 fixture; no user media.', 'exit_code': 0}
(args.output / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result), flush=True)

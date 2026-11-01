"""Generate M2's synthetic native acceptance inputs and public release metadata."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, required=True)
args = parser.parse_args()
root = args.root.resolve()
assert root == Path('D:/Temp/vlc-s8-first-run-1.1.2-20261101')
root.mkdir(exist_ok=True)
fixtures = root / 'fixtures'
assert not fixtures.exists(), 'Preserve the original generation identity'
repo = Path(__file__).resolve().parents[2]
subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('prepare-image-subtitle-fixture.py')),
    '--output', str(fixtures)], check=True)
env = dict(os.environ, TEMP=str(fixtures / 'tmp'), TMP=str(fixtures / 'tmp'))
ffmpeg = shutil.which('ffmpeg')
assert ffmpeg
def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
def run(name, *values):
    command = [ffmpeg, '-hide_banner', '-loglevel', 'error', *map(str, values), str(fixtures / name)]
    assert not (fixtures / name).exists()
    subprocess.run(command, env=env, check=True)
    (fixtures / (name + '.argv.json')).write_text(json.dumps(command, indent=2) + '\n')

english = '1\n00:00:01,000 --> 00:00:02,500\nEnglish first\n\n2\n00:00:04,000 --> 00:00:05,500\nEnglish second\n\n3\n00:00:08,000 --> 00:00:09,500\nEnglish third\n'
german = '1\n00:00:02,000 --> 00:00:03,500\nDeutsch eins\n\n2\n00:00:06,000 --> 00:00:07,500\nDeutsch zwei\n'
(fixtures / 'english.srt').write_text(english, encoding='utf-8')
(fixtures / 'german.srt').write_text(german, encoding='utf-8')
(fixtures / 'english.ass').write_text('[Script Info]\nScriptType: v4.00+\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,24,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:01.00,0:00:02.50,Default,,0,0,0,,English first\nDialogue: 0,0:00:04.00,0:00:05.50,Default,,0,0,0,,English second\nDialogue: 0,0:00:08.00,0:00:09.50,Default,,0,0,0,,English third\n', encoding='utf-8')
control = fixtures / 'control.mkv'
run('embedded-text.mkv', '-i', control, '-i', fixtures / 'english.srt', '-i', fixtures / 'german.srt',
    '-map', '0:v', '-map', '0:a', '-map', '1:s', '-map', '2:s', '-c', 'copy',
    '-metadata:s:s:0', 'language=eng', '-metadata:s:s:1', 'language=deu', '-disposition:s:0', 'default', '-disposition:s:1', '0')
run('embedded-ass.mkv', '-i', control, '-i', fixtures / 'english.ass', '-map', '0:v', '-map', '0:a', '-map', '1:s', '-c', 'copy')
run('embedded-text.mp4', '-i', control, '-i', fixtures / 'english.srt', '-map', '0:v', '-map', '0:a', '-map', '1:s', '-c', 'copy', '-c:s', 'mov_text')
for name, size in [('wide.mkv', '5760x720'), ('portrait.mkv', '720x2160'), ('preview-4k-long-gop.mkv', '3840x2160')]:
    run(name, '-f', 'lavfi', '-i', 'testsrc2=size=' + size + ':rate=12', '-t', '12',
        '-an', '-c:v', 'libx264', '-preset', 'ultrafast', '-g', '48', '-keyint_min', '48', '-sc_threshold', '0',
        '-pix_fmt', 'yuv420p', '-threads', '1')
request = urllib.request.Request('https://api.github.com/repos/Darkaxt/vlc/releases/latest',
    headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'Modern-VLC-Fork-M2-qualification', 'X-GitHub-Api-Version': '2022-11-28'})
with urllib.request.urlopen(request) as response:
    assert response.status == 200 and response.url == request.full_url
    metadata = response.read(1024 * 1024 + 1)
assert len(metadata) <= 1024 * 1024
release = json.loads(metadata)
assert not release['draft'] and not release['prerelease'] and release['tag_name'] == 'redesign-v1.1.1'
(fixtures / 'github-latest.json').write_bytes(metadata)
manifest = {'purpose': 'Current1.1.2 first-run, subtitle selection/timing and window/preview regression qualification',
    'generated_media_license': 'CC0-1.0', 'user_media_read': False, 'public_release_https': request.full_url,
    'files': [{'file': path.name, 'bytes': path.stat().st_size, 'sha256': digest(path)}
        for path in sorted(fixtures.iterdir()) if path.is_file() and not path.name.endswith('.argv.json')]}
(fixtures / 'first-run-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'fixtures': str(fixtures), 'files': len(manifest['files']), 'bytes': sum(item['bytes'] for item in manifest['files'])}))

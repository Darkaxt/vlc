"""Render the maintained Figma cone into the Windows multi-size application icon.

Uses the installed ImageMagick renderer and Pillow; no downloaded artwork,
Windows icon-cache reset, pinned-shortcut changes or profile mutation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from PIL import Image

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--scratch', type=Path, required=True)
parser.add_argument('--svg-only', action='store_true', help='Emit the matching vector without regenerating the verified PE icon')
args = parser.parse_args()
repo = Path(__file__).resolve().parents[2]
scratch = args.scratch.resolve()
assert scratch.is_relative_to(Path('E:/Temp'))
assert not scratch.exists(), 'Preserve an existing generation receipt'
scratch.mkdir(parents=True)
source = repo / 'modules/gui/qt/pixmaps/redesign/vlc.svg'
original = source.read_text(encoding='utf-8')
assert original.count('fill="white"') == 3
colored = original.replace('fill="white"', 'fill="#d37918"')
svg = scratch / 'app.svg'
svg.write_text(colored, encoding='utf-8', newline='\n')
if args.svg_only:
    target = repo / 'modules/gui/qt/pixmaps/redesign/app.svg'
    target.write_text(colored, encoding='utf-8', newline='\n')
    (scratch / 'icon-generation.json').write_text(json.dumps({
        'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'output': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'only_fill_changed': target.read_text().replace('fill="#d37918"', 'fill="white"') == original,
        'color': '#d37918', 'PE_icon_unchanged': True}, indent=2) + '\n')
    raise SystemExit(0)
png = scratch / 'app-256.png'
renderer = shutil.which('magick')
assert renderer, 'Use the installed SVG renderer'
env = dict(os.environ, MAGICK_TEMPORARY_PATH=str(scratch), TEMP=str(scratch), TMP=str(scratch))
subprocess.run([renderer, '-background', 'none', '-density', '768', str(svg),
    '-resize', '256x256', str(png)], env=env, check=True)
image = Image.open(png).convert('RGBA')
assert image.size == (256, 256) and image.getpixel((0, 0))[3] == 0
assert image.getbbox() and any(p[0:3] == (211, 121, 24) and p[3] == 255 for p in image.get_flattened_data())
destination = repo / 'share/icons/vlc.ico'
destination.parent.mkdir(parents=True, exist_ok=True)
sizes = [(n, n) for n in (16, 20, 24, 32, 40, 48, 64, 128, 256)]
image.save(destination, format='ICO', sizes=sizes)
shutil.copyfile(png,repo / 'modules/gui/qt/pixmaps/redesign/app.png')
icon = Image.open(destination)
assert icon.ico.sizes() == set(sizes)
for size in sizes:
    frame = icon.ico.getimage(size).convert('RGBA')
    assert frame.size == size and frame.getpixel((0, 0))[3] == 0 and frame.getbbox()
receipt = {'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'color': '#d37918', 'output': str(destination), 'sizes': sizes,
    'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'transparent_corners': True}
(scratch / 'icon-generation.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))

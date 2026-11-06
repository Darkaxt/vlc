"""Build optically aligned display frames from the preserved original MPV artwork.

The extracted ICO and native PNGs remain unchanged provenance. Only transparent
outer padding is removed from its largest embedded frame; no shape is redrawn.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
from PIL import Image

repo=Path(__file__).resolve().parents[2]
directory=repo/'modules/gui/qt/pixmaps/redesign'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--verify',action='store_true')
args=parser.parse_args()
source=directory/'mpv.ico';original=source.read_bytes()
provenance=json.loads((directory/'mpv-source.json').read_text())
assert hashlib.sha256(original).hexdigest()==provenance['sha256']
ico=Image.open(source);master=ico.ico.getimage((256,256)).convert('RGBA')
bounds=master.getchannel('A').getbbox()
assert bounds==(9,11,246,248) and bounds[2]-bounds[0]==bounds[3]-bounds[1]
cropped=master.crop(bounds)
payloads=[];files=[]
def save(name,data):
    path=directory/name
    if args.verify:assert path.read_bytes()==data,('Regenerate the display asset',name)
    else:path.write_bytes(data)
for size in (16,24,32,48,64,256):
    # Pillow resamples RGBA in premultiplied-alpha space to avoid dark halos.
    image=cropped.resize((size,size),Image.Resampling.LANCZOS)
    output=io.BytesIO();image.save(output,format='PNG',optimize=True)
    data=output.getvalue();save(f'mpv-display-{size}.png',data);payloads.append((size,data))
    raw=ico.ico.getimage((size,size)).convert('RGBA')
    def opaque_diameter(im):
        box=im.getchannel('A').point(lambda a:255 if a>=240 else 0).getbbox()
        return max(box[2]-box[0],box[3]-box[1])
    files.append({'size':size,'sha256':hashlib.sha256(data).hexdigest(),
        'decoded_rgba_sha256':hashlib.sha256(image.tobytes()).hexdigest(),
        'original_opaque_diameter':opaque_diameter(raw),'display_opaque_diameter':opaque_diameter(image)})
header=struct.pack('<HHH',0,1,len(payloads));offset=6+16*len(payloads);entries=[]
for size,data in payloads:
    entries.append(struct.pack('<BBBBHHII',size%256,size%256,0,0,1,32,len(data),offset));offset+=len(data)
display=header+b''.join(entries)+b''.join(data for size,data in payloads)
save('mpv-display.ico',display)
record={'source':'mpv.ico','source_sha256':hashlib.sha256(original).hexdigest(),
    'source_frame':[256,256],'alpha_bounds':bounds,'resampling':'premultiplied RGBA Lanczos',
    'recipe':'Crop only fully transparent outer padding from largest original frame, then downsample each display size',
    'sha256':hashlib.sha256(display).hexdigest(),'frames':files}
save('mpv-display-source.json',(json.dumps(record,indent=2)+'\n').encode('utf-8'))
assert source.read_bytes()==original
print(json.dumps({'verified':args.verify,'source_unchanged':True,'display':record},indent=2))

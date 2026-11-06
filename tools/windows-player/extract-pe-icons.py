"""Extract Windows icon groups byte-for-byte; never execute or modify the PE."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import pefile
from PIL import Image, ImageDraw

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--executable',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
source=args.executable.resolve(strict=True)
destination=args.output.resolve()
assert not destination.exists(),'Keep an existing extraction and its provenance'
destination.mkdir(parents=True)
with source.open('rb') as stream:source_hash=hashlib.file_digest(stream,'sha256').hexdigest()
resources={};groups=[]
with pefile.PE(str(source),fast_load=True) as pe:
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
    for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if kind.id not in (3,14):continue
        for item in kind.directory.entries:
            for language in item.directory.entries:
                entry=language.data.struct;payload=pe.get_data(entry.OffsetToData,entry.Size)
                if kind.id==3:resources[(item.id,language.id)]=payload
                else:groups.append((str(item.name) if item.name else item.id,language.id,payload))
records=[];previews=[]
for index,(identity,language,group) in enumerate(groups):
    reserved,kind,count=struct.unpack_from('<HHH',group)
    assert (reserved,kind)==(0,1)
    entries=[];payloads=[];offset=6+16*count
    for frame in range(count):
        width,height,colors,unused,planes,bits,size,resource=struct.unpack_from('<BBBBHHIH',group,6+14*frame)
        payload=resources[(resource,language)]
        assert len(payload)==size
        entries.append(struct.pack('<BBBBHHII',width,height,colors,unused,planes,bits,size,offset))
        payloads.append(payload);offset+=size
    icon=struct.pack('<HHH',0,1,count)+b''.join(entries)+b''.join(payloads)
    path=destination/('group-'+str(index)+'.ico');path.write_bytes(icon)
    decoded=Image.open(io.BytesIO(icon))
    sizes=sorted(decoded.ico.sizes())
    for size in sizes:
        image=decoded.ico.getimage(size).convert('RGBA')
        png=destination/('group-'+str(index)+'-'+str(size[0])+'.png');image.save(png)
        if size==max(sizes):previews.append((index,image))
    records.append({'group':identity,'language':language,'ico':path.name,'sizes':sizes,
        'sha256':hashlib.sha256(icon).hexdigest(),'frames':[
            {'resource_id':struct.unpack_from('<H',group,6+14*n+12)[0],
             'sha256':hashlib.sha256(payload).hexdigest()} for n,payload in enumerate(payloads)]})
sheet=Image.new('RGB',(320*len(previews),360),'#1b1b1b');draw=ImageDraw.Draw(sheet)
for position,(index,frame) in enumerate(previews):
    frame.thumbnail((256,256),Image.Resampling.LANCZOS)
    sheet.paste(frame,(position*320+(320-frame.width)//2,32),frame)
    draw.text((position*320+24,310),'PE group '+str(index),fill='white')
sheet.save(destination/'groups.png')
report={'source_executable':str(source),'source_sha256':source_hash,'groups':records,
    'read_only_pe_inspection':True,'original_icon_payloads_preserved':True}
(destination/'extraction.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(report))

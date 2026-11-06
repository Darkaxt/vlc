"""Create a retained synthetic video long enough for interactive miniplayer checks."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

root=Path('D:/VLC-Redesign/build/windows-x64/m2-regression-fixtures')
target=root/'miniplayer-long.mkv'
assert root.is_dir() and not target.exists()
ffmpeg=shutil.which('ffmpeg');probe=shutil.which('ffprobe');assert ffmpeg and probe
command=[ffmpeg,'-hide_banner','-loglevel','error','-f','lavfi','-i',
    'testsrc2=size=640x360:rate=1','-t','600','-an','-c:v','libx264',
    '-preset','ultrafast','-pix_fmt','yuv420p','-threads','1',str(target)]
subprocess.run(command,check=True)
details=json.loads(subprocess.check_output([probe,'-v','error','-show_format','-show_streams','-of','json',str(target)],text=True))
assert float(details['format']['duration'])==600 and len(details['streams'])==1
assert details['streams'][0]['codec_type']=='video'
sidecar=target.with_suffix('.mkv.argv.json');sidecar.write_text(json.dumps(command,indent=2)+'\n')
retention=root.parent/'m2-regression-retention.json';record=json.loads(retention.read_text())
for path in (target,sidecar):
    record['files'].append({'name':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
record['miniplayer_fixture']='600-second640x360 synthetic1fps test pattern; hover/drag checks must not race the12-second EOF fixture. Same weekly regression consumer and retirement contract; never package.'
retention.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'fixture':str(target),'duration':600,'bytes':target.stat().st_size}))

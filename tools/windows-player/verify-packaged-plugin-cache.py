"""Exercise the shipped module index through real Windows ZIP extractors."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import time
import zipfile
from package_plugin_cache import PACKAGE_EPOCH, archive_info, digest, generate

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--runtime',type=Path,required=True)
p.add_argument('--scratch',type=Path,required=True)
p.add_argument('--seven-zip',type=Path,required=True)
a=p.parse_args();source=a.runtime.resolve();root=a.scratch.resolve()
assert root.is_relative_to(Path('D:/Temp')) and not root.exists()
assert a.seven_zip.is_file() and (source/'vlc.exe').is_file()
root.mkdir();package=root/'package'
shutil.copytree(source,package,ignore=shutil.ignore_patterns('portable','plugins.dat'))
(package/'portable').mkdir()
receipt={'scope':'Exact stripped DLL bytes; native module checks, relocation,7-Zip and PowerShell extraction; no UI or real profile', 'checks':[], 'passed':False}
result=root/'result.json'
def save():result.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
save()
cache=generate(package);assert cache['plugin_count']==410
assert len({row['file'] for row in cache['plugins']})==410
for row in cache['plugins']:assert digest(source/row['file'])==row['sha256']
receipt['cache']=cache
def native(runtime,label,stale=False):
    env=dict(os.environ,TEMP=str(root),TMP=str(root),VLC_USERDATA_PATH=str(runtime/'portable'),VLC_CONFIG_PATH=str(runtime/'portable'))
    env.pop('VLC_PLUGIN_PATH',None)
    command=[str(runtime/'vlc.exe'),'--ignore-config','--intf=dummy','--no-one-instance','--no-media-library','--no-metadata-network-access','--verbose=2','--play-and-exit','vlc://quit']
    started=time.perf_counter()
    with (root/(label+'.stdout')).open('wb') as out,(root/(label+'.stderr')).open('wb') as err:
        process=subprocess.run(command,cwd=runtime,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    elapsed=time.perf_counter()-started;log=(root/(label+'.stderr')).read_text(encoding='utf-8',errors='replace')
    assert process.returncode==0 and 'plug-ins loaded: 603 modules' in log
    assert not any(text in log for text in ('cannot read','cannot load plug-in','could not load module'))
    assert ('stale plugins cache: modified' in log)==stale
    row={'label':label,'seconds_including_core_teardown':elapsed,'exit_code':process.returncode,'module_count':603,'stale_module_rejected':stale}
    receipt['checks'].append(row);save();print(json.dumps(row),flush=True)
native(package,'generated')
archive=root/'package.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as target:
    target.writestr('package/portable/','')
    for file in sorted(package.rglob('*')):
        if file.is_file():target.writestr(archive_info('package/'+file.relative_to(package).as_posix()),file.read_bytes())
with zipfile.ZipFile(archive) as target:
    for entry in target.infolist():
        if not entry.filename.endswith('.dll'):continue
        assert entry.extra[:9]==struct.pack('<HHBI',0x5455,5,1,PACKAGE_EPOCH)
        assert len(entry.extra)==45
for label in ('seven-zip','powershell'):
    extraction=root/label
    if label=='seven-zip':
        command=[str(a.seven_zip),'x',str(archive),'-o'+str(extraction),'-y','-bd']
    else:
        command=['pwsh','-NoProfile','-File',str(Path(__file__).with_name('extract-release-zip.ps1')),'-Archive',str(archive),'-Destination',str(extraction)]
    with (root/(label+'-extract.log')).open('wb') as stream:
        assert subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
    extracted=extraction/'package'
    assert digest(extracted/'plugins/plugins.dat')==cache['cache_sha256']
    for row in cache['plugins']:
        file=extracted/row['file'];assert int(file.stat().st_mtime)==PACKAGE_EPOCH,(label,row['file'],file.stat().st_mtime)
        assert digest(file)==row['sha256']
    relocated=root/(label+'-relocated')
    assert extracted.is_relative_to(root) and relocated.is_relative_to(root) and not relocated.exists()
    extracted.rename(relocated)
    native(relocated,label+'-relocated')
    changed=relocated/'plugins/video_filter/libadjust_plugin.dll';assert changed.is_file()
    os.utime(changed,(PACKAGE_EPOCH+2,PACKAGE_EPOCH+2))
    native(relocated,label+'-stale',stale=True)
receipt.update(passed=True,archive_sha256=digest(archive),zip_bytes=archive.stat().st_size)
save();print(json.dumps({'passed':True,'result':str(result)}))

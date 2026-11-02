"""Build native boundary checks from the actual old/new HEIF offset guards.

This focused arithmetic regression does not claim a crafted-file crash
reproduction. Real grid-file playback is a separate packaged acceptance check.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--baseline',required=True)
a=p.parse_args()
assert Path('/proc/self/cgroup').read_text().split('::',1)[1].strip().startswith('/llm-coordinator/')
a.output.mkdir(parents=True,exist_ok=True)
name='modules/demux/mp4/heif.c'
texts={'fixed':(a.source/name).read_text(), 'baseline':subprocess.check_output(['git','-C',str(a.source),'show',a.baseline+':'+name],text=True)}
records=[]
for label,text in texts.items():
    function=text[text.index('static int LoadGridImage('):text.index('static int DerivedImageAssembleGrid(')]
    if label=='fixed':
        guard=re.search(r'unsigned offset_len;\s*if \((.*?)\)\s*\{\s*picture_Release',function,re.S).group(1)
        declaration='unsigned offset_len;'
    else:
        guard=re.search(r'if \((i_buffer < offsetpxh.*?)\)\s*\{\s*picture_Release',function,re.S).group(1)
        declaration=''
    code='''#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdckdint.h>
static int rejected(unsigned offsetpxh, unsigned imagewidth, size_t i_buffer) {
DECLARATION
    if (GUARD) return 1;
    return 0;
}
int main(void) {
    if (sizeof(unsigned)!=4 || sizeof(size_t)!=8) return 2;
    if (rejected(0,1920,16)) return 3;
    if (rejected(2,3,24)) return 4;
    if (!rejected(2,3,23)) return 5;
    if (rejected(1073741823u,1,UINT_MAX)) return 6;
    if (!rejected(1073741824u,4,16)) return 1;
    if (!rejected(65536u,16384,16)) return 1;
    puts("actual HEIF guard rejects both multiplication overflows and short destination; valid boundaries pass");
    return 0;
}
'''.replace('DECLARATION',declaration).replace('GUARD',guard)
    source=a.output/(label+'.c');binary=a.output/(label+'.exe')
    source.write_text(code)
    command=['x86_64-w64-mingw32-gcc','-std=gnu2x','-O2','-g0','-static-libgcc','-o',str(binary),str(source)]
    subprocess.run(command,check=True)
    records.append({'case':label,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'extracted_guard':guard,
        'heif_source_sha256':hashlib.sha256(text.encode()).hexdigest(),'expected_native_exit':0 if label=='fixed' else 1,'compiler_argv':command})
(a.output/'build.json').write_text(json.dumps({'scope':__doc__,'cases':records},indent=2)+'\n')
print(json.dumps({'native_HEIF_boundary_binaries_built':True,'execution':'Pending native Windows acceptance'}),flush=True)

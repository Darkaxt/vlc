"""Add the pinned private swapchain accessor using the retained QtGui build.

Run only inside the managed toolchain. No configure, SDK bootstrap or other
dependency rebuild. On failure the installed archive remains unchanged until
the Gui target succeeds. Recovery reverses the recorded patch, rebuilds Gui,
then verifies the preimage archive hash before restaging an older application.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

PATCH='0003-Expose-the-existing-backing-store-swapchain.patch'
PATCH_SHA256='0a11ce8fd003bbf74ebcd1f5f4e333ba629c331f9ae657edda0d73d5b2a5f610'

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--receipt-root',required=True,type=Path)
    parser.add_argument('--runtime',required=True,type=Path)
    args=parser.parse_args()
    group=Path('/proc/self/cgroup').read_text().split('::',1)[1].strip()
    assert group.startswith('/llm-coordinator/') and Path('/.vlc-s8-toolchain.json').is_file()
    patch=args.source/'contrib/src/qt'/PATCH
    assert sha(patch)==PATCH_SHA256
    qt=Path('/work/build/contrib/contrib-win64/qt')
    build=qt/'vlc_build'
    prefix=Path('/work/build/contrib/x86_64-w64-mingw32')
    installed=prefix/'lib/libQt6Gui.a'
    header=prefix/'include/QtGui/6.8.3/QtGui/qpa/qplatformbackingstore.h'
    assert installed.is_file() and (build/'build.ninja').is_file()
    root=args.receipt_root
    assert not root.exists(),'Inspect/resume the original dependency repair instead of applying again'
    root.mkdir(parents=True)
    sources=['src/gui/painting/qplatformbackingstore.cpp']
    assert header.read_bytes()==(qt/'src/gui/painting/qplatformbackingstore.h').read_bytes()
    before={name:sha(qt/name) for name in sources}
    # These installed static libraries are the current SDK inputs. Retain their
    # identities; only the Gui archive will be installed. Headers stay intact.
    libraries={str(path.relative_to(prefix)):sha(path) for path in sorted((prefix/'lib').glob('libQt6*.a'))}
    record={'schema':'vlc_redesign.qt_backingstore_repair.v1','group':group,
        'source_commit':subprocess.check_output(['git','-C',str(args.source),'rev-parse','HEAD'],text=True).strip(),
        'patch':PATCH,'patch_sha256':PATCH_SHA256,'before_sources':before,
        'before_libraries':libraries,'before_installed_header_sha256':sha(header),
        'recovery':'Reverse the exact recorded patch in retained Qt source; rebuild lib/libQt6Gui.a; verify before_libraries Gui hash before copying it back. Headers were not changed.'}
    (root/'started.json').write_text(json.dumps(record,indent=2)+'\n')
    subprocess.run(['git','apply','--check',str(patch)],cwd=qt,check=True)
    subprocess.run(['git','apply',str(patch)],cwd=qt,check=True)
    with (root/'ninja-plan.log').open('xb') as log:
        subprocess.run(['ninja','-C',str(build),'-n','lib/libQt6Gui.a'],stdout=log,stderr=subprocess.STDOUT,check=True)
    plan=(root/'ninja-plan.log').read_text()
    assert 'Re-running CMake' not in plan,'Relevant configuration changed; inspect before rebuilding'
    with (root/'build.log').open('xb') as log:
        subprocess.run(['ninja','-C',str(build),'-j1','lib/libQt6Gui.a'],stdout=log,stderr=subprocess.STDOUT,check=True)
    object_file=build/'src/gui/CMakeFiles/Gui.dir/painting/qplatformbackingstore.cpp.obj'
    assert b'_vlc_widget_rhi\0' in object_file.read_bytes()
    (root/'bridge-object.json').write_text(json.dumps({'object':str(object_file),
        'sha256':sha(object_file),'headers_and_ABI_unchanged':True})+'\n')
    for name,value in libraries.items():
        assert sha(prefix/name)==value,'Installed SDK changed concurrently: '+name
    output=build/'lib/libQt6Gui.a'
    assert sha(output)!=libraries['lib/libQt6Gui.a']
    shutil.copyfile(output,installed)
    assert sha(header)==record['before_installed_header_sha256']
    after={name:sha(prefix/name) for name in libraries}
    assert {name for name in libraries if libraries[name]!=after[name]}=={'lib/libQt6Gui.a'}
    record.update(after_sources={name:sha(qt/name) for name in sources},after_libraries=after,
        after_library_stats={name:{'bytes':(prefix/name).stat().st_size,
            'mtime_ns':(prefix/name).stat().st_mtime_ns} for name in libraries},
        installed_gui_sha256=sha(installed),installed_header_sha256=sha(header),
        target='lib/libQt6Gui.a',configuration_reused=True,compiler_jobs=1,
        no_other_installed_archives_changed=True,no_global_flags_or_VLC_core_ABI_change=True)
    (root/'complete.json').write_text(json.dumps(record,indent=2)+'\n')
    (args.runtime/'VLC-QT-BACKINGSTORE-REPAIR.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'qt_backingstore_repaired':True,'gui_archive_sha256':sha(installed),
        'receipt':str(root/'complete.json')}),flush=True)

if __name__=='__main__':main()

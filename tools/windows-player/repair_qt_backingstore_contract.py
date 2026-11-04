"""Exact private QtGui-only exception to the retained non-Qt plugin guard."""
import hashlib
import json
from pathlib import Path
import subprocess

PATCH='contrib/src/qt/0003-Expose-the-existing-backing-store-swapchain.patch'
PATCH_SHA256='ec33d822136e1c79faa62b5c112233e9d4cf7edf6787389d904519eabf0e758e'
RULES='contrib/src/qt/rules.mak'

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def verify_qt_accessor(source,runtime,baseline,changes):
    special={PATCH,RULES}&set(changes)
    receipt=runtime/'VLC-QT-BACKINGSTORE-REPAIR.json'
    if not special and not receipt.exists():return {'allowed_source_paths':[],'applied':False}
    assert sha(source/PATCH)==PATCH_SHA256,'Unexpected Qt dependency patch'
    if RULES in special:
        before=subprocess.check_output(['git','-C',str(source),'show',baseline+':'+RULES],text=True)
        added='\t$(APPLY) $(SRC)/qt/'+Path(PATCH).name+'\n'
        assert (source/RULES).read_text()==before.replace(added,'').replace(
            '\t$(APPLY) $(SRC)/qt/0002-Mingw-own-regex-JIT-in-QThreadStorage.patch\n',
            '\t$(APPLY) $(SRC)/qt/0002-Mingw-own-regex-JIT-in-QThreadStorage.patch\n'+added)
    data=json.loads(receipt.read_text())
    assert data['schema']=='vlc_redesign.qt_backingstore_repair.v1' and data['patch_sha256']==PATCH_SHA256
    assert data['no_other_installed_archives_changed'] and data['no_global_flags_or_VLC_core_ABI_change']
    assert {name for name,value in data['before_libraries'].items() if value!=data['after_libraries'][name]}=={'lib/libQt6Gui.a'}
    prefix=Path('/work/build/contrib/x86_64-w64-mingw32')
    assert sha(prefix/'lib/libQt6Gui.a')==data['installed_gui_sha256']
    assert sha(prefix/'include/QtGui/6.8.3/QtGui/qpa/qplatformbackingstore.h')==data['installed_header_sha256']
    for name,expected in data['after_library_stats'].items():
        actual=(prefix/name).stat()
        if actual.st_size!=expected['bytes'] or actual.st_mtime_ns!=expected['mtime_ns']:
            assert sha(prefix/name)==data['after_libraries'][name],'Unverified SDK archive change: '+name
    # Qt is statically linked into the replaced GUI plugin. The other plugin
    # binaries and VLC public ABI remain bound by the ordinary complete guard.
    return {'allowed_source_paths':[PATCH,RULES],'applied':True,
        'patch_sha256':PATCH_SHA256,'receipt_sha256':sha(receipt),
        'only_changed_static_archive':'lib/libQt6Gui.a'}

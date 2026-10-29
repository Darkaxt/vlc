"""Read-only before/after evidence for installed VLC's exact settings owners."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import winreg


def snapshot():
    records = []
    for base in [Path(os.environ['APPDATA'])/'vlc', Path(os.environ['LOCALAPPDATA'])/'vlc']:
        for relative in ['vlcrc','vlc-qt-interface.ini','ml.db','ml.db-wal','ml.db-shm','ml/ml.db','ml/ml.db-wal','ml/ml.db-shm','vlc-qt-interface.ini.bak']:
            path = base/relative
            record = {'path':str(path),'exists':path.is_file()}
            if path.is_file():
                with path.open('rb') as source:
                    record.update(bytes=path.stat().st_size,sha256=hashlib.file_digest(source,'sha256').hexdigest())
            records.append(record)
    language = {'key_exists':False,'value_exists':False}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\VideoLAN\VLC',0,winreg.KEY_READ) as key:
            language['key_exists'] = True
            try:
                value,kind = winreg.QueryValueEx(key,'Lang')
                language.update(value_exists=True,value=value,kind=kind)
            except FileNotFoundError:
                pass
    except FileNotFoundError:
        pass
    return {'files':records,'windows_language':language}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--compare',type=Path)
    options = parser.parse_args()
    current = snapshot()
    if options.compare:
        baseline = json.loads(options.compare.read_text(encoding='utf-8'))
        current = {'unchanged':current == baseline,'before':str(options.compare),'current':current}
    options.output.parent.mkdir(parents=True,exist_ok=True)
    options.output.write_text(json.dumps(current,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'snapshot_saved':str(options.output),'unchanged':current.get('unchanged')}))
    if options.compare and not current['unchanged']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

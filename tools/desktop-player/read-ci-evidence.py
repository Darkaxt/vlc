#!/usr/bin/env python3
"""Read named small evidence files without downloading a native binary artifact.

Uses the current gh credential only for GitHub's artifact redirect. Signed blob
range requests carry no GitHub credential. ZIP CRC validates selected members;
this is diagnostic retrieval, not whole-artifact release hash verification.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request
import zipfile


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


class Artifact(io.RawIOBase):
    def __init__(self, url):
        self.url = url
        self.position = 0
        self.downloaded = 0
        self.length = None
        self.read_range(0, 1)

    def read_range(self, start, size):
        request = urllib.request.Request(self.url,
            headers={'Range': f'bytes={start}-{start + size - 1}'})
        with urllib.request.urlopen(request) as response:
            if response.status != 206:
                raise RuntimeError('Artifact server did not honor the bounded Range request')
            match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers['Content-Range'])
            if not match or int(match[1]) != start:
                raise RuntimeError('Unexpected artifact range')
            self.length = int(match[3])
            result = response.read(size + 1)
        if len(result) != size:
            raise RuntimeError('Truncated or excessive artifact range')
        self.downloaded += size
        return result

    def seek(self, offset, whence=0):
        self.position = offset + (self.position if whence == 1 else self.length if whence == 2 else 0)
        return self.position

    def tell(self):
        return self.position

    def read(self, size=-1):
        size = self.length - self.position if size < 0 else min(size, self.length - self.position)
        if size > 4 * 1024 * 1024:
            raise RuntimeError('Only small evidence members are permitted')
        if size <= 0:
            return b''
        result = self.read_range(self.position, size)
        self.position += size
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', required=True, type=int)
    parser.add_argument('--member', action='append', default=[])
    parser.add_argument('--list-prefix')
    parser.add_argument('--destination', type=Path)
    args = parser.parse_args()
    if not args.member and args.list_prefix is None:
        parser.error('Select explicit members or an evidence listing prefix')
    if args.member and args.destination is None:
        parser.error('Named members require an explicit destination')
    token = subprocess.check_output(['gh', 'auth', 'token'], text=True).strip()
    request = urllib.request.Request(
        f'https://api.github.com/repos/Darkaxt/vlc/actions/artifacts/{args.artifact}/zip',
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'})
    try:
        urllib.request.build_opener(NoRedirect()).open(request)
        raise RuntimeError('Expected the artifact API redirect')
    except urllib.error.HTTPError as error:
        if error.code != 302:
            raise
        archive_url = error.headers['Location']
    del token, request
    source = Artifact(archive_url)
    members = []
    with zipfile.ZipFile(source) as archive:
        if args.list_prefix is not None:
            members.extend({'member': entry.filename, 'bytes': entry.file_size}
                for entry in archive.infolist() if entry.filename.startswith(args.list_prefix))
        if args.member:
            args.destination.mkdir(parents=True, exist_ok=True)
        for name in args.member:
            matches = [entry for entry in archive.infolist() if entry.filename.endswith('/' + name)]
            if len(matches) != 1:
                raise RuntimeError(f'Expected one evidence member {name}: {len(matches)}')
            entry = matches[0]
            if entry.file_size > 4 * 1024 * 1024:
                raise RuntimeError('Selected evidence member exceeds the small-file boundary')
            content = archive.read(entry)
            destination = args.destination / Path(name).name
            with destination.open('xb') as stream:
                stream.write(content)
            members.append({'member': entry.filename, 'bytes': len(content),
                            'sha256': hashlib.sha256(content).hexdigest(), 'path': str(destination)})
    print(json.dumps({'artifact': args.artifact, 'range_bytes': source.downloaded,
                      'members': members, 'whole_artifact_hash_verified': False}, indent=2))


if __name__ == '__main__':
    main()

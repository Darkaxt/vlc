"""Retrieve pinned source archives; callers verify their original checksums."""
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import urllib.parse
import urllib.request


def retrieve(url, destination, source=None):
    parsed = urllib.parse.urlsplit(url)
    asset = re.fullmatch(r'/([^/]+)/([^/]+)/releases/download/([^/]+)/([^/]+)', parsed.path)
    if (os.environ.get('GITHUB_ACTIONS') == 'true' and parsed.scheme == 'https'
            and parsed.netloc == 'github.com' and not parsed.query and asset):
        if not os.environ.get('GH_TOKEN'):
            raise RuntimeError('Native CI source retrieval requires its existing read-only GitHub token')
        owner, repo, tag, name = map(urllib.parse.unquote, asset.groups())
        # GitHub's release client resolves the asset through the supported API.
        # Preserve the exact tag/name and caller's checksum, with no retry or
        # fallback to a different archive after an uncertain transfer.
        subprocess.run(['gh', 'release', 'download', tag, '--repo', owner + '/' + repo,
                        '--pattern', name, '--output', str(Path(destination))], check=True)
    elif (os.environ.get('GITHUB_ACTIONS') == 'true' and parsed.scheme == 'https'
            and parsed.netloc == 'archive.ubuntu.com' and parsed.path.startswith('/ubuntu/pool/')):
        # Hosted runners intermittently receive 403s and truncated bodies from
        # the global archive. Their own apt mirror serves the identical pool;
        # the caller's original checksum still decides acceptance.
        # When the caller names the Debian source package and version, Launchpad's
        # librarian (which stores every primary-archive source file) is the last
        # transport for the same exact filename.
        mirrors = [urllib.parse.urlunsplit(parsed._replace(netloc='azure.archive.ubuntu.com'))]
        if source:
            package, version = source
            mirrors.append('https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/'
                           + '/'.join(urllib.parse.quote(part, safe='+~')
                                      for part in (package, version, PurePosixPath(parsed.path).name)))
        try:
            urllib.request.urlretrieve(url, destination)
        except OSError as error:
            failure = error
            for mirror in mirrors:
                print('SOURCE MIRROR ' + url + ' -> ' + mirror + ': ' + str(failure), flush=True)
                try:
                    urllib.request.urlretrieve(mirror, destination)
                    return
                except OSError as next_failure:
                    failure = next_failure
            raise failure
    else:
        urllib.request.urlretrieve(url, destination)

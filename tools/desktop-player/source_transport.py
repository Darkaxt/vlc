"""Retrieve pinned source archives; callers verify their original checksums."""
import os
from pathlib import Path
import re
import subprocess
import urllib.parse
import urllib.request


def retrieve(url, destination):
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
    else:
        urllib.request.urlretrieve(url, destination)

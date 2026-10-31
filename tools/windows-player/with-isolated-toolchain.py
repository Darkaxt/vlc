"""Run the pinned toolchain in a private mount namespace through the WSL gate.

The extracted filesystem and all build/source/runtime files belong to the D: task.
No distribution is imported, registered, configured, upgraded or retired here.
The existing Ubuntu installation supplies only the already available kernel,
Python and mount utilities. Every operation stays in the admitted cgroup.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--scratch', required=True, type=Path)
parser.add_argument('--initialize', action='store_true')
parser.add_argument('--inside-namespace', action='store_true', help=argparse.SUPPRESS)
parser.add_argument('command', nargs=argparse.REMAINDER)
args = parser.parse_args()
root = args.scratch.resolve(strict=True)
temporary = root.parent == Path('/mnt/d/Temp') and root.name.startswith('vlc-s8-')
retained = root == Path('/mnt/d/VLC-Redesign/build/windows-x64')
assert temporary or retained, 'Use the exact task root or verified project build binding'
if retained:
    retention = json.loads((root / 'build-retention.json').read_text())
    assert retention['schema'] == 'vlc_redesign.retained_build.v1'
    assert retention['state'] == 'moved'
    assert retention['consumer'] == 'vlc-weekly-upstream-sync-and-release'
    assert retention['destination'] == 'D:/VLC-Redesign/build/windows-x64'
    retained_marker = json.loads((root / 'toolchain/.vlc-s8-toolchain.json').read_text())
    assert retention['toolchain_marker'] == retained_marker
    assert not args.initialize, 'Retained inputs must not be reinitialized'
cgroup = Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1]
assert cgroup.startswith('/llm-coordinator/'), 'Use the installed WSL gate; direct launch is unsupported'
cap = Path('/sys/fs/cgroup' + cgroup + '/memory.max').read_text().strip()
assert cap != 'max' and int(cap) <= 3758096384
if not args.inside_namespace:
    parameters = sys.argv[1:]
    # Wait outside the private mount/PID namespace. Its init's exit closes the
    # whole mount unit, including inherited locked /dev and /sys submounts that
    # cannot be individually unmounted in a less-privileged user namespace.
    result = subprocess.run(['/usr/bin/unshare', '--user', '--map-root-user', '--mount', '--pid', '--fork', '--propagation', 'private',
        sys.executable, str(Path(__file__).resolve()), '--inside-namespace', *parameters])
    mount_root = str(root / 'toolchain')
    remaining = [line.split()[4] for line in Path('/proc/self/mountinfo').read_text().splitlines()
                 if line.split()[4] == mount_root or line.split()[4].startswith(mount_root + '/')]
    assert not remaining, 'Owned mount escaped its private namespace: ' + repr(remaining)
    ownership = root / 'evidence/toolchain-filesystem.json'
    if ownership.is_file():
        receipt = json.loads(ownership.read_text())
        receipt['last_mount_cleanup_failures'] = []
        receipt['last_namespace_exit_code'] = result.returncode
        receipt['mount_release'] = 'private PID/mount namespace exited; no owned mounts in caller namespace'
        ownership.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'private_mounts_released': True, 'namespace_exit_code': result.returncode}), flush=True)
    raise SystemExit(result.returncode)

assert os.geteuid() == 0
uid_map = Path('/proc/self/uid_map').read_text().strip().split()
assert len(uid_map) == 3 and uid_map[0] == '0' and uid_map[2] == '1', 'Require one mapped host user, not host-root escalation'
ownership = root / 'evidence/toolchain-filesystem.json'
mount = root / 'toolchain'
archive = root / 'downloads/toolchain-rootfs.tar'
inputs = json.loads((root / 'inputs.json').read_text())
source = next(value for value in inputs if value.get('image'))

def run(*command, **kwargs):
    subprocess.run(command, check=True, **kwargs)

def save(value):
    ownership.parent.mkdir(parents=True, exist_ok=True)
    ownership.write_text(json.dumps(value, indent=2) + '\n')

if not mount.exists():
    assert args.initialize and not ownership.exists()
    assert archive.stat().st_size == source['bytes']
    with archive.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == source['sha256']
    mount.mkdir()
    receipt = {'schema': 'vlc_redesign.s8_toolchain_filesystem.v1', 'uuid': str(uuid.uuid4()),
        'filesystem': str(mount), 'source': source, 'phase': 'formatted',
        'placement': 'D: task-owned toolchain filesystem; no Ubuntu user/configuration data',
        'host_uid_mapping': uid_map, 'initialization_cgroup': cgroup, 'memory_max': cap}
    save(receipt)
else:
    assert mount.is_dir() and not mount.is_symlink() and ownership.is_file()
    receipt = json.loads(ownership.read_text())
    assert receipt['source']['sha256'] == source['sha256']
    assert receipt['phase'] in ('formatted', 'initialized'), 'Inspect partial extraction; do not overwrite it'

assert receipt['host_uid_mapping'] == uid_map
assert not mount.is_mount()
mounted = []
try:
    run('/usr/bin/mount', '--bind', str(mount), str(mount))
    mounted.append(mount)
    marker = mount / '.vlc-s8-toolchain.json'
    if receipt['phase'] == 'formatted':
        assert args.initialize and not any(mount.iterdir())
        receipt['phase'] = 'extracting'
        save(receipt)
        print('Extracting verified image inside admitted private filesystem', flush=True)
        run('/usr/bin/tar', '-xf', str(archive), '-C', str(mount), '--no-same-owner', '--no-same-permissions')
        assert (mount / 'usr/bin/python3').exists()
        assert (mount / 'opt/tools').is_dir()
        marker.write_text(json.dumps({'uuid': receipt['uuid'], 'source_sha256': source['sha256']}) + '\n')
        receipt['phase'] = 'initialized'
        save(receipt)
    assert json.loads(marker.read_text()) == {'uuid': receipt['uuid'], 'source_sha256': source['sha256']}
    for relative in ('work/home', 'work/tmp', 'work/build', 'scratch'):
        (mount / relative).mkdir(parents=True, exist_ok=True)
    share = root / 'scratch-share'
    share.mkdir(exist_ok=True)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    assert command and command[0].startswith('/'), 'Supply an explicit reviewed absolute chroot command'
    for value in command:
        if value.startswith('/scratch/'):
            relative = Path(value).relative_to('/scratch')
            assert len(relative.parts) == 1 and (root / relative).is_file()
            shutil.copyfile(root / relative, share / relative)
    # A new user namespace needs a procfs belonging to its own PID namespace;
    # binding the host's procfs is rejected by Linux's namespace protection.
    proc = mount / 'proc'
    run('/usr/bin/mount', '-t', 'proc', 'proc', str(proc))
    mounted.append(proc)
    for original, relative in [('/dev', 'dev'), ('/sys', 'sys'),
            (str(share), 'scratch'), ('/etc/resolv.conf', 'etc/resolv.conf')]:
        target = mount / relative
        recursive = original in ('/dev', '/sys')
        # Preserve inherited locked submounts as a unit in a less-privileged
        # namespace; a nonrecursive bind would hide them and Linux rejects it.
        run('/usr/bin/mount', '--rbind' if recursive else '--bind', original, str(target))
        mounted.append((target, recursive))
    (share / 'downloads').mkdir(exist_ok=True)
    run('/usr/bin/mount', '--bind', str(root / 'downloads'), str(mount / 'scratch/downloads'))
    mounted.append((mount / 'scratch/downloads', False))
    # Exact source archives for the current S8 runtime build, without copying
    # them or exposing unrelated host paths to the toolchain.
    mpv_sources = root / 'mpv-source-inputs'
    if mpv_sources.is_dir():
        (share / 'mpv-source-inputs').mkdir(exist_ok=True)
        target = mount / 'scratch/mpv-source-inputs'
        run('/usr/bin/mount', '--bind', str(mpv_sources), str(target))
        mounted.append((target, False))
    environment = ['PATH=/opt/tools/bin:/opt/tools/libexec:/opt/rust/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        'HOME=/work/home', 'TMPDIR=/work/tmp', 'LANG=en_US.UTF-8',
        'WINE_SDK_PATH=/usr/include/wine/wine/windows', 'RUST_HOME=/opt/rust',
        'RUSTUP_HOME=/opt/rust/rustup', 'CARGO_HOME=/opt/rust/cargo', 'WINEPREFIX=/work/wine',
        'JOBS=1', 'CMAKE_BUILD_PARALLEL_LEVEL=1', 'CARGO_BUILD_JOBS=1']
    run('/usr/sbin/chroot', str(mount), '/usr/bin/env', '-i', *environment, *command)
finally:
    # The outer owner waits for namespace exit and records release there. Do
    # not recursively unmount locked inherited children or mask a build error
    # with cleanup errors. No mount namespace descriptor is retained/exported.
    receipt['mount_release'] = 'awaiting private namespace exit'
    save(receipt)

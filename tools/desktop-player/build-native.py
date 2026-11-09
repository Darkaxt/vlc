#!/usr/bin/env python3
"""Build the native Qt redesign and source-pinned libmpv on a hosted native runner.

Builds have one compiler job. Retained inputs are content-bound; a failed build
keeps its outputs for diagnosis/resumption and never triggers a blind clean build.
Packaging and release qualification are separate steps, not inferred from make.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import select
import shlex
import shutil
import signal
import subprocess
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


class NativeBuildCancelled(BaseException):
    def __init__(self, signum):
        self.signum = signum


def cancel_build(signum, frame):
    raise NativeBuildCancelled(signum)


def stop_command(process):
    # The direct child remains unreaped, reserving this owned process-group ID.
    # Cancellation is terminal for this exact command, including configure's
    # shells/compilers, before the workflow snapshots its reusable build.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()
    members = []
    for line in output('ps', '-axo', 'pid=,pgid=,stat=').splitlines():
        pid, group, state = line.split()
        if int(group) == process.pid and not state.startswith('Z'):
            members.append(int(pid))
    if platform.system() == 'Darwin':
        queue = select.kqueue()
        try:
            watched = set()
            for pid in members:
                try:
                    queue.control([select.kevent(pid, filter=select.KQ_FILTER_PROC,
                        flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                        fflags=select.KQ_NOTE_EXIT)], 0, 0)
                    watched.add(pid)
                except ProcessLookupError:
                    pass
            while watched:
                for event in queue.control(None, len(watched)):
                    watched.discard(event.ident)
        finally:
            queue.close()
    else:
        descriptors = []
        try:
            for pid in members:
                try:
                    descriptors.append(os.pidfd_open(pid))
                except ProcessLookupError:
                    pass
            while descriptors:
                readable, _, _ = select.select(descriptors, [], [])
                for descriptor in readable:
                    os.close(descriptor)
                    descriptors.remove(descriptor)
        finally:
            for descriptor in descriptors:
                os.close(descriptor)
    print('NATIVE COMMAND GROUP EXITED', process.pid, flush=True)


def run(*args, cwd=None, env=None):
    print('+', ' '.join(map(str, args)), flush=True)
    signals = (signal.SIGINT, signal.SIGTERM)
    # Register the child before delivering cancellation received during spawn.
    mask = signal.pthread_sigmask(signal.SIG_BLOCK, signals)
    previous = {sig: signal.signal(sig, cancel_build) for sig in (signal.SIGINT, signal.SIGTERM)}
    process = None
    try:
        process = subprocess.Popen(list(map(str, args)), cwd=cwd, env=env, start_new_session=True,
            preexec_fn=lambda: signal.pthread_sigmask(signal.SIG_SETMASK, mask))
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)
        code = process.wait()
    except NativeBuildCancelled:
        # Ignore a repeated cancellation while supervising the original group.
        for sig in previous:
            signal.signal(sig, signal.SIG_IGN)
        if process is not None:
            stop_command(process)
        raise
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)
    if code:
        raise subprocess.CalledProcessError(code, list(map(str, args)))


def output(*args, cwd=None):
    return subprocess.check_output(list(map(str, args)), cwd=cwd, text=True).strip()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_aom_release_flags(cache):
    values = {}
    for line in cache.splitlines():
        if line and not line.startswith(('#', '//')) and ':' in line and '=' in line:
            key, value = line.split('=', 1)
            values[key.split(':', 1)[0]] = value
    required = ('CMAKE_BUILD_TYPE', 'CMAKE_C_FLAGS', 'CMAKE_C_FLAGS_RELEASE',
                'CMAKE_CXX_FLAGS', 'CMAKE_CXX_FLAGS_RELEASE')
    observed = {key: values.get(key, '') for key in required}
    print('AOM release flags:', json.dumps(observed, sort_keys=True), flush=True)
    valid = observed['CMAKE_BUILD_TYPE'] == 'Release'
    for language in ('C', 'CXX'):
        # AOM appends supported warning/language flags to the configuration
        # cache. Check the effective policy in compiler argument order rather
        # than rejecting those upstream additions by literal string equality.
        flags = shlex.split(observed[f'CMAKE_{language}_FLAGS'] + ' ' +
                            observed[f'CMAKE_{language}_FLAGS_RELEASE'])
        optimization = [flag for flag in flags if flag.startswith('-O')]
        debug = [flag for flag in flags if flag.startswith('-g')]
        assertions = [flag for flag in flags if flag in ('-DNDEBUG', '-UNDEBUG')
                      or flag.startswith('-DNDEBUG=')]
        valid &= (bool(optimization) and optimization[-1] == '-O3'
                  and bool(debug) and debug[-1] == '-g0'
                  and bool(assertions) and assertions[-1] == '-DNDEBUG')
    if not valid:
        raise RuntimeError('AOM overlay did not retain the required release compiler flags: ' +
                           json.dumps(observed, sort_keys=True))
    return observed


def source(work, name, url, expected=None):
    archive = work / 'sources' / (name + '.tar.gz')
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        temporary = archive.with_suffix('.download')
        urllib.request.urlretrieve(url, temporary)
        temporary.replace(archive)
    digest = sha(archive)
    if expected and digest != expected:
        raise RuntimeError(f'Source digest mismatch: {name}')
    target = work / 'deps-src' / name
    if not target.exists():
        target.mkdir(parents=True)
        with tarfile.open(archive) as bundle:
            # GitHub/VideoLAN archives have one enclosing source directory.
            members = bundle.getmembers()
            top = members[0].name.split('/')[0]
            for member in members:
                if not member.name.startswith(top + '/'):
                    continue
                member.name = member.name[len(top) + 1:]
                if member.name:
                    bundle.extract(member, target, filter='data')
    return target, {'name': name, 'url': url, 'sha256': digest, 'archive': archive.name}


def meson(work, name, src, prefix, options, env):
    build = work / ('build-' + name)
    signature = json.dumps({'source': str(src), 'prefix': str(prefix), 'options': options,
                            'compiler': env.get('CC', ''), 'pkgconfig': env.get('PKG_CONFIG_PATH', '')}, sort_keys=True)
    binding = build / 'modern-vlc-configuration.json'
    if (build / 'build.ninja').exists():
        if not binding.exists() or binding.read_text() != signature:
            old = json.loads(binding.read_text()) if binding.exists() else None
            new = json.loads(signature)
            # Undo only the recorded, insufficient Swift-disable attempt.
            # Cocoa's clipboard glue requires Swift; the source-bound optional
            # Metal guard below preserves the normal Cocoa configuration.
            permitted = (name == 'mpv' and platform.system() == 'Darwin' and old
                and {key: value for key, value in old.items() if key != 'options'} ==
                    {key: value for key, value in new.items() if key != 'options'}
                and old['options'] == new['options'] + ['-Dswift-build=disabled'])
            if not permitted:
                raise RuntimeError(f'{name}: configuration differs from retained build; use a distinct build directory')
            run('meson', 'configure', build, '-Dswift-build=auto', env=env)
            (build / 'modern-vlc-library-only-migration.json').write_text(json.dumps({
                'previous': old, 'current': new,
                'reason': 'Restore Cocoa Swift integration; guard its optional MetalLayer reference in source'}, indent=2) + '\n')
            binding.write_text(signature)
    else:
        run('meson', 'setup', build, src, '--prefix=' + str(prefix), '--libdir=lib',
            '--buildtype=release', '-Db_ndebug=true', *options, env=env)
        binding.write_text(signature)
    run('ninja', '-C', build, '-j1', env=env)
    run('ninja', '-C', build, '-j1', 'install', env=env)


def bind_source_mtimes(work):
    manifest = work / 'source-times.json'
    previous = json.loads(manifest.read_text()) if manifest.exists() else {}
    current = {}
    paths = output('git', 'ls-files', '-z', cwd=ROOT).split('\0')
    for relative in paths:
        path = ROOT / relative
        if not relative or not path.is_file():
            continue
        digest = sha(path)
        old = previous.get(relative)
        if old and old['sha256'] == digest:
            os.utime(path, ns=(path.stat().st_atime_ns, old['mtime_ns']))
        current[relative] = {'sha256': digest, 'mtime_ns': path.stat().st_mtime_ns}
    manifest.write_text(json.dumps(current, sort_keys=True))
    return previous


def prepare_mpv_cocoa_guard(source, pin):
    """Apply the exact optional-Metal source repair, preserving cached inputs."""
    applied = []
    for record in pin['patches']:
        if record['target'] != 'video/out/mac/view.swift':
            raise RuntimeError('Unexpected native MPV patch target')
        patch = ROOT / record['file']
        target = source / record['target']
        if sha(patch) != record['sha256']:
            raise RuntimeError('MPV Cocoa guard patch identity changed')
        actual = sha(target)
        if actual == record['before_sha256']:
            run('git', 'apply', '--check', patch, cwd=source)
            run('git', 'apply', patch, cwd=source)
        elif actual != record['after_sha256']:
            raise RuntimeError('Cached MPV Cocoa source has unexpected local changes')
        if sha(target) != record['after_sha256']:
            raise RuntimeError('Applied MPV Cocoa guard does not match its recorded source')
        applied.append(record)
    return applied


def bootstrap_inputs(tracked):
    return {path: sha(ROOT / path) for path in sorted(tracked)
        if path.endswith('Makefile.am') or path.startswith('m4/')
        or path in ('bootstrap', 'configure.ac') or path.startswith('autotools/')}


def retain_bootstrap_sources(work, tracked):
    generated = {'configure', 'aclocal.m4', 'config.h.in', 'po/Makefile.in.in'}
    generated.update(str(Path(path).with_name('Makefile.in')) for path in tracked if path.endswith('Makefile.am'))
    for directory in ('autotools', 'm4', 'po'):
        generated.update(str(path.relative_to(ROOT)) for path in (ROOT / directory).iterdir() if path.is_file())
    with tarfile.open(work / 'bootstrap-generated.tar', 'w') as archive:
        for relative in sorted(generated - tracked):
            path = ROOT / relative
            if path.is_file() and not path.is_symlink():
                info = archive.gettarinfo(path, arcname=relative)
                info.pax_headers['modern-vlc.mtime_ns'] = str(path.stat().st_mtime_ns)
                with path.open('rb') as stream:
                    archive.addfile(info, stream)
    # Bind the generated archive itself. source-times.json is refreshed before
    # dependency builds and may describe a later, interrupted source attempt.
    (work / 'bootstrap-inputs.json').write_text(json.dumps(bootstrap_inputs(tracked), sort_keys=True) + '\n')


def prepare_bootstrap_sources(work, build, env, previous):
    tracked = set(output('git', 'ls-files', '-z', cwd=ROOT).split('\0'))
    inputs = bootstrap_inputs(tracked)
    input_binding = work / 'bootstrap-inputs.json'
    if input_binding.exists():
        unchanged = json.loads(input_binding.read_text()) == inputs
    elif (work / 'native-build.json').exists():
        # Legacy archives predate their separate input binding. The last
        # successful native build is authoritative even when an interrupted
        # attempt has already refreshed source-times.json.
        base = json.loads((work / 'native-build.json').read_text())['source_commit']
        unchanged = not output('git', 'diff', '--name-only', base, 'HEAD', '--',
            '**/Makefile.am', 'Makefile.am', 'm4', 'bootstrap', 'configure.ac', 'autotools', cwd=ROOT)
    else:
        unchanged = all(path in previous and digest == previous[path]['sha256'] for path, digest in inputs.items())
    archive_path = work / 'bootstrap-generated.tar'
    if archive_path.exists() and unchanged:
        with tarfile.open(archive_path) as archive:
            for member in archive:
                if member.name in tracked or not member.isfile() or Path(member.name).is_absolute() or '..' in Path(member.name).parts:
                    raise RuntimeError('Invalid generated bootstrap cache member: ' + member.name)
                # The source checkout belongs to this CI job. Restore generated
                # files and their exact recorded mtimes, never tracked source.
                archive.extract(member, ROOT, filter='data')
                path = ROOT / member.name
                os.utime(path, ns=(path.stat().st_atime_ns, int(member.pax_headers['modern-vlc.mtime_ns'])))
        return tracked
    configured = (build / 'config.status').exists()
    if configured and not archive_path.exists():
        # One-time adoption of the initial native cohort, which retained all
        # objects but omitted generated source. Reconstruct only after proving
        # that every bootstrap input is identical to that cohort's source.
        if not unchanged:
            raise RuntimeError('Cannot reconstruct bootstrap files for changed native configuration inputs')
    run('sh', ROOT / 'bootstrap', cwd=ROOT, env=env)
    retain_bootstrap_sources(work, tracked)
    if configured and unchanged:
        # No configure rerun: these files were regenerated with the same inputs
        # and bound toolchain. Their original times were not retained in the
        # first cohort; use its configuration boundary once and record that
        # migration explicitly. Future runs restore the exact saved mtimes.
        reference = (build / 'config.status').stat().st_mtime_ns
        with tarfile.open(archive_path) as archive:
            members = archive.getnames()
        for relative in members:
            path = ROOT / relative
            os.utime(path, ns=(path.stat().st_atime_ns, reference))
        retain_bootstrap_sources(work, tracked)
        (work / 'bootstrap-cache-migration.json').write_text(json.dumps({
            'reason': 'initial cohort omitted generated source files',
            'inputs_unchanged': True, 'configuration_boundary_mtime_ns': reference,
            'configure_rerun': False}, indent=2) + '\n')
    return tracked


def native_make_flags(work, env):
    flags = ['PLAYER_MPV_CPPFLAGS=-DVLC_MPV_RUNTIME_IDENTITY']
    if platform.system() == 'Darwin':
        # Upstream's prebuilt ncurses .pc embeds its producer's -isysroot.
        # Keep its exact libraries, but bind the consumer link to this runner's
        # selected SDK. This is a make-time variable, not a configure rerun.
        original = subprocess.check_output(['pkg-config', '--static', '--libs', 'ncursesw'],
                                           text=True, env=env).strip()
        arguments = shlex.split(original)
        sdk = output('xcrun', '--show-sdk-path')
        rewritten = []
        index = 0
        while index < len(arguments):
            value = arguments[index]
            if value == '-isysroot':
                if index + 1 == len(arguments):
                    raise RuntimeError('Incomplete ncurses SDK binding')
                rewritten.extend([value, sdk]); index += 2
            elif value.startswith('-isysroot'):
                rewritten.append('-isysroot' + sdk); index += 1
            else:
                rewritten.append(value); index += 1
        resolved = shlex.join(rewritten)
        # This archive's libplacebo pulls glslang/SPIRV C++ objects into VLC's
        # C-linked Vulkan plugin. Its static pkg-config metadata omits libc++.
        placebo_original = subprocess.check_output(['pkg-config', '--static', '--libs', 'libplacebo'],
                                                  text=True, env=env).strip()
        placebo_arguments = shlex.split(placebo_original)
        if '-lc++' not in placebo_arguments:
            placebo_arguments.append('-lc++')
        placebo_resolved = shlex.join(placebo_arguments)
        (work / 'native-link-bindings.json').write_text(json.dumps({
            'ncurses_pkgconfig_libs': original, 'ncurses_consumer_libs': resolved,
            'selected_sdk': sdk, 'reason': 'prebuilt producer SDK path is not a consumer toolchain',
            'libplacebo_static_pkgconfig_libs': placebo_original,
            'libplacebo_consumer_libs': placebo_resolved,
            'libplacebo_reason': 'C-linked plugin consumes glslang/SPIRV C++ archive objects'}, indent=2) + '\n')
        flags.append('NCURSES_LIBS=' + resolved)
        flags.append('LIBPLACEBO_LIBS=' + placebo_resolved)
    return flags


def retire_prior_package_generations(work):
    """Bound this hosted native cache after a replacement package is complete.

    This is the native CI cache's lifecycle policy, never host Windows cleanup.
    Compiler trees, SDKs, source downloads and the current package stay retained.
    """
    if os.environ.get('GITHUB_ACTIONS') != 'true' or platform.system() not in ('Darwin', 'Linux'):
        return
    if (Path(os.environ['GITHUB_WORKSPACE']).resolve() != ROOT.resolve()
            or work.resolve() != (ROOT / '.desktop-build').resolve()):
        raise RuntimeError('Native cache retirement requires its exact hosted build root')
    current = json.loads((work / 'package-output.json').read_text())
    generation = current['source_commit']
    directory = work / 'packages' / generation
    if Path(current['directory']).resolve() != directory.resolve():
        raise RuntimeError('Current native package escaped its generation')
    status = json.loads((directory / 'PACKAGE-STATUS.json').read_text())
    if status['source_commit'] != generation or not status['assets']:
        raise RuntimeError('Replacement package is incomplete; preserve recovery generations')
    for row in status['assets']:
        asset = directory / row['name']
        if asset.parent != directory or sha(asset) != row['sha256']:
            raise RuntimeError('Replacement package changed; preserve recovery generations')
    targets = []
    for name in ('packages', 'plugin-deployment', 'qml-deployment'):
        parent = work / name
        if not parent.is_dir():
            continue
        for candidate in sorted(parent.iterdir()):
            if candidate.name == generation or not re.fullmatch('[0-9a-f]{40}', candidate.name):
                continue
            if candidate.is_symlink() or candidate.resolve().parent != parent.resolve():
                raise RuntimeError('Native generation retirement found a redirected target')
            if not candidate.is_dir():
                continue
            ancestry = subprocess.run(['git', 'merge-base', '--is-ancestor', candidate.name, generation], cwd=ROOT)
            if ancestry.returncode == 1:
                continue
            if ancestry.returncode:
                raise RuntimeError('Cannot establish generated package ancestry')
            targets.append(candidate)
    # The original contrib fetch now uses RUNNER_TEMP. Its old extracted work
    # trees are reproducible from recipes.tar.gz and cached original tarballs.
    if platform.system() == 'Darwin':
        pin = json.loads((ROOT / 'tools/desktop-player/native-inputs.json').read_text())['macos_contrib_commit']
        original = work / 'corresponding-contrib' / pin
        for name in ('source', 'selection'):
            candidate = original / name
            if candidate.exists():
                if candidate.is_symlink() or candidate.resolve().parent != original.resolve():
                    raise RuntimeError('Original contrib recovery tree was redirected')
                targets.append(candidate)
    receipt = {'source_commit': generation, 'state': 'retiring',
               'targets': [path.relative_to(work).as_posix() for path in targets], 'retired': []}
    record = work / 'generation-retention.json'
    record.write_text(json.dumps(receipt, indent=2) + '\n')
    for target in targets:
        shutil.rmtree(target)
        receipt['retired'].append(target.relative_to(work).as_posix())
        record.write_text(json.dumps(receipt, indent=2) + '\n')
    receipt['state'] = 'complete'
    record.write_text(json.dumps(receipt, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    native_mac = platform.system() == 'Darwin'
    arch = platform.machine()
    if arch not in ('arm64', 'aarch64', 'x86_64'):
        raise RuntimeError('Unqualified native architecture: ' + arch)
    previous_source = bind_source_mtimes(work)
    toolchain_file = ROOT / '.desktop-toolchain/binding.json'
    if toolchain_file.exists():
        toolchain = toolchain_file.read_bytes()
        retained = work / 'toolchain-binding.json'
        if retained.exists() and retained.read_bytes() != toolchain:
            raise RuntimeError('The retained native build belongs to another installed toolchain')
        if not retained.exists() and (work / 'build-mpv').exists():
            # One-time migration of the first diagnostic run, whose objects
            # were saved before the separate normalized toolchain binding.
            actual = json.loads(toolchain)
            if native_mac:
                old = json.loads((work / 'brew-packages.json').read_text())
                packages = sorted([formula['full_name'], installed['version'], installed.get('built_as_bottle')]
                    for formula in old['formulae'] for installed in formula['installed'])
            else:
                packages = sorted((work / 'dpkg-packages.tsv').read_text().splitlines())
            if packages != actual['packages']:
                raise RuntimeError('Legacy native cache package identities differ from this runner')
            compilers = json.loads((work / 'build-mpv/meson-info/intro-compilers.json').read_text())
            if compilers['host']['c']['full_version'].splitlines()[0] != actual['compiler']:
                raise RuntimeError('Legacy native cache compiler differs from this runner')
        retained.write_bytes(toolchain)
    env = os.environ.copy()
    env.update(CFLAGS='-O3 -g0 -DNDEBUG', CXXFLAGS='-O3 -g0 -DNDEBUG',
               MAKEFLAGS='-j1', CMAKE_BUILD_PARALLEL_LEVEL='1', PYTHONDONTWRITEBYTECODE='1')
    prefix = work / 'deps'
    sources = []
    if native_mac:
        brew = output('brew', '--prefix')
        qt = output('brew', '--prefix', 'qt')
        env['PATH'] = ':'.join([qt + '/bin', brew + '/opt/gettext/bin', brew + '/opt/bison/bin', env['PATH']])
        env['PKG_CONFIG_PATH'] = ':'.join([str(prefix / 'lib/pkgconfig'), qt + '/lib/pkgconfig',
            brew + '/opt/ffmpeg/lib/pkgconfig', brew + '/opt/libarchive/lib/pkgconfig',
            brew + '/lib/pkgconfig'])
        env['MACOSX_DEPLOYMENT_TARGET'] = '13.0'
    else:
        env['PATH'] = '/usr/lib/qt6/bin:' + env['PATH']
        env['PKG_CONFIG_PATH'] = str(prefix / 'lib/pkgconfig')
    # Stock MPV 0.42 requires >=7.387. Ubuntu and the Intel hosted image
    # currently provide older versions; preserve a matching native installation
    # when it already satisfies the exact source pin, otherwise build the pin.
    placebo_pin = json.loads((ROOT / 'tools/desktop-player/native-inputs.json').read_text())['stock_libplacebo']
    placebo_version = subprocess.run(['pkg-config', '--modversion', 'libplacebo'], env=env,
        text=True, capture_output=True)
    if placebo_version.returncode or placebo_version.stdout.strip() != placebo_pin['version']:
        placebo, record = source(work, 'libplacebo-' + placebo_pin['commit'],
            'https://codeload.github.com/haasn/libplacebo/tar.gz/' + placebo_pin['commit'])
        sources.append(record)
        for pin in placebo_pin['submodules']:
            submodule, subrecord = source(work, pin['path'] + '-' + pin['commit'],
                'https://codeload.github.com/' + pin['repository'] + '/tar.gz/' + pin['commit'])
            sources.append(subrecord)
            destination = placebo / '3rdparty' / pin['path']
            for path in submodule.rglob('*'):
                target = destination / path.relative_to(submodule)
                if path.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                elif path.is_file() and (not target.exists() or sha(target) != sha(path)):
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)
        meson(work, 'placebo-' + placebo_pin['version'], placebo, prefix, ['-Ddemos=false', '-Dtests=false',
            '-Dopengl=enabled', '-Dvulkan=disabled', '-Dshaderc=disabled', '-Dglslang=disabled'], env)

    pin = json.loads((ROOT / 'modules/gui/qt/player/mpv/source-portable.json').read_text())
    mpv, record = source(work, 'mpv-' + pin['commit'],
        'https://codeload.github.com/mpv-player/mpv/tar.gz/' + pin['commit'])
    if native_mac:
        record['patches'] = prepare_mpv_cocoa_guard(mpv, pin)
    sources.append(record)
    mpv_options = ['-Dlibmpv=true', '-Dcplayer=false', '-Dbuild-date=false',
        '-Dplain-gl=enabled', '-Dmanpage-build=disabled', '-Dhtml-build=disabled', '-Dtests=false']
    meson(work, 'mpv', mpv, prefix, mpv_options, env)

    # VLC's required medialibrary ABI is newer than Ubuntu's packaged ABI.
    if not native_mac:  # macOS's full upstream contrib already contains this ABI.
        medialibrary_url = ('https://code.videolan.org/videolan/medialibrary/-/archive/0.14.1/'
                            'medialibrary-0.14.1.tar.bz2')
        medialibrary, record = source(work, 'medialibrary-0.14.1', medialibrary_url)
        # splitPath() in this pinned ABI stops at a repeated first-folder name,
        # e.g. /home/runner/work/home/... becomes /home/.... Preserve the full
        # root ancestry, and bind both the patch and retained source bytes.
        path_patch = ROOT / 'tools/desktop-player/patches/medialibrary-full-root.patch'
        patch_sha = '8945fa0efb6ac25cb178609cbb57f0f82b3f2fa600677f1448d9c5b2424c4e0c'
        original_sha = '6b3adac32c933d838a67d8dcd8aba456ef038472182b5ce1b8e71e95db4abd4b'
        patched_sha = '0d4c54031b80faa6824d118a7809e05b6b8faf5efe3192824d345c76374713e0'
        filename = medialibrary / 'src/utils/Filename.cpp'
        if sha(path_patch) != patch_sha or sha(filename) not in (original_sha, patched_sha):
            raise RuntimeError('Pinned medialibrary path repair input changed')
        if sha(filename) == original_sha:
            # The extracted dependency is inside an ignored directory of the
            # VLC checkout. git apply would interpret its paths relative to
            # that enclosing repository and silently skip this source file.
            run('patch', '--dry-run', '--batch', '--forward', '-p1', '-i', path_patch, cwd=medialibrary)
            run('patch', '--batch', '--forward', '-p1', '-i', path_patch, cwd=medialibrary)
        if sha(filename) != patched_sha:
            raise RuntimeError('Pinned medialibrary path repair did not apply exactly')
        record['patches'] = [{'file': path_patch.relative_to(ROOT).as_posix(), 'sha256': patch_sha,
                              'original_file_sha256': original_sha, 'patched_file_sha256': patched_sha}]
        sources.append(record)
        meson(work, 'medialibrary', medialibrary, prefix, ['-Dlibvlc=disabled', '-Dlibtool_workaround=true'], env)

    build = work / 'vlc-build'
    build.mkdir(exist_ok=True)
    install = work / 'installed'
    # The runtime dependency closure is staged before compiling its immutable
    # identities into the Qt plugin; packaging must preserve these exact bytes.
    run('python3', ROOT / 'tools/desktop-player/package-native.py', 'stage-mpv',
        '--work', work, '--prefix', prefix)
    flags = ['--prefix=' + str(install), '--enable-qt', '--disable-debug',
             '--disable-skins2', '--disable-nls', '--enable-libass', '--disable-merge-ffmpeg']
    if native_mac:
        # Reuse upstream's full native codec graph. Qt comes from the native
        # toolchain; the stock MPV graph above remains separate from these VLC
        # contribs (whose libplacebo ABI is older).
        triplet = ('aarch64' if arch == 'arm64' else arch) + '-apple-darwin19'
        inputs = json.loads((ROOT / 'tools/desktop-player/native-inputs.json').read_text())
        contrib_sha = inputs['macos_contrib_commit']
        changed = set(output('git', 'diff', '--name-only', contrib_sha, 'HEAD', '--',
            'extras/tools', 'contrib', 'extras/ci', 'extras/package/macosx', cwd=ROOT).splitlines())
        reviewed = inputs.get('reviewed_prebuilt_recipe_delta', {})
        accepted = set(inputs['windows_only_contrib_delta']) | set(reviewed)
        if not changed <= accepted or any(sha(ROOT / path) != digest for path, digest in reviewed.items()):
            raise RuntimeError('Native contrib inputs changed; bind the new native dependency build before reusing its archive')
        archive = work / 'sources' / ('vlc-contrib-' + triplet + '-' + contrib_sha + '.tar.zst')
        url = 'https://artifacts.videolan.org/vlc/macos-' + ('arm64' if arch == 'arm64' else 'x86_64') + '/' + archive.name
        contrib_root = work / 'native-contrib'
        contrib = contrib_root / triplet
        if not archive.exists():
            urllib.request.urlretrieve(url, archive)
        if not contrib.exists():
            contrib_root.mkdir(exist_ok=True)
            run('tar', '-xf', archive, '-C', contrib_root)
            run('sh', ROOT / 'contrib/src/change_prefix.sh', cwd=contrib, env=env)
        sources.append({'name': 'vlc-native-contrib', 'upstream_input_commit': contrib_sha,
                        'url': url, 'archive': archive.name, 'sha256': sha(archive)})
        # Update only the dependency changed by this upstream integration.
        # Preserve the full pinned SDK, compiler objects and unrelated codecs.
        overlay = inputs.get('native_contrib_aom_overlay')
        if overlay:
            overlay_work = work / 'native-contrib-overlays' / ('aom-' + overlay['version'])
            overlay_work.mkdir(parents=True, exist_ok=True)
            if not (overlay_work / 'Makefile').exists():
                run('sh', ROOT / 'contrib/bootstrap', '--build=' + triplet,
                    '--host=' + triplet, '--prefix=' + str(contrib), '--disable-all',
                    '--enable-aom', cwd=overlay_work, env=env)
            # contrib defaults to RelWithDebInfo, whose per-configuration
            # flags override CFLAGS. Append the release policy after loading
            # upstream's recipe, preserving all of its architecture options.
            release_makefile = overlay_work / 'overlay-release.mk'
            release_rules = ('include Makefile\n'
                'AOM_CONF += -DCMAKE_BUILD_TYPE=Release '
                '-DCMAKE_C_FLAGS_RELEASE="-O3 -g0 -DNDEBUG" '
                '-DCMAKE_CXX_FLAGS_RELEASE="-O3 -g0 -DNDEBUG"\n'
                '.aom: overlay-release.mk\n')
            if not release_makefile.exists() or release_makefile.read_text() != release_rules:
                release_makefile.write_text(release_rules)
            run('make', '-f', release_makefile.name, '-j1', '.aom',
                'TARBALLS=' + str(work / 'sources'), cwd=overlay_work, env=env)
            cache = (overlay_work / 'aom/vlc_build/CMakeCache.txt').read_text()
            verify_aom_release_flags(cache)
            source_archive = work / 'sources' / ('libaom-' + overlay['version'] + '.tar.gz')
            sources.append({'name': 'native-contrib-aom-overlay', 'version': overlay['version'],
                            'upstream_input_commit': overlay['upstream_commit'],
                            'url': overlay['url'], 'archive': source_archive.name,
                            'sha256': sha(source_archive)})
        import image_dependencies
        image_work = work / 'native-contrib-overlays/images'
        run('python3', ROOT / 'tools/desktop-player/image_dependencies.py',
            '--repo', ROOT, '--work', image_work, '--prefix', contrib,
            '--archives', work / 'sources', env=env)
        images = json.loads((image_work / 'build-receipt.json').read_text())
        for item in images['libraries']:
            sources.append({'name': 'native-contrib-' + item['name'] + '-overlay',
                'version': item['version'], 'url': item['url'], 'archive': item['archive'],
                'sha256': item['archive_sha256']})
        # Prebuilt target libraries omit the native generators. Use upstream's
        # matching recipes (including Lua's 64-bit bytecode patch), rather than
        # a system luac/protoc that can generate incompatible serialized data.
        native_tools = work / 'native-contrib-tools'
        native_tools.mkdir(exist_ok=True)
        if not (native_tools / 'Makefile').exists():
            run('sh', ROOT / 'contrib/bootstrap', '--build=' + triplet,
                '--host=' + triplet, '--prefix=' + str(contrib), '--disable-all',
                '--enable-luac', '--enable-protoc', cwd=native_tools, env=env)
        run('make', '-j1', '.luac', '.protoc', 'TARBALLS=' + str(work / 'sources'),
            'BUILDCFLAGS=-O3 -g0 -DNDEBUG', cwd=native_tools, env=env)
        env['LUAC'] = str(contrib.parent / 'bin' / (triplet + '-luac'))
        env['PROTOC'] = str(contrib.parent / 'bin/protoc')
        env['PATH'] = str(contrib.parent / 'bin') + ':' + env['PATH']
        env['PKG_CONFIG_PATH'] = str(contrib / 'lib/pkgconfig') + ':' + env['PKG_CONFIG_PATH']
        flags += ['--with-contrib=' + str(contrib)]
        flags += ['--disable-macosx', '--disable-xcb', '--without-x', '--with-macosx-version-min=13.0']
    else:
        flags += ['--enable-xcb', '--disable-wayland']
    # Preserve configure and generated objects when relevant inputs are equal.
    config = json.dumps({'flags': flags, 'environment': {k: env.get(k) for k in
        ('CFLAGS', 'CXXFLAGS', 'PKG_CONFIG_PATH', 'MACOSX_DEPLOYMENT_TARGET', 'LUAC', 'PROTOC')},
        'configure_inputs': {str(p.relative_to(ROOT)): sha(p) for p in
            [ROOT / 'configure.ac', ROOT / 'modules/gui/qt/qt6.pro']}}, sort_keys=True)
    binding = build / 'native-config.json'
    tracked_sources = prepare_bootstrap_sources(work, build, env, previous_source)
    if (build / 'config.status').exists():
        if not binding.exists():
            raise RuntimeError('Retained VLC configuration has no source binding')
        if binding.read_text() != config:
            old = json.loads(binding.read_text())
            current = json.loads(config)
            if any(old[key] != current[key] for key in ('flags', 'environment')):
                raise RuntimeError('Retained native compiler configuration changed; use a distinct cohort')
            # Upstream configure inputs changed, while toolchain/flags/paths
            # remain identical. Reconfigure in place and let make rebuild the
            # affected dependency graph, retaining all reusable SDK objects.
            run(ROOT / 'configure', *flags, cwd=build, env=env)
            (work / 'native-reconfiguration.json').write_text(json.dumps({
                'old': old, 'new': current, 'preserved_dependency_objects': True}, indent=2) + '\n')
            binding.write_text(config)
    else:
        run(ROOT / 'configure', *flags, cwd=build, env=env)
        binding.write_text(config)
    try:
        make_flags = native_make_flags(work, env)
        if native_mac:
            image_rules = image_dependencies.mac_link_rules(image_work, contrib)
            env['MAKEFILES'] = str(image_rules)
        run('make', '-j1', *make_flags, cwd=build, env=env)
        image_links = image_dependencies.verify_mac_links(image_work, build) if native_mac else None
        run('make', '-j1', 'test_input_clock', *make_flags, cwd=build / 'src', env=env)
        run(build / 'src/test_input_clock', cwd=build, env=env)
        run('make', '-j1', 'install', *make_flags, cwd=build, env=env)
    finally:
        retain_bootstrap_sources(work, tracked_sources)
    (work / 'native-build.json').write_text(json.dumps({
        'schema': 'modern-vlc.native-build.v1', 'source_commit': output('git', 'rev-parse', 'HEAD', cwd=ROOT),
        'platform': platform.platform(), 'architecture': arch, 'mpv': pin,
        'sources': sources, 'configuration': json.loads(config),
        'image_dependencies': image_links,
        'qualification': 'NOT RUN; build/packaging is not playback acceptance'}, indent=2) + '\n')
    run('python3', ROOT / 'tools/desktop-player/package-native.py', 'packages', '--work', work, '--prefix', prefix)
    retire_prior_package_generations(work)


if __name__ == '__main__':
    try:
        main()
    except NativeBuildCancelled as error:
        raise SystemExit(128 + error.signum)

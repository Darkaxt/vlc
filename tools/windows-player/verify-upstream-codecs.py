"""Decode real synthetic fixtures with the newly linked native codec plugins."""
import argparse
import array
import hashlib
import json
import os
from pathlib import Path
import shutil
import wave
from isolated_desktop import IsolatedProcess


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    args = parser.parse_args()
    assert args.scratch.parent == Path('D:/Temp/vlc-s8-release-1.1.1-20261031')
    assert not args.scratch.exists()
    args.scratch.mkdir()
    runtime = args.scratch / 'runtime'
    shutil.copytree(args.runtime, runtime)
    assert not any((runtime / 'portable').iterdir())
    (args.scratch / 'tmp').mkdir()
    linkage = json.loads((runtime / 'VLC-CODEC-BUILDINFO.json').read_text())
    fixtures = json.loads((args.fixtures / 'fixtures.json').read_text())
    for item in fixtures['fixtures']:
        assert sha(args.fixtures / item['file']) == item['sha256']
    env = {key: value for key, value in os.environ.items() if not key.startswith('VLC_PLAYER_DIAGNOSTICS')}
    env.pop('VLC_PLUGIN_PATH', None)
    env.update(TEMP=str(args.scratch / 'tmp'), TMP=str(args.scratch / 'tmp'),
        VLC_USERDATA_PATH=str(runtime / 'portable'), VLC_DATA_PATH=str(runtime))
    cases = []
    progress = {'schema': 'vlc_redesign.upstream_codec_native.v1', 'cases': cases, 'passed': False}
    (args.scratch / 'result.json').write_text(json.dumps(progress, indent=2) + '\n')
    for codec in ('mpg123', 'mad', 'aom'):
        case = args.scratch / codec
        case.mkdir()
        audio = codec != 'aom'
        fixture = args.fixtures / ('sine.mp3' if audio else 'testsrc-av1.ivf')
        output = case / ('decoded.wav' if audio else 'decoded.yuv')
        command = [str(runtime / 'vlc.exe'), '--ignore-config', '--intf=dummy', '--no-one-instance',
            '--no-media-library', '--no-save-recentplay', '--no-metadata-network-access', '--no-plugins-cache',
            '--play-and-exit', '--file-logging', '--log-verbose=2', '--logfile=' + str(case / 'native.log'),
            '--codec=' + codec + ',none']
        if audio:
            command += ['--no-video', '--aout=afile', '--audiofile-format=s16', '--audiofile-wav', '--audiofile-file=' + str(output)]
        else:
            command += ['--no-audio', '--vout=yuv', '--yuv-chroma=I420', '--no-yuv-yuv4mpeg2', '--yuv-file=' + str(output)]
        command.append(str(fixture))
        (case / 'launch-argv.json').write_text(json.dumps(command, indent=2) + '\n')
        with (case / 'stdout').open('wb') as stdout, (case / 'stderr').open('wb') as stderr:
            process = IsolatedProcess(command, cwd=runtime, env=env, stdout=stdout, stderr=stderr)
            code = process.wait()
        result = {'codec': codec, 'exit_code': code, 'input_desktop_preserved': True,
            'fixture_sha256': sha(fixture), 'plugin_sha256': sha(next((runtime / 'plugins').rglob('lib' + codec + '_plugin.dll')))}
        (args.scratch / 'result.json').write_text(json.dumps(dict(progress, cases=cases + [dict(result, passed=False)]), indent=2) + '\n')
        log = (case / 'native.log').read_text(encoding='utf-8', errors='replace')
        assert code == 0 and 'EOF reached' in log, (codec, code)
        assert ('using ' + ('audio' if audio else 'video') + ' decoder module "' + codec + '"') in log, codec
        assert 'cannot load plug-in' not in log
        if audio:
            with wave.open(str(output), 'rb') as stream:
                assert stream.getsampwidth() == 2
                pcm = array.array('h', stream.readframes(stream.getnframes()))
                result.update(sample_frames=stream.getnframes(), sample_rate=stream.getframerate(),
                    pcm_peak=max(map(abs, pcm)))
                assert stream.getnframes() >= 3 * stream.getframerate() and result['pcm_peak'] > 0
        else:
            data = output.read_bytes()
            size = 160 * 96 * 3 // 2
            # VLC's yuv output always writes a format line and FRAME markers,
            # including when the optional YUV4MPEG2 identifier is disabled.
            header, separator, body = data.partition(b'\n')
            assert separator and header.startswith(b'I420 W160 H96 ')
            stride = len(b'FRAME\n') + size
            assert len(body) % stride == 0
            hashes = set()
            for offset in range(0, len(body), stride):
                assert body[offset:offset + 6] == b'FRAME\n'
                hashes.add(hashlib.sha256(body[offset + 6:offset + stride]).hexdigest())
            result.update(decoded_frames=len(body) // stride, different_frames=len(hashes))
            assert result['decoded_frames'] >= 24 and len(hashes) >= 20
        result.update(decoded_output_sha256=sha(output), passed=True)
        cases.append(result)
        (args.scratch / 'result.json').write_text(json.dumps(progress, indent=2) + '\n')
    result = {'schema': 'vlc_redesign.upstream_codec_native.v1', 'cases': cases,
        'linkage_sha256': sha(runtime / 'VLC-CODEC-BUILDINFO.json'), 'passed': True,
        'zvbi_scope': 'Verified upstream patched source and actual new archive linkage; no teletext sample decode claimed'}
    assert {item['library'] for item in linkage['libraries']} == {'mpg123', 'mad', 'aom', 'zvbi'}
    (args.scratch / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()

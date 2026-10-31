"""Create an owned, color-converted HDR10 fixture for S8 native acceptance.

Uses the installed media helper and an existing locally authored SDR fixture.
The PQ/BT.2020 conversion changes pixel values; this is not metadata retagging.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    source, output = options.input.resolve(), options.output.resolve()
    assert source.is_file() and source.is_relative_to(Path('D:/Temp'))
    assert output.is_relative_to(Path('D:/Temp')) and not output.exists()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.parent / 'tmp'
    temporary.mkdir(exist_ok=True)
    os.environ['TEMP'] = os.environ['TMP'] = str(temporary)
    wrapper = Path.home() / '.codex/skills/yt-dlp-ffmpeg/scripts/invoke_media_tool.py'
    spec = importlib.util.spec_from_file_location('installed_media_wrapper', wrapper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from agent_toolbelt_media import media

    arguments = [
        '-hide_banner', '-loglevel', 'error', '-t', '24',
        '-map', '0:v:0', '-map', '0:a:0?', '-sn',
        '-vf', 'zscale=matrixin=709:transferin=709:primariesin=709:rangein=limited:'
               'matrix=2020_ncl:transfer=smpte2084:primaries=2020:range=limited:npl=100,'
               'format=yuv420p10le',
        '-c:v', 'libx265', '-preset', 'ultrafast', '-crf', '20', '-threads', '1',
        '-x265-params', 'pools=none:frame-threads=1:wpp=0:hdr10=1:'
            'colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc:'
            'master-display=G(8500,39850)B(6550,2300)R(35400,14600)WP(15635,16450)L(10000000,1):'
            'max-cll=100,100',
        '-color_primaries', 'bt2020', '-color_trc', 'smpte2084',
        '-colorspace', 'bt2020nc', '-color_range', 'tv',
        '-c:a', 'copy', '-movflags', '+faststart',
    ]
    transcode = media.invoke_transcode(input_path=str(source), output_path=str(output),
                                     ffmpeg_args=arguments, timeout_sec=None)
    report = {'schema': 'vlc_redesign.hdr10_fixture.v1',
              'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'license': 'CC0-1.0 locally authored testsrc2/sine fixture',
              'conversion': arguments, 'media_helper': str(wrapper), 'transcode': transcode}
    if transcode.get('ok'):
        probe = media.run_process([media.resolve_binary('ffprobe'), '-v', 'error',
            '-print_format', 'json', '-show_streams', '-show_format', str(output)], timeout_sec=None)
        assert probe.returncode == 0, probe.stderr
        report['probe'] = json.loads(probe.stdout)
        video = next(stream for stream in report['probe']['streams'] if stream['codec_type'] == 'video')
        assert video['codec_name'] == 'hevc' and video['pix_fmt'] == 'yuv420p10le', video
        assert video['color_transfer'] == 'smpte2084' and video['color_primaries'] == 'bt2020', video
        assert video['color_space'] == 'bt2020nc' and video['color_range'] == 'tv', video
        side_data = video.get('side_data_list', [])
        assert not any('DOVI' in item.get('side_data_type', '') for item in side_data), side_data
        report['output_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
        report['output_bytes'] = output.stat().st_size
    output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    assert transcode.get('ok'), transcode
    print(json.dumps({'fixture': str(output), 'sha256': report['output_sha256'],
                      'format': 'HEVC Main10, BT.2020/PQ, no Dolby Vision RPU',
                      'player_acceptance': False}))


if __name__ == '__main__':
    main()

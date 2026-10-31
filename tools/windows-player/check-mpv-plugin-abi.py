"""Require an additive public ABI before retaining the verified 1.0 plugins.

S8 adds a stopped-player release entry point, a locked external-playback reservation
and exposure of native playlist expansion.
Existing public headers,
callback layouts, enums and exported names must remain identical to 1.0.
"""
import argparse
from pathlib import Path
import subprocess

BASE = 'dd61caec26f8cc65f15d78369d09fb254196c810'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)

    def original(name):
        return subprocess.check_output(['git', '-C', str(source), 'show', BASE + ':' + name]).decode().replace('\r\n', '\n')

    header = (source / 'include/vlc_player.h').read_text(encoding='utf-8')
    start = '\n/**\n * Reserve this player for an external playback engine.\n'
    end = 'vlc_player_SetExternalPlayback(vlc_player_t *player, bool enabled);\n'
    assert header.count(start) == 1 and header.count(end) == 1
    first = header.index(start)
    last = header.index(end, first) + len(end)
    addition = header[first:last]
    assert addition.count('VLC_API void\nvlc_player_SetExternalPlayback(') == 1
    assert addition.count('{') == 0 and addition.count(';') == 1
    header = header[:first] + header[last:]
    start = '\n/**\n * Release cached video resources after stopping the player.\n'
    end = '                             void *opaque);\n'
    assert header.count(start) == 1 and header.count(end) == 1
    first = header.index(start)
    last = header.index(end, first) + len(end)
    addition = header[first:last]
    assert addition.count('VLC_API int\nvlc_player_vout_ReleaseUnused(') == 1
    assert addition.count('{') == 0 and addition.count(';') == 1
    assert header[:first] + header[last:] == original('include/vlc_player.h'), 'Existing public player ABI changed'
    playlist = (source / 'include/vlc_playlist.h').read_text(encoding='utf-8')
    start = '\n/**\n * Expand a container using the native playlist\'s item replacement semantics.\n'
    end = '                    input_item_t *const media[], size_t count);\n'
    assert playlist.count(start) == 1
    first = playlist.index(start)
    last = playlist.index(end, first) + len(end)
    addition = playlist[first:last]
    assert addition.count('VLC_API int\nvlc_playlist_Expand(') == 1
    assert addition.count('{') == 0 and addition.count(';') == 1
    assert playlist[:first] + playlist[last:] == original('include/vlc_playlist.h'), 'Existing public playlist ABI changed'
    exports = (source / 'src/libvlccore.sym').read_text(encoding='utf-8')
    for export in ('vlc_player_vout_ReleaseUnused\n', 'vlc_player_SetExternalPlayback\n', 'vlc_playlist_Expand\n'):
        assert exports.count(export) == 1
        exports = exports.replace(export, '', 1)
    assert exports == original('src/libvlccore.sym'), 'Existing exports changed'
    subprocess.run(['git', '-C', str(source), 'diff', '--exit-code', BASE, '--',
        'include', ':!include/vlc_player.h', ':!include/vlc_playlist.h', 'modules/audio_output', 'modules/text_renderer',
        'modules/audio_filter', 'modules/misc', 'modules/stream_out', 'modules/services_discovery',
        'modules/gui/skins2', 'share', 'contrib'], check=True)
    print('Existing public headers, callback layouts, exports and retained-plugin sources match 1.0; three additive entry points.')


if __name__ == '__main__':
    main()

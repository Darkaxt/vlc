"""Generate redistributable synthetic media for the complete S7 native matrix."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    options = parser.parse_args()
    root = options.output.resolve()
    if root.drive.upper() != 'D:' or 'Temp' not in root.parts:
        parser.error('Use the registered D:/Temp stage scratch')
    if root.exists():
        parser.error('Fixture destination already exists; inspect existing evidence before regeneration')
    root.mkdir(parents=True)
    (root / 'tmp').mkdir()
    environment = dict(os.environ, TEMP=str(root/'tmp'), TMP=str(root/'tmp'))

    def ffmpeg(name, arguments):
        with (root/(name+'.log')).open('wb') as log:
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error', *arguments],
                env=environment,stdout=log,stderr=log,check=True,creationflags=subprocess.CREATE_NO_WINDOW)

    subtitles = root/'captions.en.srt'
    subtitles.write_text('1\n00:00:00,000 --> 00:00:30,000\nS7 synthetic subtitle - first cue\n\n2\n00:00:30,000 --> 00:01:00,000\nSecond cue: Greek Ω and Japanese 日本語\n\n3\n00:01:00,000 --> 00:02:00,000\nFinal cue after a real seek\n',encoding='utf-8')
    chapters = root/'chapters.ffmeta'
    chapters.write_text(';FFMETADATA1\ntitle=S7 synthetic multi-track Ω 日本語\n[CHAPTER]\nTIMEBASE=1/1000\nSTART=0\nEND=60000\ntitle=First chapter\n[CHAPTER]\nTIMEBASE=1/1000\nSTART=60000\nEND=120000\ntitle=Second chapter\n',encoding='utf-8')
    video = root/'Multi-track Ω 日本語.mp4'
    ffmpeg('multi-track', ['-f','lavfi','-i','testsrc2=size=320x180:rate=12',
        '-f','lavfi','-i','sine=frequency=440:sample_rate=48000',
        '-f','lavfi','-i','sine=frequency=880:sample_rate=48000',
        '-i',str(subtitles),'-f','ffmetadata','-i',str(chapters),
        '-map','0:v','-map','1:a','-map','2:a','-map','3:s','-map_metadata','4','-map_chapters','4',
        '-t','120','-c:v','libx264','-preset','ultrafast','-crf','25','-pix_fmt','yuv420p',
        '-c:a','aac','-b:a','64k','-c:s','mov_text','-metadata:s:a:0','language=eng',
        '-metadata:s:a:1','language=spa','-metadata:s:s:0','language=eng',
        '-threads','1','-movflags','+faststart',str(video)])
    first,second = root/'clip-a.mp4',root/'clip-b.mp4'
    ffmpeg('clip-a',['-i',str(video),'-t','8','-map','0:v','-map','0:a:0','-c','copy',str(first)])
    ffmpeg('clip-b',['-ss','60','-i',str(video),'-t','8','-map','0:v','-map','0:a:1','-c','copy',str(second)])
    ffmpeg('transport',['-i',str(first),'-map','0:v','-map','0:a','-c','copy','-f','mpegts',str(root/'stream.ts')])
    ffmpeg('audio',['-f','lavfi','-i','sine=frequency=660:sample_rate=48000','-t','8','-c:a','pcm_s16le',str(root/'audio.wav')])
    (root/'local-playlist.m3u8').write_text('#EXTM3U\n'+first.as_uri()+'\n'+second.as_uri()+'\n',encoding='utf-8')
    records = []
    for path in sorted(root.iterdir()):
        if path.is_file() and path.suffix != '.log':
            with path.open('rb') as source:
                records.append({'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.file_digest(source,'sha256').hexdigest()})
    (root/'fixture-manifest.json').write_text(json.dumps({'source':'FFmpeg lavfi testsrc2 and sine; locally authored text/chapter metadata','user_media_read':False,'license':'CC0-1.0 for these generated validation fixtures','files':records},indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
    print(json.dumps({'fixtures_generated':True,'output':str(root),'multi_track':str(video),'files':len(records)}),flush=True)


if __name__ == '__main__':
    main()

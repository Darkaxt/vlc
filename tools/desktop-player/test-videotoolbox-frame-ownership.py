"""Exercise the actual VT submission fragment when its callback retires metadata.

No Apple framework is invoked. The mock callback reuses its frame metadata before
DecodeFrame returns, a permitted synchronous completion of an asynchronous request.
"""
import argparse
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', required=True, type=Path)
    parser.add_argument('--compiler', default='cc')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    text = (root / 'modules/codec/videotoolbox/decoder.c').read_text()
    start = text.index('    CMSampleBufferRef sampleBuffer =', text.index('static int DecodeBlock'))
    stop = text.index('    CFRelease(sampleBuffer);', start) + len('    CFRelease(sampleBuffer);')
    fragment = text[start:stop]
    prefix = r'''
#include <stdbool.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdlib.h>
#include <stdio.h>
typedef struct { bool b_field; int64_t pts; } frame_info_t;
typedef int CMSampleBufferRef;
typedef int VTDecodeInfoFlags;
typedef int VTDecodeFrameFlags;
typedef int OSStatus;
typedef int64_t vlc_tick_t;
enum vtsession_status { VTSESSION_STATUS_OK };
typedef struct { int session, videoFormatDescription, pic_pacer, decoder_state;
    int sync_state, start_sync_state, lock; enum vtsession_status vtsession_status; } decoder_sys_t;
typedef struct { int i_flags; } block_t;
enum { kVTDecodeFrame_EnableAsynchronousDecompression=1,
    VLC_SUCCESS=0, STATE_DECODER_STARTED=1, BLOCK_FLAG_END_OF_SEQUENCE=1 };
static int scheduled;
static int64_t logged_pts;
static int rejected;
#define unlikely(x) (x)
#define VTSampleBufferCreate(...) 1
#define pic_pacer_WaitAllocatableSlot(...) ((void)0)
#define pic_pacer_AccountScheduledDecode(pacer, field) (scheduled = (field))
#define msg_Dbg(decoder, format, pts, ...) (logged_pts = (pts))
#define vlc_mutex_lock(...) ((void)0)
#define vlc_mutex_unlock(...) ((void)0)
#define CFRelease(...) ((void)0)
#define Drain(...) ((void)0)
static OSStatus VTDecompressionSessionDecodeFrame(int session, int sample,
    int flags, frame_info_t *info, int *out)
{
    /* A callback can already own/free this allocation. Reusing its fields is
       sufficient to detect the same invalid caller dependency deterministically. */
    info->b_field = false;
    info->pts = -999;
    return rejected;
}
static int HandleVTStatus(void *decoder, int status, enum vtsession_status *out)
{ *out = VTSESSION_STATUS_OK; return status; }
static void submit(void)
{
    decoder_sys_t sys = {0}; decoder_sys_t *p_sys = &sys;
    block_t block = {0}; block_t *p_block = &block;
    void *p_dec = NULL;
    frame_info_t *p_info = malloc(sizeof(*p_info));
    p_info->b_field = true; p_info->pts = 123;
'''
    suffix = r'''
skip:;
    free(p_info);
}
int main(void)
{
    submit();
    if (scheduled != 1 || logged_pts != 123) {
        fputs("Caller read callback-owned frame metadata after submission\n", stderr);
        return 1;
    }
    rejected = 1; logged_pts = 0;
    submit();
    return logged_pts == 123 ? 0 : 2;
}
'''
    args.scratch.mkdir(parents=True, exist_ok=False)
    source = args.scratch / 'vt-frame-ownership.c'
    executable = args.scratch / ('vt-frame-ownership.exe' if os.name == 'nt' else 'vt-frame-ownership')
    source.write_text(prefix + fragment + suffix)
    subprocess.run([args.compiler, '-std=c11', '-O0', str(source), '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
    print('Actual VT submission preserves metadata across synchronous callback retirement')


if __name__ == '__main__':
    main()

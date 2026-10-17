/* S1 verification only: exercise the built Windows libVLC on generated media.
 * No GUI simulation, test clock, polling deadline or user profile access. */
#include <windows.h>
#include <malloc.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdbool.h>
#include <vlc/vlc.h>

enum { WIDTH = 320, HEIGHT = 180, PITCH = WIDTH * 4 };
struct observation {
    HANDLE stopped;
    CRITICAL_SECTION pixels_lock;
    unsigned char *pixels;
    volatile LONG opened, eos, error;
    volatile LONG64 frames, changed_frames, samples;
    uint64_t previous_hash;
    int audio_peak;
};

static void state_changed(void *opaque, libvlc_state_t state)
{
    struct observation *o = opaque;
    fprintf(stderr, "player state: %d\n", (int)state);
    if (state != libvlc_Stopped)
        InterlockedExchange(&o->opened, 1);
    if (state == libvlc_Stopped && InterlockedCompareExchange(&o->opened, 0, 0))
        SetEvent(o->stopped);
}

static void media_stopping(void *opaque, libvlc_media_t *media,
                           libvlc_stopping_reason_t reason)
{
    (void)media;
    struct observation *o = opaque;
    fprintf(stderr, "media stopping reason: %d\n", (int)reason);
    if (reason == libvlc_stopping_reason_eos) InterlockedExchange(&o->eos, 1);
    if (reason == libvlc_stopping_reason_error) InterlockedExchange(&o->error, 1);
}

static void *video_lock(void *opaque, void **planes)
{
    struct observation *o = opaque;
    EnterCriticalSection(&o->pixels_lock);
    planes[0] = o->pixels;
    return NULL;
}

static void video_unlock(void *opaque, void *picture, void *const *planes)
{
    (void)picture; (void)planes;
    struct observation *o = opaque;
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t i = 0; i < PITCH * HEIGHT; i++)
        hash = (hash ^ o->pixels[i]) * UINT64_C(1099511628211);
    if (o->previous_hash && hash != o->previous_hash)
        InterlockedIncrement64(&o->changed_frames);
    o->previous_hash = hash;
    LeaveCriticalSection(&o->pixels_lock);
}

static void video_display(void *opaque, void *picture)
{
    (void)picture;
    InterlockedIncrement64(&((struct observation *)opaque)->frames);
}

static void audio_play(void *opaque, const void *samples, unsigned count, int64_t pts)
{
    (void)pts;
    struct observation *o = opaque;
    const int16_t *pcm = samples;
    for (size_t i = 0; i < (size_t)count * 2; i++) {
        int magnitude = pcm[i] < 0 ? -(int)pcm[i] : pcm[i];
        if (magnitude > o->audio_peak) o->audio_peak = magnitude;
    }
    InterlockedExchangeAdd64(&o->samples, count);
}

int main(int argc, char **argv)
{
    if (argc != 2) { fprintf(stderr, "Usage: playback-check.exe <six-second-AV-fixture>\n"); return 2; }
    const char *options[] = {"--ignore-config", "--no-media-library", "--no-plugins-cache",
        "--no-osd"};
    struct observation o = {0};
    o.stopped = CreateEventW(NULL, TRUE, FALSE, NULL);
    o.pixels = _aligned_malloc(PITCH * HEIGHT, 32);
    InitializeCriticalSection(&o.pixels_lock);
    if (!o.stopped || !o.pixels) return 3;
    libvlc_instance_t *instance = libvlc_new(sizeof(options) / sizeof(options[0]), options);
    if (!instance) { fprintf(stderr, "%s\n", libvlc_errmsg()); return 3; }
    const struct libvlc_media_player_cbs callbacks = {
        .version = 0, .on_state_changed = state_changed, .on_media_stopping = media_stopping,
    };
    libvlc_media_t *media = libvlc_media_new_path(argv[1]);
    libvlc_media_player_t *player = libvlc_media_player_new(instance, &callbacks, &o);
    if (!media || !player) return 3;
    libvlc_video_set_callbacks(player, video_lock, video_unlock, video_display, &o);
    libvlc_video_set_format(player, "RV32", WIDTH, HEIGHT, PITCH);
    libvlc_audio_set_callbacks(player, audio_play, NULL, NULL, NULL, NULL, &o);
    libvlc_audio_set_format(player, "S16N", 48000, 2);
    libvlc_media_player_set_media(player, media);
    if (libvlc_media_player_play(player) != 0) return 3;
    if (WaitForSingleObject(o.stopped, INFINITE) != WAIT_OBJECT_0) return 3;
    /* Stopped is the libVLC lifecycle boundary; release joins output consumers. */
    libvlc_media_player_release(player);
    libvlc_media_release(media);
    libvlc_release(instance);
    bool passed = o.eos && !o.error && o.frames >= 100 && o.changed_frames >= 20
                  && o.samples >= 200000 && o.audio_peak > 0;
    printf("{\"passed\":%s,\"end_of_stream\":%s,\"error\":%s,"
           "\"displayed_frames\":%" PRId64 ",\"changing_frames\":%" PRId64 ","
           "\"audio_sample_frames\":%" PRId64 ",\"audio_peak_s16\":%d}\n",
           passed ? "true" : "false", o.eos ? "true" : "false", o.error ? "true" : "false",
           (int64_t)o.frames, (int64_t)o.changed_frames, (int64_t)o.samples, o.audio_peak);
    _aligned_free(o.pixels);
    DeleteCriticalSection(&o.pixels_lock);
    CloseHandle(o.stopped);
    return passed ? 0 : 1;
}

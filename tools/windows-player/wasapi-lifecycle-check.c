/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Exercise the actual pinned WASAPI functions with a deterministic COM client.
 * This controls event ordering, not elapsed time or physical audio rendering.
 * Native full-player/WASAPI acceptance remains a separate required check.
 */
#include <config.h>
#define MODULE_NAME wasapi_lifecycle_check
#define VLC_DYNAMIC_PLUGIN
#include "../../modules/audio_output/wasapi.c"
#include <vlc/vlc.h>
#include "../../lib/libvlc_internal.h"
#include <stdio.h>

struct client {
    IAudioClient audio;
    IAudioRenderClient render;
    bool running;
    unsigned starts, stops, padding;
    BYTE samples[4096];
};

static struct client *from_audio(IAudioClient *audio)
{
    return container_of(audio, struct client, audio);
}

static struct client *from_render(IAudioRenderClient *render)
{
    return container_of(render, struct client, render);
}

static HRESULT STDMETHODCALLTYPE client_start(IAudioClient *audio)
{
    struct client *client = from_audio(audio);
    if (client->running) return AUDCLNT_E_NOT_STOPPED;
    client->running = true;
    client->starts++;
    return S_OK;
}

static HRESULT STDMETHODCALLTYPE client_stop(IAudioClient *audio)
{
    struct client *client = from_audio(audio);
    client->running = false;
    client->stops++;
    return S_OK;
}

static HRESULT STDMETHODCALLTYPE client_reset(IAudioClient *audio)
{
    from_audio(audio)->padding = 0;
    return S_OK;
}

static HRESULT STDMETHODCALLTYPE current_padding(IAudioClient *audio, UINT32 *padding)
{
    *padding = from_audio(audio)->padding;
    return S_OK;
}

static HRESULT STDMETHODCALLTYPE get_service(IAudioClient *audio, REFIID iid, void **object)
{
    if (!IsEqualIID(iid, &IID_IAudioRenderClient)) return E_NOINTERFACE;
    *object = &from_audio(audio)->render;
    return S_OK;
}

static HRESULT STDMETHODCALLTYPE get_buffer(IAudioRenderClient *render, UINT32 frames, BYTE **buffer)
{
    if (frames > 1024) return E_INVALIDARG;
    *buffer = from_render(render)->samples;
    return S_OK;
}

static HRESULT STDMETHODCALLTYPE release_buffer(IAudioRenderClient *render, UINT32 frames, DWORD flags)
{
    (void)flags;
    from_render(render)->padding += frames;
    return S_OK;
}

static ULONG STDMETHODCALLTYPE release_render(IAudioRenderClient *render)
{
    (void)render;
    return 1;
}

static IAudioClientVtbl audio_methods = {
    .Start = client_start, .Stop = client_stop, .Reset = client_reset,
    .GetCurrentPadding = current_padding, .GetService = get_service,
};

static IAudioRenderClientVtbl render_methods = {
    .GetBuffer = get_buffer, .ReleaseBuffer = release_buffer, .Release = release_render,
};

static HRESULT queue_block(aout_stream_t *stream)
{
    block_t *block = block_Alloc(64);
    if (!block) return E_OUTOFMEMORY;
    memset(block->p_buffer, 0, block->i_buffer);
    block->i_nb_samples = 16;
    block->i_pts = VLC_TICK_0;
    block->i_length = vlc_tick_from_samples(16, 48000);
    return Play(stream, block, vlc_tick_now() + VLC_TICK_FROM_MS(80));
}

static void deliver_armed_start(struct aout_stream_owner *owner)
{
    if (owner->timer.deadline == VLC_TICK_INVALID) return;
    void (*callback)(aout_stream_t *) = owner->timer.callback;
    owner->timer.deadline = VLC_TICK_INVALID;
    owner->timer.callback = NULL;
    callback(&owner->s);
}

static int check(libvlc_instance_t *instance, bool queue_before_resume, bool flush_before_resume)
{
    struct client client = { .audio.lpVtbl = &audio_methods, .render.lpVtbl = &render_methods };
    struct aout_stream_owner *owner = vlc_object_create(VLC_OBJECT(instance->p_libvlc_int), sizeof(*owner));
    if (!owner) return 2;
    aout_stream_sys_t state = { .client = &client.audio, .started_state = STARTED_STATE_INIT,
        .rate = 48000, .frames = 1024, .block_align = 4, .format = VLC_CODEC_S16N,
        .first_pts = VLC_TICK_INVALID };
    owner->s.sys = &state;
    owner->timer.deadline = VLC_TICK_INVALID;
    owner->timer.callback = NULL;
    int result = 0;
    if (FAILED(Pause(&owner->s, true))) result = 2;
    if (!result && queue_before_resume) {
        if (FAILED(queue_block(&owner->s))) result = 2;
        deliver_armed_start(owner);
        if (client.starts || client.running) {
            fprintf(stderr, "FAIL: queued first audio started WASAPI while the input was paused\n");
            HRESULT resumed = Pause(&owner->s, false);
            fprintf(stderr, "resume after unexpected start returned 0x%08lX\n", (unsigned long)resumed);
            result = resumed == AUDCLNT_E_NOT_STOPPED ? 23 : 36;
        }
    }
    if (!result && queue_before_resume && flush_before_resume) {
        if (FAILED(Flush(&owner->s)) || client.padding || state.written) result = 32;
        if (!result && FAILED(queue_block(&owner->s))) result = 33;
        if (!result && (state.written != 16 || client.padding != 16)) result = 34;
        deliver_armed_start(owner);
        if (!result && client.running) result = 35;
    }
    if (!result && FAILED(Pause(&owner->s, false))) result = 24;
    if (!result && !queue_before_resume && client.starts) {
        fprintf(stderr, "FAIL: resume started an empty, never-started audio client\n");
        result = 25;
    }
    if (!result && !queue_before_resume) {
        if (FAILED(queue_block(&owner->s))) result = 2;
        deliver_armed_start(owner);
    }
    if (!result && (client.starts != 1 || !client.running)) result = 26;
    if (!result && (FAILED(Pause(&owner->s, true)) || client.running)) result = 27;
    if (!result && FAILED(Flush(&owner->s))) result = 28;
    if (!result && FAILED(queue_block(&owner->s))) result = 29;
    if (!result) {
        deliver_armed_start(owner);
        if (client.running) result = 30;
    }
    if (!result && (FAILED(Pause(&owner->s, false)) || !client.running || client.starts != 2)) result = 31;
    printf("case=%s flush-before-resume=%d result=%d starts=%u stops=%u\n", queue_before_resume ? "buffer-before-resume" : "resume-before-buffer", flush_before_resume, result, client.starts, client.stops);
    vlc_object_delete(&owner->s);
    return result;
}

int main(void)
{
    const char *options[] = {"--ignore-config", "--no-media-library", "--no-plugins-cache", "--no-plugins-scan"};
    libvlc_instance_t *instance = libvlc_new(ARRAY_SIZE(options), options);
    if (!instance) return 2;
    int first = check(instance, true, false);
    int second = check(instance, false, false);
    int third = check(instance, true, true);
    libvlc_release(instance);
    return first ? first : second ? second : third;
}

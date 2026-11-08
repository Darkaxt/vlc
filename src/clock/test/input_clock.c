/*****************************************************************************
 * input_clock.c: tests for the input buffering code
 *****************************************************************************
 * Copyright (C) 2023-2025 Alexandre Janniaux <ajanni@videolabs.io>
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 2.1 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
 *****************************************************************************/

#ifdef HAVE_CONFIG_H
# include "config.h"
#endif

/* This test must exercise its assertions in release-configuration builds. */
#undef NDEBUG

#include <vlc_common.h>
#include <vlc_modules.h>
#include <vlc_messages.h>
#include <vlc_tick.h>

#include <vlc/libvlc.h>

#include "../../../src/clock/input_clock.h"
#include "../../../src/clock/clock.h"
#include "../../../src/clock/clock_internal.h"

const char vlc_module_name[] = "test_input_clock";

static void LoggerLog(void *data, int type, const vlc_log_t *item,
        const char *fmt, va_list args)
{
    (void)data; (void)type; (void)item;
    vfprintf(stderr, fmt, args);
}

static const struct vlc_logger_operations logger_ops =
{
    .log = LoggerLog,
};
static struct vlc_logger logger = { &logger_ops };

static void test_clock_update(void)
{
    input_clock_t *clock = input_clock_New(&logger, 1.f);
    assert(clock != NULL);

    {
        vlc_tick_t system_now = VLC_TICK_0;
        vlc_tick_t system_duration = input_clock_GetSystemDuration(clock, system_now);
        assert(system_duration == 0);
    }

    bool can_pace_control = true;
    bool buffering_allowed = true;
    vlc_tick_t date_stream = VLC_TICK_0;
    vlc_tick_t date_system = VLC_TICK_0;
    input_clock_Update(clock, can_pace_control, buffering_allowed, false, date_stream, date_system);

    vlc_tick_t stream_duration, system_duration;
    input_clock_GetBufferingDuration(clock, &stream_duration, &system_duration);
    fprintf(stderr, "system_duration=%" PRId64 " stream_duration=%" PRId64 "\n",
            system_duration, stream_duration);
    assert(stream_duration == 0);
    assert(system_duration == 0);

    vlc_tick_t system_now = VLC_TICK_0;
    system_duration = input_clock_GetSystemDuration(clock, system_now);
    assert(system_duration == 0);

    /* Reset drift */
    input_clock_Reset(clock);
    input_clock_Delete(clock);
}

struct input_clock_updates {
    unsigned updates;
    unsigned discontinuities;
};

static vlc_tick_t input_clock_update(void *opaque, vlc_tick_t system,
        vlc_tick_t stream, double rate, bool discontinuity)
{
    (void)system; (void)stream; (void)rate;
    struct input_clock_updates *updates = opaque;
    updates->updates++;
    updates->discontinuities += discontinuity;
    return 0;
}

static const struct vlc_input_clock_cbs input_clock_ops = {
    .update = input_clock_update,
};

static void test_paused_pcr_updates(void)
{
    /* A paused seek/next-frame can feed PCRs spaced farther apart than the
     * normal 300ms gap threshold while the system date remains frozen. */
    for (unsigned paced = 0; paced < 2; paced++)
    {
        struct input_clock_updates updates = { 0 };
        input_clock_t *clock = input_clock_New(&logger, 1.f);
        assert(clock != NULL);
        input_clock_AttachListener(clock, &input_clock_ops, &updates);
        const vlc_tick_t paused_at = VLC_TICK_0 + VLC_TICK_FROM_SEC(10);
        input_clock_ChangePause(clock, true, paused_at);
        input_clock_Update(clock, paced, true, false,
                           VLC_TICK_0 + VLC_TICK_FROM_SEC(6), paused_at);
        for (unsigned second = 7; second <= 9; second++)
            input_clock_Update(clock, paced, false, false,
                               VLC_TICK_0 + VLC_TICK_FROM_SEC(second), paused_at);
        assert(updates.updates == 4);
        assert(updates.discontinuities == 0);

        /* Backwards PCRs still reset the clock, even while paused. */
        input_clock_Update(clock, paced, false, false,
                           VLC_TICK_0 + VLC_TICK_FROM_SEC(8), paused_at);
        assert(updates.discontinuities == 1);

        /* Resume shifts system dates by the real pause duration. Ordinary
         * equal progression is valid; a later forward jump remains a gap. */
        const vlc_tick_t resumed_at = paused_at + VLC_TICK_FROM_SEC(20);
        input_clock_ChangePause(clock, false, resumed_at);
        input_clock_Update(clock, paced, false, false,
                           VLC_TICK_0 + VLC_TICK_FROM_SEC(9),
                           resumed_at + VLC_TICK_FROM_SEC(1));
        assert(updates.discontinuities == 1);
        input_clock_Update(clock, paced, false, false,
                           VLC_TICK_0 + VLC_TICK_FROM_SEC(20),
                           resumed_at + VLC_TICK_FROM_SEC(2));
        assert(updates.discontinuities == 2);
        input_clock_Delete(clock);
    }
}

static bool test_paused_output_clock_reset(void)
{
    /* A seek finishes buffering against the frozen pause date. Resetting its
     * output references must retain that date so resume shifts the new PCR
     * and monotonic references by the actual pause duration, exactly once. */
    for (unsigned resets = 0; resets <= 2; resets++)
    {
        vlc_clock_main_t *main = vlc_clock_main_New(&logger, NULL);
        assert(main != NULL);
        vlc_clock_main_Lock(main);
        vlc_clock_t *output = vlc_clock_main_CreateMaster(main, "audio/test", NULL, NULL);
        assert(output != NULL);
        const vlc_tick_t paused_at = VLC_TICK_0 + VLC_TICK_FROM_SEC(10);
        const vlc_tick_t resumed_at = paused_at + VLC_TICK_FROM_SEC(20);
        const vlc_tick_t pts = VLC_TICK_0 + VLC_TICK_FROM_SEC(60);
        vlc_clock_main_SetFirstPcr(main, paused_at, pts);
        vlc_clock_Start(output, paused_at, pts);
        vlc_clock_main_ChangePause(main, paused_at, true);
        for (unsigned reset = 0; reset < resets; reset++)
        {
            vlc_clock_main_Reset(main);
            vlc_clock_main_SetFirstPcr(main, paused_at, pts);
            vlc_clock_Start(output, paused_at, pts);
        }
        vlc_tick_t before = vlc_clock_ConvertToSystem(output, paused_at, pts, 1., NULL);
        vlc_clock_main_ChangePause(main, resumed_at, false);
        vlc_tick_t after = vlc_clock_ConvertToSystem(output, resumed_at, pts, 1., NULL);
        fprintf(stderr, "paused output reset=%u: shift=%"PRId64" expected=%"PRId64"\n",
                resets, after - before, resumed_at - paused_at);
        const bool valid = after - before == resumed_at - paused_at;
        vlc_clock_main_Unlock(main);
        vlc_clock_Delete(output);
        vlc_clock_main_Delete(main);
        if (!valid)
            return false;
    }
    return true;
}

static void clock_update_abort(
    vlc_tick_t system_ts, vlc_tick_t ts, double rate,
    unsigned frame_rate, unsigned frame_rate_base, void *data)
{
    (void)system_ts; (void)ts; (void)rate;
    (void)frame_rate; (void)frame_rate_base;
    (void)data;
    assert(!"No clock update should happen");
}

static const struct vlc_clock_cbs clock_abort_ops =
{
    .on_update = clock_update_abort,
};

struct clock_validate {
    bool validate;
    struct {
        vlc_tick_t system;
        vlc_tick_t stream;
    } expected;
};

static void clock_update_validate(
    vlc_tick_t system_ts, vlc_tick_t ts, double rate,
    unsigned frame_rate, unsigned frame_rate_base, void *data)
{
    (void)system_ts; (void)ts; (void)rate;
    (void)frame_rate; (void)frame_rate_base;

    struct clock_validate *validate = data;
    fprintf(stderr, "%s: system=%" PRId64 " stream=%" PRId64
            ", checking against system=%"PRId64 " stream=%" PRId64 "\n",
            __func__, system_ts, ts, validate->expected.system, validate->expected.stream);
    validate->validate = true;
    assert(validate->expected.system == system_ts);
    assert(validate->expected.stream == ts);
}
static const struct vlc_clock_cbs clock_validate_ops =
{
    .on_update = clock_update_validate,
};

struct clock_listener_switch {
    const struct vlc_clock_cbs *cbs;
    void *opaque;
};

static void clock_update_switch(
    vlc_tick_t system_ts, vlc_tick_t ts, double rate,
    unsigned frame_rate, unsigned frame_rate_base, void *data)
{
    struct clock_listener_switch *listener = data;
    listener->cbs->on_update(system_ts, ts, rate, frame_rate, frame_rate_base, listener->opaque);
}

static const struct vlc_clock_cbs clock_switch_ops = {
    .on_update = clock_update_switch,
};



int main(void)
{
    fprintf(stderr, "test_clock_update:\n");
    test_clock_update();
    fprintf(stderr, "test_paused_pcr_updates:\n");
    test_paused_pcr_updates();
    fprintf(stderr, "test_paused_output_clock_reset:\n");
    if (!test_paused_output_clock_reset())
        return 1;
    return 0;
}

/* Regression for the actual 6.1 -> 5.x worker, LGPL-2.1-or-later. */
#define MODULE_NAME check_channel_mixer
#define MODULE_STRING "check_channel_mixer"
#include <simple.c>

/* This is a test host, not a dynamic plugin exporting its own module symbol. */
const char vlc_module_name[] = MODULE_STRING;

int main(void)
{
    const float input[] = {1, 2, 4, 6, 8, 10, 12, 21, 22, 24, 26, 28, 30, 32};
    const float expected[][6] = {{1, 2, 6, 7, 10, 12}, {21, 22, 26, 27, 30, 32}};
    for (unsigned lfe = 0; lfe < 2; ++lfe)
    {
        float output[14];
        for (unsigned i = 0; i < 14; ++i)
            output[i] = -1234.f;
        filter_t filter = {0};
        filter.fmt_in.audio.i_physical_channels = AOUT_CHAN_LFE;
        filter.fmt_out.audio.i_physical_channels = lfe ? AOUT_CHAN_LFE : 0;
        block_t in = {.p_buffer = (uint8_t *)input, .i_nb_samples = 2};
        block_t out = {.p_buffer = (uint8_t *)(output + 1)};
        DoWork_6_1_to_5_x(&filter, &in, &out);
        unsigned channels = 5 + lfe;
        for (unsigned frame = 0; frame < 2; ++frame)
            for (unsigned channel = 0; channel < channels; ++channel)
                if (output[1 + frame * channels + channel] != expected[frame][channel])
                    return 1;
        if (output[0] != -1234.f || output[1 + 2 * channels] != -1234.f)
            return 2;
    }
    return 0;
}

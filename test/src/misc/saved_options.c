/* SPDX-License-Identifier: LGPL-2.1-or-later */
#undef NDEBUG
#include <assert.h>
#include <vlc_saved_options.h>
int main(void)
{
    struct vlc_saved_options options;
    assert(vlc_saved_options_split("--no-video --rate=1.25 --snapshot-path=\"D:\\My Videos\"",&options));
    assert(options.count==3);
    struct vlc_saved_option option;
    bool enabled;
    assert(vlc_saved_option_read(options.args[0],&option));
    assert(vlc_saved_option_bool(&option,&enabled) && !enabled);
    assert(vlc_saved_option_read(options.args[2],&option));
    assert(!strcmp(option.name,"snapshot-path") && !strcmp(option.value,"D:\\My Videos"));
    vlc_saved_options_release(&options);
    assert(!vlc_saved_options_split("--snapshot-path=\"unfinished",&options));
    assert(vlc_saved_options_split("video.mp4 --no-video=true --rate=\"$(touch x)\"",&options));
    assert(!vlc_saved_option_read(options.args[0],&option));
    assert(!vlc_saved_option_read(options.args[1],&option));
    assert(vlc_saved_option_read(options.args[2],&option));
    assert(!strcmp(option.value,"$(touch x)"));
    vlc_saved_options_release(&options);
    assert(!vlc_saved_option_allowed("reset-config"));
    assert(!vlc_saved_option_allowed("extra-options"));
    assert(vlc_saved_option_allowed("rate"));
    assert(vlc_saved_options_split("--snapshot-path=\\\\server\\share",&options));
    assert(vlc_saved_option_read(options.args[0],&option));
    assert(!strcmp(option.value,"\\\\server\\share"));
    vlc_saved_options_release(&options);
    assert(vlc_saved_options_split("",&options) && !options.count);
    vlc_saved_options_release(&options);
    return 0;
}

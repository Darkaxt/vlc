/* SPDX-License-Identifier: LGPL-2.1-or-later */
#undef NDEBUG
#include <assert.h>
#include <vlc_history.h>

int main(void)
{
    assert(!vlc_history_is_excluded("", "file:///D:/Movies/a.mp4", "D:\\Movies\\a.mp4"));
    assert(vlc_history_is_excluded("private", "file:///D:/private/a.mp4", NULL));
    assert(vlc_history_is_excluded(" *.secret; D:\\Private\\* ", "file:///D:/Private/a.mp4", "D:\\Private\\a.mp4"));
    assert(vlc_history_is_excluded("https://example.test/*", "https://EXAMPLE.test/live?id=1", NULL));
    assert(!vlc_history_is_excluded("*.mkv", "file:///D:/a.mp4", "D:\\a.mp4"));
    assert(vlc_history_is_excluded("a?.mp4", "file:///a1.mp4", "a1.mp4"));
    assert(!vlc_history_is_excluded("a?.mp4", "file:///a12.mp4", "a12.mp4"));
    assert(!vlc_history_is_excluded(" ; ; ", "file:///anything", NULL));
    assert(vlc_history_is_excluded("*", "", NULL));
    assert(!vlc_history_is_excluded(NULL, NULL, NULL));
    return 0;
}

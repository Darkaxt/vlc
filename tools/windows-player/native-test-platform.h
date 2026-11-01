/* Native Windows test-only binding for the POSIX harness alarm declaration.
 * The native runner sets VLC_TEST_TIMEOUT=0: lifecycle follows process exit.
 * Never silently ignore an alarm request if that required setting is missing.
 * No production target includes this header.
 */
#ifndef VLC_REDESIGN_NATIVE_TEST_PLATFORM_H
#define VLC_REDESIGN_NATIVE_TEST_PLATFORM_H
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
#ifdef _WIN32
#include <stdio.h>
#include <stdlib.h>
static inline unsigned vlc_native_test_alarm(unsigned seconds)
{
    fprintf(stderr, "Unsupported POSIX alarm(%u): native tests require VLC_TEST_TIMEOUT=0\n", seconds);
    exit(EXIT_FAILURE);
}
#define alarm vlc_native_test_alarm
#endif
#endif

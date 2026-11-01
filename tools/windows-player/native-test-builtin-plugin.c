/* Expose an upstream test EXE's existing builtins through the Windows loader.
 * PE core DLLs cannot discover an EXE's ELF-style weak builtin table. Keep all
 * mocks and their state in the unchanged test EXE; register that exact entry.
 * This adapter is staged only in the isolated native-test plugin directory.
 */
#include "config.h"
#include <windows.h>
#include <vlc_common.h>
#include <vlc_plugin.h>

VLC_API_VERSION_EXPORT

int vlc_entry(vlc_set_cb callback, void *opaque)
{
    const vlc_plugin_cb *entries = (const vlc_plugin_cb *)
        GetProcAddress(GetModuleHandleW(NULL), "vlc_static_modules");
    if (entries == NULL || entries[0] == NULL || entries[1] != NULL)
        return VLC_EGENERIC;
    return entries[0](callback, opaque);
}

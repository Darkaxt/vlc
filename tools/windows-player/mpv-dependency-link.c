/* Build diagnostic for the actual dependency contract used by FFmpeg.
 * Compile/link only; no playback or feature acceptance is claimed here. */
#include <libplacebo/vulkan.h>
#include <spirv_cross_c.h>
#include <stdint.h>

int main(void)
{
    volatile uintptr_t placebo = (uintptr_t) pl_vulkan_create;
    volatile uintptr_t spirv_cross = (uintptr_t) spvc_get_version;
    return (placebo == 0) || (spirv_cross == 0);
}

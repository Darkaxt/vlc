/* Pinned-core metadata inspection for S1. No user configuration is loaded. */
#include <vlc/vlc.h>
#include <vlc_common.h>
#include <vlc_modules.h>
#include <vlc_configuration.h>
#include <stdio.h>

static void string(const char *text)
{
    putchar('"');
    if (text) for (const unsigned char *p = (const unsigned char *)text; *p; p++) {
        if (*p == '"' || *p == '\\') { putchar('\\'); putchar(*p); }
        else if (*p < 32) printf("\\u%04x", (unsigned)*p);
        else putchar(*p);
    }
    putchar('"');
}

int main(void)
{
    const char *options[] = {"--ignore-config", "--no-media-library", "--no-plugins-cache"};
    libvlc_instance_t *instance = libvlc_new(3, options);
    if (!instance) return 1;
    size_t count;
    module_t **modules = module_list_get(&count);
    if (!modules || !count) return 1;
    printf("{\"version\":"); string(libvlc_get_version());
    printf(",\"compiler\":"); string(libvlc_get_compiler());
    printf(",\"changeset\":"); string(libvlc_get_changeset());
    printf(",\"modules\":[");
    for (size_t i = 0; i < count; i++) {
        if (i) putchar(',');
        printf("{\"id\":"); string(module_get_object(modules[i]));
        printf(",\"name\":"); string(module_get_name(modules[i], true));
        printf(",\"capability\":"); string(module_get_capability(modules[i]));
        printf(",\"options\":[");
        unsigned length;
        module_config_t *config = module_config_get(modules[i], &length);
        bool first = true;
        for (unsigned j = 0; j < length; j++) if (config[j].psz_name) {
            if (!first) putchar(',');
            first = false;
            printf("{\"name\":"); string(config[j].psz_name);
            printf(",\"type\":%u}", (unsigned)config[j].i_type);
        }
        printf("]}"); module_config_free(config);
    }
    printf("]}\n"); module_list_free(modules); libvlc_release(instance);
    return 0;
}

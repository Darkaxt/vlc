// SPDX-License-Identifier: GPL-2.0-or-later
// Native Windows regression; invoke with a fresh, task-owned E: directory.
// Leaves exact test outputs for the transactional cleanup owner.
#include <vlc/vlc.h>
#include <vlc_common.h>
#include <vlc_configuration.h>
#include <vlc_charset.h>
#include <vlc_fs.h>
#include "../../lib/libvlc_internal.h"
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char *contents(const char *path)
{
    FILE *file = vlc_fopen(path, "rb");
    if (!file) return NULL;
    if (fseek(file, 0, SEEK_END)) abort();
    long length = ftell(file);
    if (length < 0 || length > 1000000) abort();
    rewind(file);
    char *text = malloc(length + 1);
    if (!text || fread(text, 1, length, file) != (size_t)length) abort();
    text[length] = 0;
    fclose(file);
    return text;
}

int main(int argc, char **argv)
{
    if (argc != 2 || (argv[1][0] != 'E' && argv[1][0] != 'e') || argv[1][1] != ':')
        return 2;
    size_t capacity = strlen(argv[1]) + 64;
    char *path = malloc(capacity), *option = malloc(capacity), *missing = malloc(capacity);
    if (!path || !option || !missing) return 2;
    snprintf(path, capacity, "%s/vlcrc", argv[1]);
    snprintf(option, capacity, "--config=%s", path);
    snprintf(missing, capacity, "%s/absent-source", argv[1]);
    wchar_t *wide = ToWide(path);
    if (!wide) return 2;
    bool exists = GetFileAttributesW(wide) != INVALID_FILE_ATTRIBUTES;
    free(wide);
    if (exists) return 2;
    const char *args[] = {"--ignore-config", "--no-media-library", "--no-plugins-cache",
                         "--no-plugins-scan", option};
    libvlc_instance_t *instance = libvlc_new(ARRAY_SIZE(args), args);
    if (!instance) return 2;
    config_PutInt("short-jump-size", 13);
    if (config_SaveConfigFile(instance->p_libvlc_int)) return 2;
    char *before = contents(path);
    if (!before || !strstr(before, "\nshort-jump-size=13")) return 2;

    wide = ToWide(path);
    HANDLE lock = CreateFileW(wide, GENERIC_READ, FILE_SHARE_READ, NULL,
                              OPEN_EXISTING, 0, NULL);
    free(wide);
    if (lock == INVALID_HANDLE_VALUE) return 2;
    config_PutInt("short-jump-size", 17);
    int result = config_SaveConfigFile(instance->p_libvlc_int);
    char *after = contents(path);
    bool reported_failure = result != 0;
    bool original_preserved = after && !strcmp(before, after);
    CloseHandle(lock);
    free(after);

    bool missing_source_failed = vlc_rename(missing, path) != 0;
    after = contents(path);
    bool missing_source_preserved_destination = after && !strcmp(before, after);
    free(after);
    free(before);

    bool retry_succeeded = config_SaveConfigFile(instance->p_libvlc_int) == 0;
    after = contents(path);
    bool replacement_saved_value = after && strstr(after, "\nshort-jump-size=17");
    free(after);
    libvlc_release(instance);
    printf("{\"locked_save_reports_failure\":%s,\"locked_save_preserves_original\":%s,"
           "\"missing_source_reports_failure\":%s,\"missing_source_preserves_destination\":%s,"
           "\"retry_succeeds\":%s,\"replacement_saves_value\":%s}\n",
           reported_failure ? "true" : "false", original_preserved ? "true" : "false",
           missing_source_failed ? "true" : "false", missing_source_preserved_destination ? "true" : "false",
           retry_succeeded ? "true" : "false", replacement_saved_value ? "true" : "false");
    free(missing); free(option); free(path);
    return reported_failure && original_preserved && missing_source_failed &&
           missing_source_preserved_destination && retry_succeeded && replacement_saved_value ? 0 : 1;
}

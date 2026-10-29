// SPDX-License-Identifier: LGPL-2.1-or-later
/*****************************************************************************
 * filesystem.c: filesystem helpers
 *****************************************************************************
 * Copyright © 2024 VLC authors, VideoLAN and Videolabs
 *
 * Authors: Gabriel Lafond Thenaille <gabriel@videolabs.io>
 *****************************************************************************/

#ifdef HAVE_CONFIG_H
# include "config.h"
#endif

#include <vlc_common.h>
#include <vlc_fs.h>

/**
 * Create all directories in the given path if missing.
 */
int vlc_mkdir_parent(const char *dirname, mode_t mode)
{
    int ret = vlc_mkdir(dirname, mode);
    if (ret == 0 || errno == EEXIST) {
        return 0;
    } else if (errno != ENOENT) {
        return -1;
    }

    char *path = strdup(dirname);
    if (path == NULL) {
        return -1;
    }

    char *ptr = path;
#ifdef _WIN32
    /* Win32 accepts both separators. A skin member can append '/' to a
     * native temporary path, so walk the same components that mkdir sees. */
    for (char *cursor = path; *cursor; ++cursor)
        if (*cursor == '/')
            *cursor = DIR_SEP_CHAR;

    if (path[0] && path[1] == ':') {
        /* A drive prefix is a root, not a directory to create. _wmkdir("D:")
         * returns EACCES even when the drive and requested parents exist. */
        ptr = path + 2;
        if (*ptr == DIR_SEP_CHAR)
            ++ptr;
    } else if (path[0] == DIR_SEP_CHAR && path[1] == DIR_SEP_CHAR) {
        /* Preserve the existing server/share root of a UNC path. */
        char *root_end = strchr(path + 2, DIR_SEP_CHAR);
        if (root_end != NULL)
            root_end = strchr(root_end + 1, DIR_SEP_CHAR);
        if (root_end == NULL) {
            free(path);
            return -1;
        }
        ptr = root_end + 1;
    } else
#endif
    if (*ptr == DIR_SEP_CHAR)
        ++ptr;
    while (*ptr) {
        ptr = strchr(ptr, DIR_SEP_CHAR);
        if (ptr == NULL) {
            break;
        }
        *ptr = '\0';
        if (vlc_mkdir(path, mode) != 0) {
            if (errno != EEXIST) {
                free(path);
                return -1;
            }
        }
        *ptr = DIR_SEP_CHAR;
        ptr++;
    }
    ret = vlc_mkdir(path, mode);
    if (errno == EEXIST) {
        ret = 0;
    }
    free(path);
    return ret;
}

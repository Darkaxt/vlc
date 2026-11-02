/* SPDX-License-Identifier: LGPL-2.1-or-later */
#ifndef VLC_HISTORY_H
#define VLC_HISTORY_H
#include <stdbool.h>
#include <stddef.h>
#include <string.h>

static inline unsigned char vlc_history_fold(unsigned char c)
{
    return c >= 'A' && c <= 'Z' ? c + ('a'-'A') : c;
}

/* No recursion or regular-expression engine. UTF-8 bytes are preserved; ASCII
 * path/scheme letters compare without case. Stars and question marks match a
 * full URI/path; a plain term matches anywhere. Empty terms never exclude. */
static inline bool vlc_history_match(const char *first, const char *last, const char *text)
{
    if (!text || first == last) return false;
    bool glob = false;
    for (const char *p=first; p!=last; ++p) glob |= *p=='*' || *p=='?';
    if (!glob)
    {
        for (const char *s=text; *s; ++s)
        {
            const char *p=first, *v=s;
            while (p!=last && *v && vlc_history_fold(*p)==vlc_history_fold(*v)) { ++p; ++v; }
            if (p==last) return true;
        }
        return false;
    }
    const char *pattern=first, *star=NULL, *retry=NULL;
    while (*text)
    {
        if (pattern!=last && (*pattern=='?' || vlc_history_fold(*pattern)==vlc_history_fold(*text)))
        { ++pattern; ++text; }
        else if (pattern!=last && *pattern=='*') { star=pattern++; retry=text; }
        else if (star) { pattern=star+1; text=++retry; }
        else return false;
    }
    while (pattern!=last && *pattern=='*') ++pattern;
    return pattern==last;
}

static inline bool vlc_history_is_excluded(const char *patterns, const char *uri, const char *path)
{
    if (!patterns) return false;
    while (*patterns)
    {
        const char *end=strchr(patterns,';');
        if (!end) end=patterns+strlen(patterns);
        const char *first=patterns, *last=end;
        while (first!=last && (*first==' ' || *first=='\t')) ++first;
        while (last!=first && (last[-1]==' ' || last[-1]=='\t')) --last;
        if (vlc_history_match(first,last,uri) || vlc_history_match(first,last,path)) return true;
        patterns=*end ? end+1 : end;
    }
    return false;
}
#endif

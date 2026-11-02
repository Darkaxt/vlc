/* SPDX-License-Identifier: LGPL-2.1-or-later */
#ifndef VLC_SAVED_OPTIONS_H
#define VLC_SAVED_OPTIONS_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <math.h>

struct vlc_saved_options { char *storage; char **args; size_t count; };
struct vlc_saved_option { const char *name; const char *value; bool negative; };

static inline bool vlc_saved_space(char c) { return c==' ' || c=='\t' || c=='\r' || c=='\n'; }
static inline void vlc_saved_options_release(struct vlc_saved_options *options)
{
    free(options->args);free(options->storage);
    options->storage=NULL;options->args=NULL;options->count=0;
}

/* Shell-free tokenisation: quoting groups a value, backslashes are retained in
 * Windows paths, and no environment, substitution or executable is evaluated. */
static inline bool vlc_saved_options_split(const char *text,struct vlc_saved_options *out)
{
    out->storage=NULL;out->args=NULL;out->count=0;
    if (!text) text="";
    const size_t length=strlen(text);
    if (length >= SIZE_MAX/sizeof(char*)-1) return false;
    out->storage=(char*)malloc(length+1);
    out->args=(char**)malloc((length+1)*sizeof(char*));
    if (!out->storage || !out->args) { vlc_saved_options_release(out);return false; }
    char *write=out->storage;
    while (*text)
    {
        while (vlc_saved_space(*text)) ++text;
        if (!*text) break;
        out->args[out->count++]=write;
        char quote=0;
        while (*text && (quote || !vlc_saved_space(*text)))
        {
            const char c=*text++;
            if ((c=='\'' || c=='"') && (!quote || quote==c)) { quote=quote ? 0 : c;continue; }
            if (c=='\\' && (*text=='"' || *text=='\'' || (!quote && vlc_saved_space(*text))))
                *write++=*text++;
            else *write++=c;
        }
        if (quote) { vlc_saved_options_release(out);return false; }
        *write++='\0';
    }
    return true;
}

/* Long options use --name=value; boolean switches also support --name and
 * --no-name. Positional files and process/startup-control switches are excluded
 * by the caller. This cannot become a second media-opening command line. */
static inline bool vlc_saved_option_read(char *arg,struct vlc_saved_option *out)
{
    if (strncmp(arg,"--",2)) return false;
    out->name=arg+2;out->negative=false;out->value=NULL;
    if (!strncmp(out->name,"no-",3)) { out->negative=true;out->name+=3; }
    char *equals=strchr((char*)out->name,'=');
    if (equals) { *equals='\0';out->value=equals+1; }
    return *out->name && !(out->negative && out->value);
}
static inline bool vlc_saved_option_allowed(const char *name)
{
    return strcmp(name,"extra-options") && strcmp(name,"plugins-cache") &&
           strcmp(name,"plugins-scan") && strcmp(name,"reset-plugins-cache") &&
           strcmp(name,"ignore-config") && strcmp(name,"config") &&
           strcmp(name,"reset-config") && strcmp(name,"help") &&
           strcmp(name,"version") && strcmp(name,"list") && strcmp(name,"list-verbose");
}
static inline bool vlc_saved_option_bool(const struct vlc_saved_option *option,bool *out)
{
    if (!option->value) { *out=!option->negative;return true; }
    if (!strcmp(option->value,"true") || !strcmp(option->value,"1")) { *out=true;return true; }
    if (!strcmp(option->value,"false") || !strcmp(option->value,"0")) { *out=false;return true; }
    return false;
}
static inline bool vlc_saved_option_int(const struct vlc_saved_option *option,int64_t *out)
{
    if (!option->value || !*option->value || option->negative) return false;
    char *end;
    errno=0;
    *out=strtoll(option->value,&end,0);
    return !errno && end!=option->value && !*end;
}
#ifdef VLC_API
#ifdef __cplusplus
extern "C" {
#endif
/* Pure validation against the loaded native option metadata. The optional
 * allocated error names the option, never its possibly secret value. */
VLC_API int config_ValidateSavedOptions(const char *,char **);
#ifdef __cplusplus
}
#endif
#endif
#endif

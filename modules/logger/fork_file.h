/* Windows stabilization diagnostics. Included by the existing file logger.
 * GPL-2.0-or-later, matching file.c. No worker, uploader or background task. */
#ifndef VLC_FORK_FILE_H
#define VLC_FORK_FILE_H
#include <windows.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include <wctype.h>
#include <fcntl.h>
#include <io.h>

#define FORK_LOG_BYTES (4u * 1024u * 1024u)
#define FORK_LOG_FILES 8u
#define FORK_LOG_RETENTION (UINT64_C(72) * 3600 * 10000000)
#define FORK_LOG_DAY (UINT64_C(86400) * 10000000)

typedef struct {
    wchar_t *directory;
    HANDLE allocation;
    CRITICAL_SECTION lock;
    FILE *stream;
    uint64_t opened, origin;
    size_t bytes;
    bool failed;
} fork_log_t;

static uint64_t fork_log_now(void)
{
    FILETIME time;
    GetSystemTimeAsFileTime(&time);
    return ((uint64_t)time.dwHighDateTime << 32) | time.dwLowDateTime;
}

static bool fork_log_name(const wchar_t *name, uint64_t *created)
{
    unsigned long long time;
    unsigned long pid;
    unsigned sequence;
    wchar_t canonical[96];
    if (swscanf(name, L"vlc-%20llu-%10lu-%6u.log", &time, &pid, &sequence) != 3)
        return false;
    swprintf(canonical, 96, L"vlc-%020llu-%010lu-%06u.log", time, pid, sequence);
    if (wcscmp(canonical, name))
        return false;
    *created = time;
    return true;
}

typedef struct { wchar_t name[96]; uint64_t created; } fork_log_entry_t;

static int fork_log_compare(const void *a, const void *b)
{
    return wcscmp(((const fork_log_entry_t *)a)->name,
                  ((const fork_log_entry_t *)b)->name);
}

/* Only exact generated leaf names are eligible. DeleteFile cannot remove an
 * active writer: our handles deliberately do not grant FILE_SHARE_DELETE. */
static bool fork_log_prune(fork_log_t *log, uint64_t now)
{
    size_t length = wcslen(log->directory) + 100;
    wchar_t *path = malloc(length * sizeof(*path));
    fork_log_entry_t *entries = NULL;
    size_t count = 0;
    bool valid = path != NULL;
    if (!valid)
        return false;
    swprintf(path, length, L"%ls\\vlc-*.log", log->directory);
    WIN32_FIND_DATAW data;
    HANDLE search = FindFirstFileW(path, &data);
    if (search == INVALID_HANDLE_VALUE) {
        valid = GetLastError() == ERROR_FILE_NOT_FOUND;
    } else {
        do {
            uint64_t created;
            if ((data.dwFileAttributes & (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT))
             || !fork_log_name(data.cFileName, &created))
                continue;
            fork_log_entry_t *next = realloc(entries, (count + 1) * sizeof(*entries));
            if (!next) { valid = false; break; }
            entries = next;
            wcscpy(entries[count].name, data.cFileName);
            entries[count++].created = created;
        } while (FindNextFileW(search, &data));
        if (valid && GetLastError() != ERROR_NO_MORE_FILES)
            valid = false;
        FindClose(search);
    }
    if (valid) {
        if (count > 1)
            qsort(entries, count, sizeof(*entries), fork_log_compare);
        size_t retained = count;
        for (size_t i = 0; i < count; ++i) {
            bool expired = now >= entries[i].created
                        && now - entries[i].created >= FORK_LOG_RETENTION;
            if (!expired && retained < FORK_LOG_FILES)
                continue;
            swprintf(path, length, L"%ls\\%ls", log->directory, entries[i].name);
            if (DeleteFileW(path))
                --retained;
        }
        valid = retained < FORK_LOG_FILES;
    }
    free(entries);
    free(path);
    return valid;
}

static bool fork_log_rotate(fork_log_t *log, uint64_t now)
{
    static LONG sequence;
    if (log->stream) { fclose(log->stream); log->stream = NULL; }
    DWORD wait = WaitForSingleObject(log->allocation, INFINITE);
    if (wait != WAIT_OBJECT_0 && wait != WAIT_ABANDONED)
        return false;
    bool ok = fork_log_prune(log, now);
    if (ok) {
        size_t length = wcslen(log->directory) + 100;
        wchar_t *path = malloc(length * sizeof(*path));
        HANDLE file = INVALID_HANDLE_VALUE;
        if (path) {
            swprintf(path, length, L"%ls\\vlc-%020llu-%010lu-%06u.log",
                     log->directory, (unsigned long long)now,
                     GetCurrentProcessId(), (unsigned)InterlockedIncrement(&sequence));
            file = CreateFileW(path, GENERIC_WRITE, FILE_SHARE_READ, NULL,
                               CREATE_NEW, FILE_ATTRIBUTE_NORMAL, NULL);
            free(path);
        }
        if (file != INVALID_HANDLE_VALUE) {
            int fd = _open_osfhandle((intptr_t)file, _O_WRONLY | _O_BINARY);
            if (fd >= 0) {
                log->stream = _fdopen(fd, "wb");
                if (!log->stream) _close(fd);
            } else CloseHandle(file);
        }
        ok = log->stream != NULL;
        log->bytes = 0;
        log->opened = now;
    }
    ReleaseMutex(log->allocation);
    return ok;
}

static bool fork_log_open(fork_log_t *log, const wchar_t *directory)
{
    memset(log, 0, sizeof(*log));
    DWORD attrs = GetFileAttributesW(directory);
    if (attrs == INVALID_FILE_ATTRIBUTES) {
        if (!CreateDirectoryW(directory, NULL) && GetLastError() != ERROR_ALREADY_EXISTS)
            return false;
        attrs = GetFileAttributesW(directory);
    }
    if (!(attrs & FILE_ATTRIBUTE_DIRECTORY) || (attrs & FILE_ATTRIBUTE_REPARSE_POINT))
        return false;
    log->directory = _wcsdup(directory);
    if (!log->directory) return false;
    uint64_t hash = UINT64_C(14695981039346656037);
    for (const wchar_t *p = directory; *p; ++p) {
        hash ^= (uint16_t)towlower(*p);
        hash *= UINT64_C(1099511628211);
    }
    wchar_t name[80];
    swprintf(name, 80, L"Local\\ModernVLC.Diagnostics.%016llx", (unsigned long long)hash);
    log->allocation = CreateMutexW(NULL, FALSE, name);
    if (!log->allocation) { free(log->directory); return false; }
    InitializeCriticalSection(&log->lock);
    log->origin = GetTickCount64();
    if (fork_log_rotate(log, fork_log_now())) return true;
    DeleteCriticalSection(&log->lock);
    CloseHandle(log->allocation);
    free(log->directory);
    return false;
}

/* Callers provide a bounded, already formatted UTF-8 line. Explicit now makes
 * age/rotation deterministic to exercise without changing the system clock. */
static void fork_log_write(fork_log_t *log, const char *line, size_t bytes, uint64_t now)
{
    EnterCriticalSection(&log->lock);
    if (!log->failed && (log->opened / FORK_LOG_DAY != now / FORK_LOG_DAY
                     || log->bytes + bytes > FORK_LOG_BYTES))
        log->failed = !fork_log_rotate(log, now);
    if (!log->failed && bytes <= FORK_LOG_BYTES) {
        if (fwrite(line, 1, bytes, log->stream) != bytes || fflush(log->stream))
            log->failed = true;
        else log->bytes += bytes;
    }
    LeaveCriticalSection(&log->lock);
}

static void fork_log_close(fork_log_t *log)
{
    if (log->stream) fclose(log->stream);
    CloseHandle(log->allocation);
    DeleteCriticalSection(&log->lock);
    free(log->directory);
}
#endif

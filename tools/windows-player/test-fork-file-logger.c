/* Native Windows contract test for the production retention/writer code. */
#include <assert.h>
#include <stdbool.h>
#include <string.h>
#include "../../modules/logger/fork_file.h"

static unsigned count_logs(const wchar_t *directory, uint64_t now)
{
    wchar_t pattern[1024];
    swprintf(pattern, 1024, L"%ls\\vlc-*.log", directory);
    WIN32_FIND_DATAW data;
    HANDLE search = FindFirstFileW(pattern, &data);
    unsigned count = 0;
    if (search == INVALID_HANDLE_VALUE) return 0;
    do {
        uint64_t created;
        if (!fork_log_name(data.cFileName, &created)) continue;
        assert(now < created || now - created < FORK_LOG_RETENTION);
        uint64_t bytes = ((uint64_t)data.nFileSizeHigh << 32) | data.nFileSizeLow;
        assert(bytes <= FORK_LOG_BYTES);
        ++count;
    } while (FindNextFileW(search, &data));
    FindClose(search);
    assert(count <= FORK_LOG_FILES);
    return count;
}

static void fixture(const wchar_t *directory, const wchar_t *name)
{
    wchar_t path[1024];
    swprintf(path, 1024, L"%ls\\%ls", directory, name);
    HANDLE file = CreateFileW(path, GENERIC_WRITE, FILE_SHARE_READ, NULL,
                              CREATE_NEW, FILE_ATTRIBUTE_NORMAL, NULL);
    assert(file != INVALID_HANDLE_VALUE);
    DWORD written;
    assert(WriteFile(file, "fixture", 7, &written, NULL) && written == 7);
    CloseHandle(file);
}

int wmain(int argc, wchar_t **argv)
{
    if (argc == 3 && !wcscmp(argv[1], L"--stress")) {
        fork_log_t writer;
        assert(fork_log_open(&writer, argv[2]));
        char chunk[65536];
        memset(chunk, 'C', sizeof(chunk));
        for (unsigned i=0; i<160; ++i)
            fork_log_write(&writer, chunk, sizeof(chunk), fork_log_now());
        assert(!writer.failed);
        fork_log_close(&writer);
        return 0;
    }
    assert(argc == 2);
    assert(CreateDirectoryW(argv[1], NULL));
    wchar_t retention[1024], rotation[1024], concurrent[1024], blocked[1024];
    swprintf(retention, 1024, L"%ls\\retention", argv[1]);
    swprintf(rotation, 1024, L"%ls\\rotation", argv[1]);
    swprintf(concurrent, 1024, L"%ls\\concurrent", argv[1]);
    swprintf(blocked, 1024, L"%ls\\unwritable", argv[1]);
    assert(CreateDirectoryW(retention, NULL));
    uint64_t now = fork_log_now();
    wchar_t stale[96];
    swprintf(stale, 96, L"vlc-%020llu-%010lu-%06u.log",
             (unsigned long long)(now-FORK_LOG_RETENTION), 123ul, 0u);
    fixture(retention, stale);
    fixture(retention, L"personal.log");
    fixture(retention, L"vlc-not-a-generated-log.log");
    fork_log_t log;
    assert(fork_log_open(&log, retention));
    fork_log_write(&log, "startup contract\n", 17, now);
    assert(count_logs(retention, now) == 1);
    fork_log_close(&log);
    wchar_t preserved[1024];
    swprintf(preserved, 1024, L"%ls\\personal.log", retention);
    assert(GetFileAttributesW(preserved) != INVALID_FILE_ATTRIBUTES);
    swprintf(preserved, 1024, L"%ls\\vlc-not-a-generated-log.log", retention);
    assert(GetFileAttributesW(preserved) != INVALID_FILE_ATTRIBUTES);

    assert(fork_log_open(&log, rotation));
    char chunk[65536];
    memset(chunk, 'X', sizeof(chunk));
    for (unsigned i=0; i<700; ++i)
        fork_log_write(&log, chunk, sizeof(chunk), now);
    assert(!log.failed && count_logs(rotation, now) == FORK_LOG_FILES);
    uint64_t later = now + FORK_LOG_RETENTION + FORK_LOG_DAY;
    fork_log_write(&log, "next day\n", 9, later);
    assert(!log.failed && count_logs(rotation, later) == 1);
    fork_log_close(&log);

    fork_log_t writers[FORK_LOG_FILES];
    for (unsigned i=0; i<FORK_LOG_FILES; ++i) {
        assert(fork_log_open(&writers[i], concurrent));
        fork_log_write(&writers[i], "active\n", 7, fork_log_now());
    }
    fork_log_t ninth;
    assert(!fork_log_open(&ninth, concurrent));
    for (unsigned i=0; i<FORK_LOG_FILES; ++i) fork_log_close(&writers[i]);
    assert(fork_log_open(&ninth, concurrent));
    fork_log_close(&ninth);
    assert(count_logs(concurrent, fork_log_now()) == FORK_LOG_FILES);
    fixture(argv[1], L"unwritable");
    assert(!fork_log_open(&log, blocked));
    puts("PASS:72h expiry, daily/4MiB rotation,32MiB bound, active-writer protection, unrelated files and unwritable destination");
    return 0;
}

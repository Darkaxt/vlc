/* Explicit Windows C API export boundary for the pinned SPIRV-Cross build.
 * This is supplied through GCC -include, avoiding shell quoting of declspec. */
#pragma once
#ifndef _WIN32
# error This header belongs only to the Windows SPIRV-Cross DLL build
#endif
#define SPVC_PUBLIC_API __declspec(dllexport)

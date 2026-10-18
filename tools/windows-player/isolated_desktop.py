# Task-owned hidden Windows desktop. Never calls SwitchDesktop or sends OS input.
import ctypes, uuid, msvcrt, os, subprocess, re
from ctypes import wintypes as W

u = ctypes.WinDLL("user32", use_last_error=True)
k = ctypes.WinDLL("kernel32", use_last_error=True)
u.CreateDesktopW.argtypes = [W.LPCWSTR, W.LPCWSTR, W.LPVOID, W.DWORD, W.DWORD, W.LPVOID]
u.CreateDesktopW.restype = W.HANDLE
u.CloseDesktop.argtypes = [W.HANDLE]
u.OpenDesktopW.argtypes = [W.LPCWSTR, W.DWORD, W.BOOL, W.DWORD]
u.OpenDesktopW.restype = W.HANDLE
u.OpenInputDesktop.argtypes = [W.DWORD, W.BOOL, W.DWORD]
u.OpenInputDesktop.restype = W.HANDLE
u.GetUserObjectInformationW.argtypes = [
    W.HANDLE,
    ctypes.c_int,
    W.LPVOID,
    W.DWORD,
    ctypes.POINTER(W.DWORD),
]


class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ("cb", W.DWORD),
        ("lpReserved", W.LPWSTR),
        ("lpDesktop", W.LPWSTR),
        ("lpTitle", W.LPWSTR),
        ("dwX", W.DWORD),
        ("dwY", W.DWORD),
        ("dwXSize", W.DWORD),
        ("dwYSize", W.DWORD),
        ("dwXCountChars", W.DWORD),
        ("dwYCountChars", W.DWORD),
        ("dwFillAttribute", W.DWORD),
        ("dwFlags", W.DWORD),
        ("wShowWindow", W.WORD),
        ("cbReserved2", W.WORD),
        ("lpReserved2", W.LPVOID),
        ("hStdInput", W.HANDLE),
        ("hStdOutput", W.HANDLE),
        ("hStdError", W.HANDLE),
    ]


class PROCESSINFO(ctypes.Structure):
    _fields_ = [
        ("hProcess", W.HANDLE),
        ("hThread", W.HANDLE),
        ("dwProcessId", W.DWORD),
        ("dwThreadId", W.DWORD),
    ]


k.CreateProcessW.argtypes = [
    W.LPCWSTR,
    W.LPWSTR,
    W.LPVOID,
    W.LPVOID,
    W.BOOL,
    W.DWORD,
    W.LPVOID,
    W.LPCWSTR,
    ctypes.POINTER(STARTUPINFO),
    ctypes.POINTER(PROCESSINFO),
]
k.CreateProcessW.restype = W.BOOL
k.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
k.WaitForSingleObject.restype = W.DWORD
k.GetExitCodeProcess.argtypes = [W.HANDLE, ctypes.POINTER(W.DWORD)]
k.CloseHandle.argtypes = [W.HANDLE]


def input_desktop():
    h = u.OpenInputDesktop(0, False, 1)
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        b = ctypes.create_unicode_buffer(256)
        n = W.DWORD()
        if not u.GetUserObjectInformationW(h, 2, b, ctypes.sizeof(b), ctypes.byref(n)):
            raise ctypes.WinError(ctypes.get_last_error())
        return b.value
    finally:
        u.CloseDesktop(h)


class IsolatedProcess:
    def __init__(self, args, cwd, env, stdout, stderr, *, desktop_name=None):
        self.before = input_desktop()
        self.desktop_name = desktop_name or ("VLC-S2-" + uuid.uuid4().hex)
        if not re.fullmatch(r"VLC-S2-[0-9a-f]{32}", self.desktop_name) or self.desktop_name == self.before:
            raise ValueError("Expected an owned inactive VLC test desktop")
        self.desktop = (u.OpenDesktopW(self.desktop_name, 0, False, 0x1FF) if desktop_name
                        else u.CreateDesktopW(self.desktop_name, None, None, 0, 0x1FF, None))
        if not self.desktop:
            raise ctypes.WinError(ctypes.get_last_error())
        si = STARTUPINFO()
        si.cb = ctypes.sizeof(si)
        si.lpDesktop = "winsta0\\" + self.desktop_name
        si.dwFlags = 0x100 | 0x80
        handles = [msvcrt.get_osfhandle(f.fileno()) for f in [stdout, stderr]]
        for h in handles:
            os.set_handle_inheritable(h, True)
        si.hStdOutput, si.hStdError = handles
        block = ctypes.create_unicode_buffer(
            "".join(key + "=" + val + "\0" for key, val in sorted(env.items())) + "\0"
        )
        pi = PROCESSINFO()
        try:
            if not k.CreateProcessW(
                str(args[0]),
                ctypes.create_unicode_buffer(subprocess.list2cmdline(args)),
                None,
                None,
                True,
                0x08000000 | 0x400,
                block,
                str(cwd),
                ctypes.byref(si),
                ctypes.byref(pi),
            ):
                raise ctypes.WinError(ctypes.get_last_error())
        except:
            u.CloseDesktop(self.desktop)
            raise
        finally:
            for h in handles:
                os.set_handle_inheritable(h, False)
        k.CloseHandle(pi.hThread)
        self.handle = pi.hProcess
        self.pid = pi.dwProcessId

    def wait(self):
        if k.WaitForSingleObject(self.handle, 0xFFFFFFFF) != 0:
            raise ctypes.WinError(ctypes.get_last_error())
        code = W.DWORD()
        if not k.GetExitCodeProcess(self.handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        k.CloseHandle(self.handle)
        if not u.CloseDesktop(self.desktop):
            raise ctypes.WinError(ctypes.get_last_error())
        assert input_desktop() == self.before, "Input desktop unexpectedly changed"
        return code.value

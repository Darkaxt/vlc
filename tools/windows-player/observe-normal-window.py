"""Passive window-show/location observation on this process's startup desktop."""
import argparse
import ctypes
from ctypes import wintypes as W
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--binding', type=Path, required=True)
p.add_argument('--result', type=Path, required=True)
p.add_argument('--ready-event', required=True)
p.add_argument('--bound-event', required=True)
p.add_argument('--cancel-event', required=True)
p.add_argument('--executable', type=Path, required=True)
p.add_argument('--expected-icon',type=Path,help='Verify the owned Qt main window icon against this maintained PNG')
a = p.parse_args()
if a.expected_icon:
    from app_icon_checks import window_icon
    assert a.expected_icon.is_file()
u = ctypes.WinDLL('user32', use_last_error=True)
k = ctypes.WinDLL('kernel32', use_last_error=True)
k.OpenEventW.argtypes = [W.DWORD, W.BOOL, W.LPCWSTR]
k.OpenEventW.restype = W.HANDLE
k.SetEvent.argtypes = [W.HANDLE]
k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
k.OpenProcess.restype = W.HANDLE
k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, ctypes.POINTER(W.DWORD)]
k.CloseHandle.argtypes = [W.HANDLE]
psapi = ctypes.WinDLL('psapi', use_last_error=True)
psapi.GetModuleFileNameExW.argtypes = [W.HANDLE, W.HANDLE, W.LPWSTR, W.DWORD]
callback_type = ctypes.WINFUNCTYPE(None, W.HANDLE, W.DWORD, W.HWND, W.LONG, W.LONG, W.DWORD, W.DWORD)
u.SetWinEventHook.argtypes = [W.DWORD, W.DWORD, W.HANDLE, callback_type, W.DWORD, W.DWORD, W.DWORD]
u.SetWinEventHook.restype = W.HANDLE
u.UnhookWinEvent.argtypes = [W.HANDLE]
u.GetWindowThreadProcessId.argtypes = [W.HWND, ctypes.POINTER(W.DWORD)]
u.GetWindowRect.argtypes = [W.HWND, ctypes.POINTER(W.RECT)]
u.IsWindowVisible.argtypes = [W.HWND]
u.GetClassNameW.argtypes = [W.HWND, W.LPWSTR, ctypes.c_int]
u.GetWindowTextW.argtypes = [W.HWND, W.LPWSTR, ctypes.c_int]
u.GetWindowLongPtrW.argtypes = [W.HWND, ctypes.c_int]
u.GetWindowLongPtrW.restype = ctypes.c_ssize_t
u.GetClassLongPtrW.argtypes = [W.HWND, ctypes.c_int]
u.GetClassLongPtrW.restype = ctypes.c_size_t
u.GetAncestor.argtypes=[W.HWND,W.UINT]
u.GetAncestor.restype=W.HWND
u.GetWindow.argtypes=[W.HWND,W.UINT]
u.GetWindow.restype=W.HWND
u.GetLayeredWindowAttributes.argtypes = [W.HWND, ctypes.POINTER(W.DWORD), ctypes.POINTER(W.BYTE), ctypes.POINTER(W.DWORD)]
u.GetForegroundWindow.restype = W.HWND
u.SetThreadDpiAwarenessContext.argtypes = [W.HANDLE]
u.SetThreadDpiAwarenessContext.restype = W.HANDLE
u.MsgWaitForMultipleObjects.argtypes = [W.DWORD, ctypes.POINTER(W.HANDLE), W.BOOL, W.DWORD, W.DWORD]
u.MsgWaitForMultipleObjects.restype = W.DWORD
u.PeekMessageW.argtypes = [ctypes.POINTER(W.MSG), W.HWND, W.UINT, W.UINT, W.UINT]
u.TranslateMessage.argtypes = [ctypes.POINTER(W.MSG)]
u.DispatchMessageW.argtypes = [ctypes.POINTER(W.MSG)]

ready, bound, cancel = [k.OpenEventW(0x100002, False, name)
    for name in (a.ready_event, a.bound_event, a.cancel_event)]
assert ready and bound and cancel
records, errors = [], []
icons={}
process = None
target = None
hooks = []
previous_dpi = u.SetThreadDpiAwarenessContext(W.HANDLE(-4))
assert previous_dpi

def image(pid):
    handle = k.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        buffer, count = ctypes.create_unicode_buffer(32768), W.DWORD(32768)
        if k.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(count)):
            return Path(buffer.value).resolve()
    finally:
        k.CloseHandle(handle)

@callback_type
def event(hook, kind, window, object_id, child_id, thread, timestamp):
    try:
        if not window or (kind != 3 and (object_id != 0 or child_id != 0)):
            return
        pid = W.DWORD()
        u.GetWindowThreadProcessId(window, ctypes.byref(pid))
        if (target is not None and pid.value != target) or image(pid.value) != a.executable.resolve():
            return
        rectangle = W.RECT()
        if not u.GetWindowRect(window, ctypes.byref(rectangle)):
            return
        class_name, title = ctypes.create_unicode_buffer(256), ctypes.create_unicode_buffer(512)
        u.GetClassNameW(window, class_name, len(class_name))
        u.GetWindowTextW(window, title, len(title))
        extended = u.GetWindowLongPtrW(window, -20)
        color, alpha, layered_flags = W.DWORD(), W.BYTE(), W.DWORD()
        layered = bool(u.GetLayeredWindowAttributes(window, ctypes.byref(color), ctypes.byref(alpha), ctypes.byref(layered_flags)))
        module_path = None
        module = u.GetClassLongPtrW(window, -16)
        native_process = k.OpenProcess(0x400 | 0x10, False, pid.value)
        if native_process:
            try:
                module_name = ctypes.create_unicode_buffer(32768)
                if psapi.GetModuleFileNameExW(native_process, module, module_name, len(module_name)):
                    module_path = module_name.value
            finally:
                k.CloseHandle(native_process)
        record = {'pid': pid.value, 'event': kind, 'timestamp': timestamp,
            'class': class_name.value, 'title': title.value,
            'class_module': module_path, 'extended_style': extended,
            'layered_attributes_known': layered, 'alpha': alpha.value if layered else None,
            'layered_flags': layered_flags.value if layered else None,
            'visible': bool(u.IsWindowVisible(window)), 'foreground_owner': u.GetForegroundWindow() == window,
            'bounds': [rectangle.left, rectangle.top, rectangle.right, rectangle.bottom]}
        if (a.expected_icon and record['visible'] and class_name.value.startswith('Qt')
                and rectangle.right-rectangle.left>=320 and rectangle.bottom-rectangle.top>=200
                and u.GetAncestor(window,2)==window and not u.GetWindow(window,4)
                and str(window) not in icons):
            icons[str(window)]=window_icon(window,pid.value,a.expected_icon,
                a.result.parent/('native-icon-'+format(window,'x')+'.png'))
        if record not in records:
            records.append(record)
    except Exception as failure:
        errors.append(repr(failure))

def messages():
    message = W.MSG()
    while u.PeekMessageW(ctypes.byref(message), None, 0, 0, 1):
        u.TranslateMessage(ctypes.byref(message))
        u.DispatchMessageW(ctypes.byref(message))

result = {'schema': 'vlc_redesign.owned_window_events.v1', 'events': records,
    'errors': errors, 'passive_observation_only': True,'native_window_icons':icons}
try:
    hooks = [u.SetWinEventHook(first, last, None, event, 0, 0, 2)
        for first, last in ((3, 3), (0x8002, 0x800B))]
    assert all(hooks)
    # Initialize the observer's message queue before declaring hook readiness.
    messages()
    assert k.SetEvent(ready)
    while True:
        handles = (W.HANDLE * 2)(process if process else bound, cancel)
        outcome = u.MsgWaitForMultipleObjects(2, handles, False, 0xFFFFFFFF, 0x04FF)
        if outcome == 2:
            messages()
        elif outcome == 1:
            result['cancelled'] = True
            break
        elif outcome == 0 and process is None:
            binding = json.loads(a.binding.read_text())
            assert Path(binding['executable']).resolve() == a.executable.resolve()
            target = binding['pid']
            process = k.OpenProcess(0x100000 | 0x1000, False, target)
            assert process, ctypes.get_last_error()
        elif outcome == 0:
            messages()
            code = W.DWORD()
            k.GetExitCodeProcess.argtypes = [W.HANDLE, ctypes.POINTER(W.DWORD)]
            assert k.GetExitCodeProcess(process, ctypes.byref(code))
            result.update(target_pid=target, target_exit_code=code.value)
            break
        else:
            raise ctypes.WinError(ctypes.get_last_error())
finally:
    for hook in hooks:
        if hook:
            u.UnhookWinEvent(hook)
    if process:
        k.CloseHandle(process)
    for handle in (ready, bound, cancel):
        k.CloseHandle(handle)
    assert u.SetThreadDpiAwarenessContext(previous_dpi)
    a.result.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')

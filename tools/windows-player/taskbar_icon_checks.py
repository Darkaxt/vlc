"""Read classic Windows taskbar buttons and their actual composed icon pixels.

MSAA exposes the button names that this host's UIA pane-only tree omits. No
activation, input, pinning, property writes or icon-cache changes are performed.
"""
import ctypes as C
from ctypes import wintypes as W
import hashlib
from pathlib import Path
import uuid
from PIL import Image, ImageChops, ImageGrab, ImageStat


def running_buttons():
    u=C.WinDLL('user32');ole=C.WinDLL('ole32');aut=C.WinDLL('oleaut32');acc=C.WinDLL('oleacc')
    class GUID(C.Structure):_fields_=[('bytes',C.c_ubyte*16)]
    iid=GUID((C.c_ubyte*16).from_buffer_copy(uuid.UUID('618736e0-3c3d-11cf-810c-00aa00389b71').bytes_le))
    class VALUE(C.Union):_fields_=[('integer',C.c_long),('pointer',C.c_void_p),('pad',C.c_ubyte*16)]
    class VARIANT(C.Structure):_fields_=[('vt',W.WORD),('r1',W.WORD),('r2',W.WORD),('r3',W.WORD),('value',VALUE)]
    def method(pointer,index,result,*arguments):
        table=C.cast(pointer,C.POINTER(C.POINTER(C.c_void_p))).contents
        return C.WINFUNCTYPE(result,C.c_void_p,*arguments)(table[index])
    aut.SysFreeString.argtypes=[C.c_void_p];aut.VariantClear.argtypes=[C.POINTER(VARIANT)]
    acc.AccessibleObjectFromWindow.argtypes=[W.HWND,W.DWORD,C.POINTER(GUID),C.POINTER(C.c_void_p)]
    acc.AccessibleChildren.argtypes=[C.c_void_p,C.c_long,C.c_long,C.POINTER(VARIANT),C.POINTER(C.c_long)]
    u.SetThreadDpiAwarenessContext.argtypes=[W.HANDLE];u.SetThreadDpiAwarenessContext.restype=W.HANDLE
    u.GetClassNameW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
    callback=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    u.EnumChildWindows.argtypes=[W.HWND,callback,W.LPARAM];u.EnumWindows.argtypes=[callback,W.LPARAM]
    windows=[];records=[]
    @callback
    def child(hwnd,unused):
        name=C.create_unicode_buffer(256);u.GetClassNameW(hwnd,name,len(name))
        if name.value=='MSTaskListWClass':windows.append(hwnd)
        return True
    @callback
    def window(hwnd,unused):
        name=C.create_unicode_buffer(256);u.GetClassNameW(hwnd,name,len(name))
        if name.value in ('Shell_TrayWnd','Shell_SecondaryTrayWnd'):u.EnumChildWindows(hwnd,child,0)
        return True
    def inspect(pointer,childid,depth,hwnd):
        text=C.c_void_p();identity=VARIANT();identity.vt=3;identity.value.integer=childid
        hr=method(pointer,10,C.c_long,VARIANT,C.POINTER(C.c_void_p))(pointer,identity,C.byref(text))
        name=C.wstring_at(text.value) if hr>=0 and text.value else None
        if text.value:aut.SysFreeString(text)
        x,y,width,height=[C.c_long() for _ in range(4)]
        hr=method(pointer,22,C.c_long,*([C.POINTER(C.c_long)]*4),VARIANT)(pointer,C.byref(x),C.byref(y),C.byref(width),C.byref(height),identity)
        if hr>=0 and width.value>0 and height.value>0:
            records.append({'tasklist':hex(hwnd),'name':name,'bounds':[x.value,y.value,width.value,height.value]})
        if childid or depth>=3:return
        count=C.c_long();hr=method(pointer,8,C.c_long,C.POINTER(C.c_long))(pointer,C.byref(count))
        assert hr>=0 and 0<=count.value<1024
        if not count.value:return
        children=(VARIANT*count.value)();obtained=C.c_long()
        assert acc.AccessibleChildren(pointer,0,count.value,children,C.byref(obtained))>=0
        for value in children[:obtained.value]:
            try:
                if value.vt==3:inspect(pointer,value.value.integer,depth+1,hwnd)
                elif value.vt==9:
                    accessible=C.c_void_p()
                    query=method(value.value.pointer,0,C.c_long,C.POINTER(GUID),C.POINTER(C.c_void_p))
                    if query(value.value.pointer,C.byref(iid),C.byref(accessible))>=0:
                        try:inspect(accessible,0,depth+1,hwnd)
                        finally:method(accessible,2,W.ULONG)(accessible)
            finally:aut.VariantClear(C.byref(value))
    assert ole.CoInitializeEx(None,2)>=0
    previous=u.SetThreadDpiAwarenessContext(W.HANDLE(-4));assert previous
    try:
        assert u.EnumWindows(window,0)
        for hwnd in windows:
            pointer=C.c_void_p()
            hr=acc.AccessibleObjectFromWindow(hwnd,0xfffffffc,C.byref(iid),C.byref(pointer))
            assert hr>=0,('Taskbar accessibility read failed',hex(hr&0xffffffff))
            try:inspect(pointer,0,0,hwnd)
            finally:method(pointer,2,W.ULONG)(pointer)
    finally:
        u.SetThreadDpiAwarenessContext(previous);ole.CoUninitialize()
    return records


def capture_mpv_button(expected_ico, output):
    """Return None while the button is absent; never wait or change the Shell."""
    matches=[row for row in running_buttons() if (row['name'] or '').startswith('MPV Media Player - ')]
    if not matches:return None
    assert len(matches)==1,('Ambiguous MPV taskbar group',matches)
    row=matches[0];x,y,width,height=row['bounds']
    assert width<=200 and height<=150,'Reject non-button/oversized capture'
    u=C.WinDLL('user32');u.SetThreadDpiAwarenessContext.argtypes=[W.HANDLE];u.SetThreadDpiAwarenessContext.restype=W.HANDLE
    previous=u.SetThreadDpiAwarenessContext(W.HANDLE(-4));assert previous
    try:picture=ImageGrab.grab(bbox=(x,y,x+width,y+height),all_screens=True).convert('RGB')
    finally:u.SetThreadDpiAwarenessContext(previous)
    native=Image.open(expected_ico);best=None
    for size in sorted(native.ico.sizes()):
        if size[0]>width or size[1]>height:continue
        frame=native.ico.getimage(size).convert('RGBA');mask=frame.getchannel('A').point(lambda alpha:255 if alpha>=240 else 0)
        for left in range(max(0,(width-size[0])//2-6),min(width-size[0],(width-size[0])//2+6)+1):
            for top in range(max(0,(height-size[1])//2-8),min(height-size[1],(height-size[1])//2+8)+1):
                crop=picture.crop((left,top,left+size[0],top+size[1]))
                error=sum(ImageStat.Stat(ImageChops.difference(crop,frame.convert('RGB')),mask).mean)/3
                if best is None or error<best['mean_rgb_error']:best={'size':size,'origin':[left,top],'mean_rgb_error':error}
    picture.save(output)
    assert best and best['mean_rgb_error']<18,('Actual taskbar pixels differ from extracted MPV icon',best)
    return {'button':row,'match':best,'image':str(output),'image_sha256':hashlib.sha256(Path(output).read_bytes()).hexdigest(),
        'reference_ico_sha256':hashlib.sha256(Path(expected_ico).read_bytes()).hexdigest(),'actual_composed_pixels':True}

"""Read-only PE and owned native-window icon checks for diagnostic and shipped builds."""
import ctypes
from ctypes import wintypes as W
import hashlib
from pathlib import Path
import struct
import pefile
from PIL import Image


def executable_icon(executable, expected_ico):
    data=Path(expected_ico).read_bytes()
    reserved,kind,count=struct.unpack_from('<HHH',data)
    assert (reserved,kind,count)==(0,1,9)
    expected={}
    for index in range(count):
        width,height,colors,unused,planes,bits,size,offset=struct.unpack_from('<BBBBHHII',data,6+16*index)
        expected[(width or 256,height or 256)]=hashlib.sha256(data[offset:offset+size]).hexdigest()
    with pefile.PE(str(executable)) as pe:
        resources,groups={},[]
        for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if kind.id not in (3,14): continue
            for item in kind.directory.entries:
                for language in item.directory.entries:
                    entry=language.data.struct
                    payload=pe.get_data(entry.OffsetToData,entry.Size)
                    if kind.id==3: resources[item.id]=payload
                    else: groups.append(payload)
        matched=False
        for group in groups:
            observed={}
            for index in range(struct.unpack_from('<H',group,4)[0]):
                width,height,colors,unused,planes,bits,size,identity=struct.unpack_from('<BBBBHHIH',group,6+14*index)
                payload=resources[identity]
                assert len(payload)==size
                observed[(width or 256,height or 256)]=hashlib.sha256(payload).hexdigest()
            matched |= observed==expected
        assert matched,'Packaged executable does not contain the flat multi-size cone'
    return {'sizes':sorted(width for width,height in expected),'payloads_match_source':True,
        'expected_ico_sha256':hashlib.sha256(data).hexdigest()}


def window_icon(hwnd, expected_pid, expected_png, output):
    """Resolve the native root and read its HICON without activation or OS input."""
    u=ctypes.WinDLL('user32',use_last_error=True)
    u.GetAncestor.argtypes=[W.HWND,W.UINT]
    u.GetAncestor.restype=W.HWND
    root=u.GetAncestor(hwnd,2)
    assert root,'Qt surface has no native root window'
    u.GetWindowThreadProcessId.argtypes=[W.HWND,ctypes.POINTER(W.DWORD)]
    pid=W.DWORD()
    u.GetWindowThreadProcessId(root,ctypes.byref(pid))
    assert pid.value==expected_pid,'Native root belongs to a different process'
    u.SendMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
    u.SendMessageW.restype=W.LPARAM
    icon=u.SendMessageW(root,0x7F,1,0)  # WM_GETICON / ICON_BIG
    origin='WM_GETICON/ICON_BIG'
    if not icon:
        # This is Windows' documented class-icon resolution, not a substitute
        # image. Both branches read the actual icon used by the native window.
        u.GetClassLongPtrW.argtypes=[W.HWND,ctypes.c_int]
        u.GetClassLongPtrW.restype=ctypes.c_size_t
        icon=u.GetClassLongPtrW(root,-14)
        origin='GCLP_HICON'
    assert icon,'Running player has no big window/application icon'
    class IconInfo(ctypes.Structure):
        _fields_=[('icon',W.BOOL),('x',W.DWORD),('y',W.DWORD),('mask',W.HBITMAP),('color',W.HBITMAP)]
    class Bitmap(ctypes.Structure):
        _fields_=[('type',W.LONG),('width',W.LONG),('height',W.LONG),('row_bytes',W.LONG),('planes',W.WORD),('bits',W.WORD),('data',W.LPVOID)]
    class Header(ctypes.Structure):
        _fields_=[('size',W.DWORD),('width',W.LONG),('height',W.LONG),('planes',W.WORD),('bits',W.WORD),('compression',W.DWORD),('image_size',W.DWORD),('xppm',W.LONG),('yppm',W.LONG),('used',W.DWORD),('important',W.DWORD)]
    gdi=ctypes.WinDLL('gdi32',use_last_error=True)
    u.GetIconInfo.argtypes=[W.HANDLE,ctypes.POINTER(IconInfo)]
    gdi.GetObjectW.argtypes=[W.HANDLE,ctypes.c_int,W.LPVOID]
    gdi.CreateCompatibleDC.argtypes=[W.HDC]
    gdi.CreateCompatibleDC.restype=W.HDC
    gdi.GetDIBits.argtypes=[W.HDC,W.HBITMAP,W.UINT,W.UINT,W.LPVOID,W.LPVOID,W.UINT]
    gdi.DeleteObject.argtypes=[W.HANDLE]
    gdi.DeleteDC.argtypes=[W.HDC]
    info,bitmap=IconInfo(),Bitmap()
    assert u.GetIconInfo(W.HANDLE(icon),ctypes.byref(info))
    dc=gdi.CreateCompatibleDC(None)
    try:
        assert gdi.GetObjectW(info.color,ctypes.sizeof(bitmap),ctypes.byref(bitmap))
        header=Header(ctypes.sizeof(Header),bitmap.width,-bitmap.height,1,32)
        pixels=ctypes.create_string_buffer(bitmap.width*bitmap.height*4)
        assert gdi.GetDIBits(dc,info.color,0,bitmap.height,pixels,ctypes.byref(header),0)==bitmap.height
        image=Image.frombytes('RGBA',(bitmap.width,bitmap.height),pixels.raw,'raw','BGRA')
        image.save(output)
        opaque=[pixel for pixel in image.get_flattened_data() if pixel[3]==255]
        assert opaque and all(max(abs(pixel[index]-channel) for index,channel in enumerate((211,121,24)))<=2 for pixel in opaque),'Native icon retains the upstream artwork'
        assert any(pixel[3]==0 for pixel in image.get_flattened_data()),'Native icon lost transparency'
        expected=Image.open(expected_png).convert('RGBA').resize(image.size,Image.Resampling.LANCZOS)
        observed_mask={index for index,pixel in enumerate(image.get_flattened_data()) if pixel[3]>=128}
        expected_mask={index for index,pixel in enumerate(expected.get_flattened_data()) if pixel[3]>=128}
        overlap=len(observed_mask & expected_mask)/len(observed_mask | expected_mask)
        assert overlap>=.94,('Native icon shape differs from the in-app cone',overlap)
        return {'size':image.size,'root_window':format(root,'x'),'origin':origin,'flat_cone':True,
            'transparent':True,'alpha_shape_overlap':overlap,'expected_png_sha256':hashlib.sha256(Path(expected_png).read_bytes()).hexdigest()}
    finally:
        if info.mask:gdi.DeleteObject(info.mask)
        if info.color:gdi.DeleteObject(info.color)
        if dc:gdi.DeleteDC(dc)

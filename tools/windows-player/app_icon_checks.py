"""Read-only PE and owned native-window icon checks for diagnostic and shipped builds."""
import ctypes
from ctypes import wintypes as W
import hashlib
from pathlib import Path
import struct
import uuid
import pefile
from PIL import Image, ImageChops, ImageStat


def qml_mpv_icon_pixels(capture, expected_ico, pixel_offset=(0,0)):
    """Reject decoding a larger native frame back down to24px before DPI scaling."""
    actual=Image.open(capture).convert('RGB')
    native=Image.open(expected_ico)
    size=next(size for size in sorted(native.ico.sizes()) if size[0]>=actual.width)
    reference=native.ico.getimage(size).convert('RGBA').resize(actual.size,Image.Resampling.LANCZOS)
    # The capture crops at rounded physical coordinates; a fractional item
    # origin with nearest texture sampling starts at floor(origin). Apply that
    # measured phase, never a searched alignment or a relaxed color threshold.
    assert all(value in (-1,0) for value in pixel_offset),pixel_offset
    if pixel_offset!=(0,0):
        aligned=Image.new('RGBA',actual.size)
        aligned.paste(reference,pixel_offset)
        reference=aligned
    mask=reference.getchannel('A').point(lambda alpha:255 if alpha>=240 else 0)
    error=sum(ImageStat.Stat(ImageChops.difference(actual,reference.convert('RGB')),mask).mean)/3
    assert error<10,('QML icon lost the original native frame detail',actual.size,error)
    return {'physical_size':actual.size,'reference_frame':size,'mean_rgb_error':error,'capture_pixel_offset':pixel_offset,
        'native_detail_preserved':True,'capture_sha256':hashlib.sha256(Path(capture).read_bytes()).hexdigest()}


def shell_identity(hwnd, expected_pid, engine, executable, expected_mpv_icon, *, custom_resource=None):
    """Read the actual owned window's Shell identity, distinct from WM_GETICON."""
    u=ctypes.WinDLL('user32',use_last_error=True)
    u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
    root=u.GetAncestor(hwnd,2)
    u.GetWindowThreadProcessId.argtypes=[W.HWND,ctypes.POINTER(W.DWORD)]
    pid=W.DWORD();u.GetWindowThreadProcessId(root,ctypes.byref(pid))
    assert pid.value==expected_pid,'Shell identity target belongs to another process'
    class GUID(ctypes.Structure):
        _fields_=[('data',ctypes.c_ubyte*16)]
        @classmethod
        def parse(cls,text):return cls((ctypes.c_ubyte*16).from_buffer_copy(uuid.UUID(text).bytes_le))
    class KEY(ctypes.Structure):_fields_=[('format',GUID),('pid',W.DWORD)]
    class VALUE(ctypes.Union):_fields_=[('string',W.LPWSTR),('bytes',ctypes.c_ubyte*16)]
    class VARIANT(ctypes.Structure):_fields_=[('type',W.USHORT),('a',W.USHORT),('b',W.USHORT),('c',W.USHORT),('value',VALUE)]
    shell=ctypes.WinDLL('shell32');ole=ctypes.WinDLL('ole32')
    ole.CoInitializeEx.argtypes=[W.LPVOID,W.DWORD];ole.PropVariantClear.argtypes=[ctypes.POINTER(VARIANT)]
    shell.SHGetPropertyStoreForWindow.argtypes=[W.HWND,ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)]
    assert ole.CoInitializeEx(None,2)>=0
    pointer=ctypes.c_void_p();properties={}
    try:
        iid=GUID.parse('886d8eeb-8cf2-4446-8d02-cdba1dbdcf99')
        assert shell.SHGetPropertyStoreForWindow(root,ctypes.byref(iid),ctypes.byref(pointer))>=0
        table=ctypes.cast(pointer,ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        get=ctypes.WINFUNCTYPE(ctypes.c_long,ctypes.c_void_p,ctypes.POINTER(KEY),ctypes.POINTER(VARIANT))(table[5])
        release=ctypes.WINFUNCTYPE(W.ULONG,ctypes.c_void_p)(table[2])
        try:
            for name,identity in (('id',5),('command',2),('icon',3),('name',4)):
                value=VARIANT();key=KEY(GUID.parse('9f4c2855-9f79-4b39-a8d0-e1d42de1d5f3'),identity)
                assert get(pointer,ctypes.byref(key),ctypes.byref(value))>=0
                try:
                    assert value.type in (0,31),(name,value.type)
                    properties[name]=value.value.string if value.type==31 else None
                finally:ole.PropVariantClear(ctypes.byref(value))
        finally:release(pointer)
    finally:ole.CoUninitialize()
    if engine=='mpv' or custom_resource:
        assert properties['id']=='Darkaxt.ModernVLC.'+engine.upper(),('Taskbar retains the wrong engine identity',properties)
        executable=Path(executable)
        expected_command='"'+str(executable)+'" --qt-playback-engine='+engine
        assert properties['command']==expected_command,properties
        assert properties['name']==engine.upper()+' Media Player',properties
        resource=Path(custom_resource) if custom_resource else executable.parent/'mpv.ico'
        assert properties['icon']==str(resource)+',0',properties
        assert resource.read_bytes()==Path(expected_mpv_icon).read_bytes(),'Shell resource differs from the verified engine artwork'
    else:
        assert engine=='vlc' and all(value is None for value in properties.values()),('VLC did not restore its original Shell grouping',properties)
    return {'root_window':format(root,'x'),'engine':engine,'properties':properties,'shell_resource_verified':True}


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


def window_icon(hwnd, expected_pid, expected_png, output, *, custom=False):
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
        mpv=Path(expected_png).name=='mpv.ico'
        if not mpv and not custom:
            assert opaque and all(max(abs(pixel[index]-channel) for index,channel in enumerate((211,121,24)))<=2 for pixel in opaque),'Native icon retains the upstream artwork'
        assert any(pixel[3]==0 for pixel in image.get_flattened_data()),'Native icon lost transparency'
        reference=Path(expected_png)
        if reference.suffix=='.ico':
            # Compare the actual HWND with the original native ICO frame,
            # rather than accepting any purple/circular icon.
            import json
            if not custom:
                provenance=json.loads(reference.with_name('mpv-source.json').read_text(encoding='utf-8'))
                assert hashlib.sha256(reference.read_bytes()).hexdigest() in json.dumps(provenance)
            native=Image.open(reference)
            sizes=native.ico.sizes()
            selected=image.size if image.size in sizes else min(
                (size for size in sizes if size[0]>=image.width),default=max(sizes),key=lambda size:size[0])
            expected=native.ico.getimage(selected).convert('RGBA')
        else:
            expected=Image.open(reference).convert('RGBA')
        expected=expected.resize(image.size,Image.Resampling.LANCZOS)
        observed_mask={index for index,pixel in enumerate(image.get_flattened_data()) if pixel[3]>=128}
        expected_mask={index for index,pixel in enumerate(expected.get_flattened_data()) if pixel[3]>=128}
        overlap=len(observed_mask & expected_mask)/len(observed_mask | expected_mask)
        assert overlap>=.94,('Native icon shape differs from the maintained artwork',overlap)
        if mpv or custom:
            differences=[abs(a-b) for actual,wanted in zip(image.get_flattened_data(),expected.get_flattened_data())
                if actual[3]>=240 and wanted[3]>=240 for a,b in zip(actual[:3],wanted[:3])]
            assert differences and sum(differences)/len(differences)<12,'Native icon differs from official MPV gradients/play emblem'
        return {'size':image.size,'root_window':format(root,'x'),'origin':origin,'flat_cone':not mpv,
            'official_mpv':mpv and not custom,'custom_colored':custom,
            'transparent':True,'alpha_shape_overlap':overlap,'expected_png_sha256':hashlib.sha256(Path(expected_png).read_bytes()).hexdigest()}
    finally:
        if info.mask:gdi.DeleteObject(info.mask)
        if info.color:gdi.DeleteObject(info.color)
        if dc:gdi.DeleteDC(dc)

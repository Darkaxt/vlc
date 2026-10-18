"""Inspect an explicitly instrumented local VLC instance without desktop input.

Windows directory notifications and process-exit handles provide completion;
there is no synchronization timeout, polling delay or OS input injection.
"""
from pathlib import Path
import argparse
import ctypes
from ctypes import wintypes
import json
import os
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('op', choices=['snapshot', 'click', 'move', 'drag', 'scroll', 'drop', 'key', 'widget_click', 'widget_key', 'resize', 'cancel', 'quit'])
    parser.add_argument('--target')
    parser.add_argument('--name', help='Exact accessible name of an actionable Qt Quick item')
    parser.add_argument('--item-url', help='Exact URL of one rendered queue row')
    parser.add_argument('--node', type=int)
    parser.add_argument('--capture', action='store_true')
    parser.add_argument('--button', choices=['left', 'right'], default='left')
    parser.add_argument('--fraction-x', type=float, default=0.5)
    parser.add_argument('--fraction-y', type=float, default=0.5)
    parser.add_argument('--end-x', type=float)
    parser.add_argument('--end-y', type=float)
    parser.add_argument('--key', type=lambda s: int(s, 0))
    parser.add_argument('--modifiers', type=lambda s: int(s, 0), default=0)
    parser.add_argument('--text', default='')
    parser.add_argument('--width', type=int)
    parser.add_argument('--height', type=int)
    parser.add_argument('--delta', type=int, default=-120)
    parser.add_argument('--action', type=int)
    parser.add_argument('--menu-action', help='Exact menu action label, ignoring mnemonic ampersands')
    parser.add_argument('--widget-text', help='Exact native widget text, ignoring mnemonic ampersands')
    parser.add_argument('--url', action='append', default=[])
    parser.add_argument('--await-property', choices=['selected', 'description', 'visible', 'checked', 'text', 'value', 'width', 'height', 'contentY'])
    parser.add_argument('--await-value', type=json.loads)
    parser.add_argument('--await-target')
    parser.add_argument('--await-name')
    parser.add_argument('--await-node', type=int, help='Observation node from a fresh rendered snapshot')
    parser.add_argument('--await-core', choices=['state', 'position', 'time_seconds', 'length_seconds', 'url', 'seekable'])
    parser.add_argument('--await-comparison', choices=['equal', 'at_least', 'at_most'], default='equal')
    parser.add_argument('--await-tolerance', type=float, default=0)
    args = parser.parse_args()
    session = json.loads(args.session.read_text(encoding='utf8'))
    directory = args.session.parent.resolve()
    user = ctypes.WinDLL('user32', use_last_error=True)
    user.GetForegroundWindow.restype = wintypes.HWND
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]

    def owns_foreground():
        pid = wintypes.DWORD()
        user.GetWindowThreadProcessId(user.GetForegroundWindow(), ctypes.byref(pid))
        return pid.value == session['pid']

    foreground_before = owns_foreground()
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.FindFirstChangeNotificationW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL, wintypes.DWORD]
    kernel.FindFirstChangeNotificationW.restype = wintypes.HANDLE
    kernel.FindNextChangeNotification.argtypes = [wintypes.HANDLE]
    kernel.FindCloseChangeNotification.argtypes = [wintypes.HANDLE]
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.WaitForMultipleObjects.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE), wintypes.BOOL, wintypes.DWORD]
    kernel.WaitForMultipleObjects.restype = wintypes.DWORD
    process = kernel.OpenProcess(0x100000 | 0x1000, False, session['pid'])
    if not process:
        raise ctypes.WinError(ctypes.get_last_error())
    notification = None
    try:
        executable = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(executable))
        if not kernel.QueryFullProcessImageNameW(process, 0, executable, ctypes.byref(length)):
            raise ctypes.WinError(ctypes.get_last_error())
        if Path(executable.value).resolve() != Path(session['executable']).resolve():
            raise RuntimeError('Session PID no longer identifies the recorded VLC executable')
        notification = kernel.FindFirstChangeNotificationW(str(directory), False, 0x1 | 0x8 | 0x10)
        if notification == wintypes.HANDLE(-1).value:
            notification = None
            raise ctypes.WinError(ctypes.get_last_error())
        handles = (wintypes.HANDLE * 2)(notification, process)

        def request(op, **fields):
            request_id = uuid.uuid4().hex
            command = dict(id=request_id, token=session['token'], op=op, **fields)
            pending = directory / ('pending-' + request_id + '.json')
            pending.write_text(json.dumps(command) + '\n', encoding='utf8')
            os.replace(pending, directory / ('request-' + request_id + '.json'))
            output = directory / (request_id + '.json')
            ready = directory / (request_id + '.ready')
            while not ready.exists():
                outcome = kernel.WaitForMultipleObjects(2, handles, False, 0xFFFFFFFF)
                if outcome == 0:
                    if not kernel.FindNextChangeNotification(notification):
                        raise ctypes.WinError(ctypes.get_last_error())
                elif outcome == 1:
                    if not ready.exists():
                        raise RuntimeError('VLC exited before producing this response: ' + request_id)
                else:
                    raise ctypes.WinError(ctypes.get_last_error())
            result = json.loads(output.read_text(encoding='utf8'))
            if result.get('id') != request_id:
                raise RuntimeError('Response identity mismatch')
            if result.get('status') == 'failed':
                raise RuntimeError(json.dumps({'id': request_id, 'error': result.get('error'), 'response': str(output)}))
            return output, result

        if args.await_core and args.await_property:
            parser.error('Choose either --await-core or --await-property')
        if args.op == 'snapshot' and not (args.await_property or args.await_core):
            output, result = request('snapshot', capture=args.capture)
        elif args.op in ('quit', 'cancel'):
            output, result = request(args.op)
        else:
            _, before = request('snapshot')
            fields = dict(revision=before['revision'], capture=args.capture)
            if args.op in ('click', 'move', 'drag', 'scroll', 'drop'):
                if args.target or args.name or args.item_url:
                    nodes = [n for n in before['tree'] if n['visible'] and n['enabled'] and
                             ((args.target and n['id'] == args.target) or
                              (args.name and n.get('name') == args.name and n.get('actions')) or
                              (args.item_url and n['id'] == 'delegate' and n.get('index', -1) >= 0 and n.get('url') == args.item_url))]
                    if len(nodes) != 1:
                        raise RuntimeError('Expected one visible enabled target; matched ' + str(len(nodes)))
                    fields['node'] = nodes[0]['node']
                elif args.node is not None:
                    fields['node'] = args.node
                else:
                    parser.error('Pointer events require --target or --node from a fresh snapshot')
                if not 0 <= args.fraction_x <= 1 or not 0 <= args.fraction_y <= 1:
                    parser.error('Target fractions must be within [0,1]')
                fields.update(fraction_x=args.fraction_x, fraction_y=args.fraction_y, button=args.button)
                if args.op == 'scroll':
                    fields['delta'] = args.delta
                if args.op == 'drop':
                    if not args.url:
                        parser.error('Drop requires at least one --url')
                    fields['urls'] = args.url
                if args.op == 'drag':
                    if args.end_x is None or args.end_y is None:
                        parser.error('Drag requires --end-x and --end-y in snapshot logical pixels')
                    fields.update(end_x=args.end_x, end_y=args.end_y)
            elif args.op in ('key', 'widget_key'):
                if args.key is None:
                    parser.error('Key requires --key with a Qt key code')
                fields.update(key=args.key, modifiers=args.modifiers, text=args.text)
                if args.op == 'widget_key':
                    if args.target:
                        nodes = [n for n in before['widgets'] if n['id'] == args.target and n['enabled']]
                        if len(nodes) != 1:
                            raise RuntimeError('Expected one native widget target; matched ' + str(len(nodes)))
                        fields['node'] = nodes[0]['node']
                    elif args.node is not None:
                        fields['node'] = args.node
                    else:
                        parser.error('Widget key requires --target or --node')
            elif args.op == 'widget_click':
                if args.menu_action:
                    matches = [(n['node'], i) for n in before['widgets'] for i, a in enumerate(n.get('actions', []))
                               if a['enabled'] and a['text'].replace('&', '').split('\t', 1)[0] == args.menu_action]
                    if len(matches) != 1:
                        raise RuntimeError('Expected one enabled menu action; matched ' + str(len(matches)))
                    fields['node'], fields['action'] = matches[0]
                elif args.widget_text:
                    matches = [n for n in before['widgets'] if n['enabled'] and n.get('text', '').replace('&', '') == args.widget_text]
                    if len(matches) != 1:
                        raise RuntimeError('Expected one enabled native widget; matched ' + str(len(matches)))
                    fields['node'] = matches[0]['node']
                elif args.target:
                    nodes = [n for n in before['widgets'] if n['id'] == args.target and n['enabled']]
                    if len(nodes) != 1:
                        raise RuntimeError('Expected one native widget target; matched ' + str(len(nodes)))
                    fields['node'] = nodes[0]['node']
                elif args.node is not None:
                    fields['node'] = args.node
                else:
                    parser.error('Widget click requires --target or --node')
                fields.setdefault('action', args.action if args.action is not None else -1)
            elif args.op == 'resize':
                if args.width is None or args.height is None:
                    parser.error('Resize requires --width and --height')
                fields.update(width=args.width, height=args.height)
            if args.await_property or args.await_core:
                if args.await_value is None:
                    parser.error('--await-property requires a JSON --await-value')
                fields.update(await_value=args.await_value, await_tolerance=args.await_tolerance, await_comparison=args.await_comparison)
                if args.await_core:
                    fields['await_core'] = args.await_core
                    if args.await_core in ('position', 'time_seconds'):
                        fields['await_media_url'] = before.get('core', {}).get('url', '')
                else:
                    fields['await_property'] = args.await_property
                if args.await_core:
                    pass
                elif args.await_node is not None:
                    fields['await_node'] = args.await_node
                elif args.await_target or args.await_name:
                    matches = [n for n in before['tree'] if (args.await_target and n['id'] == args.await_target) or
                               (args.await_name and n['visible'] and n.get('name') == args.await_name and n.get('actions'))]
                    if len(matches) != 1:
                        raise RuntimeError('Expected one observation target; matched ' + str(len(matches)))
                    fields['await_node'] = matches[0]['node']
                elif 'node' not in fields:
                    parser.error('This operation requires --await-target')
            output, result = request(args.op, **fields)
        print(json.dumps({k: result[k] for k in ['status', 'revision', 'before_revision', 'player_ready', 'missing_required_items', 'images', 'qml_errors', 'window', 'core', 'capture_saved'] if k in result}, indent=2))
        print('Response:', output)
        print('Owned VLC has OS foreground window:', json.dumps({'before': foreground_before, 'after': owns_foreground()}))
    finally:
        if notification:
            kernel.FindCloseChangeNotification(notification)
        kernel.CloseHandle(process)


if __name__ == '__main__':
    main()

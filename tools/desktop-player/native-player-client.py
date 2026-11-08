#!/usr/bin/env python3
"""Event-driven client for an owned native test player's existing diagnostics.

The caller supplies the Popen it launched, not an arbitrary desktop PID. Only
the test build's authenticated local directory protocol is used for UI actions.
"""
import ctypes
import json
import os
from pathlib import Path
import select
import selectors
import sys
import uuid


class NativePlayerClient:
    def __init__(self, process, directory, token):
        self.process = process
        self.directory = Path(directory).resolve()
        self.token = token
        self.queue = None
        self.selector = None
        self.descriptors = []
        if sys.platform == 'darwin':
            self.queue = select.kqueue()
            self.directory_fd = os.open(self.directory, os.O_RDONLY)
            self.descriptors.append(self.directory_fd)
            self.queue.control([
                select.kevent(self.directory_fd, filter=select.KQ_FILTER_VNODE,
                    flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR,
                    fflags=select.KQ_NOTE_WRITE | select.KQ_NOTE_RENAME),
                select.kevent(process.pid, filter=select.KQ_FILTER_PROC,
                    flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                    fflags=select.KQ_NOTE_EXIT)], 0, 0)
        elif sys.platform == 'linux':
            libc = ctypes.CDLL(None, use_errno=True)
            libc.inotify_init1.argtypes = [ctypes.c_int]
            libc.inotify_init1.restype = ctypes.c_int
            libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
            libc.inotify_add_watch.restype = ctypes.c_int
            self.directory_fd = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
            if self.directory_fd < 0:
                raise OSError(ctypes.get_errno(), 'inotify_init1')
            self.descriptors.append(self.directory_fd)
            # CREATE, MOVED_TO and CLOSE_WRITE cover QSaveFile's atomic commit
            # and the ready marker, rather than assuming one event per file.
            if libc.inotify_add_watch(self.directory_fd, os.fsencode(self.directory), 0x188) < 0:
                raise OSError(ctypes.get_errno(), 'inotify_add_watch')
            process_fd = os.pidfd_open(process.pid)
            self.descriptors.append(process_fd)
            self.selector = selectors.DefaultSelector()
            self.selector.register(self.directory_fd, selectors.EVENT_READ, 'directory')
            self.selector.register(process_fd, selectors.EVENT_READ, 'process')
        else:
            raise RuntimeError('This client requires native macOS or Linux')

    def close(self):
        if self.queue:
            self.queue.close()
        if self.selector:
            self.selector.close()
        for descriptor in self.descriptors:
            os.close(descriptor)
        self.descriptors.clear()

    def _wait(self):
        if self.queue:
            return any(event.filter == select.KQ_FILTER_PROC
                       for event in self.queue.control(None, 8, None))
        events = self.selector.select()
        exited = False
        for key, _ in events:
            if key.data == 'process':
                exited = True
            else:
                os.read(self.directory_fd, 65536)
        return exited

    def request(self, operation, **fields):
        request_id = uuid.uuid4().hex
        command = dict(id=request_id, token=self.token, op=operation, **fields)
        pending = self.directory / ('pending-' + request_id + '.json')
        pending.write_text(json.dumps(command) + '\n')
        pending.replace(self.directory / ('request-' + request_id + '.json'))
        ready = self.directory / (request_id + '.ready')
        while not ready.exists():
            if self.process.poll() is not None:
                raise RuntimeError('Owned player exited before response ' + request_id)
            if self._wait() and not ready.exists():
                raise RuntimeError('Owned player exited before response ' + request_id)
        result = json.loads((self.directory / (request_id + '.json')).read_text())
        if result.get('id') != request_id or result.get('status') == 'failed':
            raise RuntimeError('Player diagnostic failed: ' + json.dumps(result))
        return result

    def snapshot(self, **fields):
        return self.request('snapshot', **fields)

    @staticmethod
    def target(snapshot, identifier=None, name=None):
        nodes = [node for node in snapshot['tree'] if node['visible'] and node['enabled']
                 and ((identifier is not None and node['id'] == identifier)
                      or (name is not None and node.get('name') == name and node.get('actions')))]
        if len(nodes) != 1:
            raise RuntimeError(f'Expected one rendered target {identifier or name}; found {len(nodes)}')
        return nodes[0]['node']

    def action(self, operation, target=None, name=None, **fields):
        before = self.snapshot()
        if target is not None or name is not None:
            fields['node'] = self.target(before, target, name)
        fields.setdefault('fraction_x', 0.5)
        fields.setdefault('fraction_y', 0.5)
        fields.setdefault('button', 'left')
        return self.request(operation, revision=before['revision'], **fields)

    def await_core(self, key, value, comparison='equal', tolerance=0):
        before = self.snapshot()
        fields = dict(revision=before['revision'], await_core=key, await_value=value,
                      await_comparison=comparison, await_tolerance=tolerance)
        if key in ('position', 'time_seconds') or key.startswith('mpv_audio_'):
            fields['await_media_url'] = before.get('core', {}).get('url', '')
        return self.snapshot(**fields)

    def await_property(self, target, key, value, tolerance=0):
        before = self.snapshot()
        return self.snapshot(revision=before['revision'], await_node=self.target(before, target),
            await_property=key, await_value=value, await_comparison='equal', await_tolerance=tolerance)

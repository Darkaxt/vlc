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
    @staticmethod
    def slider_fraction(node, position):
        """Invert Qt's handle-center mapping using this rendered slider's geometry."""
        geometry = node['slider_geometry']
        width = geometry['width']
        extent = geometry['available_width'] - geometry['handle_width']
        if width <= 0 or extent <= 0 or not 0 <= position <= 1:
            raise ValueError('Slider has no usable track or position is out of range')
        offset = geometry['handle_width'] / 2 + position * extent
        x = (width - geometry['right_padding'] - offset if geometry['mirrored']
             else geometry['left_padding'] + offset)
        return x / width

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
            events = self.queue.control(None, 8, 30)
            return ('observe' if not events else
                    any(event.filter == select.KQ_FILTER_PROC for event in events))
        events = self.selector.select(timeout=30)
        if not events:
            return 'observe'
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
        print('NATIVE REQUEST', request_id, operation,
              fields.get('await_core', fields.get('await_property', '')), flush=True)
        pending = self.directory / ('pending-' + request_id + '.json')
        pending.write_text(json.dumps(command) + '\n')
        pending.replace(self.directory / ('request-' + request_id + '.json'))
        ready = self.directory / (request_id + '.ready')
        observer = None
        while not ready.exists():
            if self.process.poll() is not None:
                raise RuntimeError('Owned player exited before response ' + request_id)
            # A health interval only reports the current state. It never ends,
            # retries or changes the original pending operation. The test build
            # supports a read-only snapshot while a predicate is pending.
            if observer and (self.directory / (observer + '.ready')).exists():
                observation = json.loads((self.directory / (observer + '.json')).read_text())
                print('NATIVE WAIT', request_id, json.dumps({
                    key: observation.get(key) for key in ('status', 'error', 'core', 'main_window')
                }), flush=True)
                observer = None
            event = self._wait()
            if event == 'observe' and not observer:
                observer = uuid.uuid4().hex
                probe = self.directory / ('pending-' + observer + '.json')
                probe.write_text(json.dumps(dict(id=observer, token=self.token, op='snapshot')) + '\n')
                probe.replace(self.directory / ('request-' + observer + '.json'))
            elif event is True and not ready.exists():
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
        if key in ('position', 'time_seconds', 'selected_subtitle_count') or key.startswith('mpv_audio_'):
            fields['await_media_url'] = before.get('core', {}).get('url', '')
        return self.snapshot(**fields)

    def slider(self, target, position):
        before = self.snapshot()
        index = self.target(before, target)
        node = next(row for row in before['tree'] if row['node'] == index)
        return self.request('click', revision=before['revision'], node=index,
                            fraction_x=self.slider_fraction(node, position),
                            fraction_y=0.5, button='left')

    def await_property(self, target, key, value, tolerance=0):
        before = self.snapshot()
        return self.snapshot(revision=before['revision'], await_node=self.target(before, target),
            await_property=key, await_value=value, await_comparison='equal', await_tolerance=tolerance)

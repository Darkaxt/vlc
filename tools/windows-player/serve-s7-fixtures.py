"""Owned loopback HTTP fixtures for R61; stop on explicit owner stdin/EOF.

The live transport has no Content-Length or Range support. Finite MP4 files
and a real M3U playlist use their actual lengths. No user files are served.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import socket
import sys
import threading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', required=True, type=Path)
    parser.add_argument('--transport', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    args = parser.parse_args()
    files = {'/clip-a.mp4': args.fixtures / 'clip-a.mp4',
             '/clip-b.mp4': args.fixtures / 'clip-b.mp4', '/live.ts': args.transport}
    assert all(path.is_file() for path in files.values())
    assert args.evidence.parent.is_dir() and not args.evidence.exists()
    requests, clients = [], set()
    lock = threading.Lock()
    stopping = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.0'

        def setup(self):
            super().setup()
            with lock:
                clients.add(self.connection)

        def finish(self):
            try:
                super().finish()
            finally:
                with lock:
                    clients.discard(self.connection)

        def log_message(self, *unused):
            pass

        def do_GET(self):
            route = self.path
            entry = {'path': route, 'range_requested': self.headers.get('Range'), 'bytes_sent': 0}
            with lock:
                requests.append(entry)
            if route == '/playlist.m3u8':
                port = self.server.server_address[1]
                body = ('#EXTM3U\n#EXTINF:8,S7 first clip\nhttp://127.0.0.1:' + str(port)
                    + '/clip-a.mp4\n#EXTINF:8,S7 second clip\nhttp://127.0.0.1:' + str(port) + '/clip-b.mp4\n').encode()
                self.send_response(200)
                self.send_header('Content-Type', 'audio/x-mpegurl')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                entry['bytes_sent'] = len(body)
                return
            if route not in files:
                self.send_error(404)
                return
            size = files[route].stat().st_size
            offset, end = 0, size - 1
            ranged = route != '/live.ts' and self.headers.get('Range')
            if ranged:
                match = re.fullmatch(r'bytes=(\d+)-(\d*)', ranged)
                if not match or int(match[1]) >= size:
                    self.send_error(416)
                    return
                offset = int(match[1])
                end = min(int(match[2]), size - 1) if match[2] else size - 1
                if end < offset:
                    self.send_error(416)
                    return
            self.send_response(206 if ranged else 200)
            self.send_header('Content-Type', 'video/mp2t' if route == '/live.ts' else 'video/mp4')
            if route != '/live.ts':
                self.send_header('Content-Length', str(end - offset + 1))
                self.send_header('Accept-Ranges', 'bytes')
                if ranged:
                    self.send_header('Content-Range', f'bytes {offset}-{end}/{size}')
            self.send_header('Connection', 'close')
            self.end_headers()
            try:
                with files[route].open('rb') as source:
                    source.seek(offset)
                    remaining = end - offset + 1
                    while remaining and not stopping.is_set():
                        data = source.read(min(65536, remaining))
                        if not data:
                            break
                        self.wfile.write(data)
                        entry['bytes_sent'] += len(data)
                        remaining -= len(data)
            except (ConnectionError, OSError):
                entry['client_disconnected'] = True

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = False
    runner = threading.Thread(target=server.serve_forever)
    runner.start()
    print(json.dumps({'state': 'ready', 'base_url': 'http://127.0.0.1:' + str(server.server_address[1])}), flush=True)
    try:
        for line in sys.stdin:
            if line.strip() == 'stop':
                break
    finally:
        stopping.set()
        with lock:
            current = list(clients)
        for client in current:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        server.shutdown()
        runner.join()
        server.server_close()
        result = {'state': 'stopped', 'requests': requests, 'all_owned_threads_joined': True,
            'binding': '127.0.0.1 only', 'source': 'S7 synthetic test-owned fixtures'}
        args.evidence.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()

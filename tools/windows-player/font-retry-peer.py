"""Owned loopback proxy for one font failure followed by a real HTTPS retry.

The first expected CONNECT waits for 'fail' on stdin, then returns 502. The
second tunnels encrypted bytes to the actual publisher, without terminating TLS
or changing certificates. 'stop' cancels this exact peer. No elapsed deadlines.
"""
import json
import os
import select
import socket
import sys
import threading
from queue import Queue

ORIGIN = b'www.exljbris.com:443'
commands = Queue()
stopped = threading.Event()
sockets = []
listener = socket.socket()
sockets.append(listener)
listener.bind(('127.0.0.1', 0))
listener.listen(1)
record = {'port': listener.getsockname()[1], 'pid': os.getpid(), 'requests': 0,
    'forwarded_connections': 0, 'client_tls_bytes': 0, 'publisher_tls_bytes': 0}


def publish(**values):
    print(json.dumps(values), flush=True)


def control():
    for line in sys.stdin:
        command = line.strip()
        commands.put(command)
        if command == 'stop':
            stopped.set()
            for stream in list(sockets):
                try: stream.shutdown(socket.SHUT_RDWR)
                except OSError: pass
                stream.close()
            return


def connect_request():
    client, _ = listener.accept()
    sockets.append(client)
    headers = bytearray()
    while not headers.endswith(b'\r\n\r\n'):
        data = client.recv(1)
        if not data or len(headers) >= 8192:
            raise ValueError('invalid_connect_request')
        headers += data
    fields = bytes(headers).split(b'\r\n', 1)[0].split()
    if len(fields) != 3 or fields[0] != b'CONNECT' or fields[1] != ORIGIN:
        raise ValueError('unexpected_connect_origin')
    record['requests'] += 1
    return client


threading.Thread(target=control, daemon=True).start()
publish(state='ready', **record)
exit_code = 1
try:
    first = connect_request()
    publish(state='first_request_pending')
    if commands.get() != 'fail':
        raise ValueError('owner_abandoned_before_failure')
    first.sendall(b'HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
    first.close()
    publish(state='first_request_failed')
    client = connect_request()
    upstream = socket.create_connection(('www.exljbris.com', 443))
    sockets.append(upstream)
    record['forwarded_connections'] += 1
    client.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
    publish(state='retry_tunnel_ready')
    while True:
        ready, _, _ = select.select([client, upstream], [], [])
        ended = False
        for source in ready:
            data = source.recv(65536)
            if not data:
                ended = True
                break
            destination = upstream if source is client else client
            destination.sendall(data)
            record['client_tls_bytes' if source is client else 'publisher_tls_bytes'] += len(data)
        if ended:
            break
    exit_code = 0
except (OSError, ValueError) as error:
    record['error'] = type(error).__name__
finally:
    for stream in sockets:
        stream.close()
    record.update(state='owner_cancelled' if stopped.is_set() else 'complete' if exit_code == 0 else 'failed', exit_code=exit_code)
    publish(**record)
raise SystemExit(exit_code)

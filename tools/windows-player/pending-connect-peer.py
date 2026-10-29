"""One owned loopback CONNECT peer for native cancellation verification.

Acknowledge the expected provider tunnel, then wait for the client's TLS bytes
and disconnection. Never establish an upstream connection or complete TLS.
Send "stop" on stdin to abandon the test; no elapsed deadline closes a client.
"""
from pathlib import Path
import argparse
import json
import os
import socket
import sys
import threading
import time
sys.dont_write_bytecode = True

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--directory', type=Path, required=True)
p.add_argument('--origin', choices=['api.opensubtitles.com:443','www.exljbris.com:443'], default='api.opensubtitles.com:443')
a = p.parse_args()
e = a.directory.resolve()
if e.drive.upper() not in ('D:', 'E:') or 'Temp' not in e.parts:
    p.error('Use an exact task-owned D:/E:/Temp evidence directory')
e.mkdir(parents=True, exist_ok=False)
owner_stop = threading.Event()
client = None
listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listener.bind(('127.0.0.1', 0))
listener.listen(1)
started = time.monotonic()
result = dict(state='started', pid=os.getpid(), port=listener.getsockname()[1], accepted_connections=0, forwarded_connections=0)

def write(name, data):
    pending = e / (name + '.pending')
    pending.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8', newline='\n')
    os.replace(pending, e / (name + '.json'))

def stop_from_stdin():
    for line in sys.stdin:
        if line.strip() != 'stop':
            continue
        owner_stop.set()
        if client is not None:
            try: client.shutdown(socket.SHUT_RDWR)
            except OSError: pass
        listener.close()
        return

threading.Thread(target=stop_from_stdin, daemon=True).start()
write('peer', result)
print('Owned loopback cancellation peer ready', flush=True)
exit_code = 1
try:
    client, address = listener.accept()
    result['accepted_connections'] = 1
    listener.close()
    headers = bytearray()
    while not headers.endswith(b'\r\n\r\n'):
        byte = client.recv(1)
        if not byte or len(headers) >= 8192:
            raise ValueError('invalid_connect_request')
        headers.extend(byte)
    first = bytes(headers).split(b'\r\n', 1)[0].split()
    if len(first) != 3 or first[0] != b'CONNECT' or first[1] != a.origin.encode('ascii'):
        raise ValueError('unexpected_connect_origin')
    client.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
    greeting = client.recv(65536)
    if not greeting or greeting[0] != 22:
        raise ValueError('expected_tls_client_hello')
    count = len(greeting)
    write('handshake', dict(state='tls_pending', client_port=address[1], elapsed_ms=round((time.monotonic()-started)*1000)))
    print(json.dumps({'state':'tls_pending','origin':a.origin}),flush=True)
    while True:
        data = client.recv(65536)
        if not data:
            break
        count += len(data)
    result.update(state='owner_cancelled' if owner_stop.is_set() else 'client_disconnected', tls_bytes=count)
    exit_code = 1 if owner_stop.is_set() else 0
except (OSError, ValueError) as error:
    result.update(state='owner_cancelled' if owner_stop.is_set() else 'failed', error=type(error).__name__)
finally:
    listener.close()
    if client is not None: client.close()
    result.update(exit_code=exit_code, elapsed_ms=round((time.monotonic()-started)*1000))
    write('result', result)
    print(json.dumps(result), flush=True)
raise SystemExit(exit_code)

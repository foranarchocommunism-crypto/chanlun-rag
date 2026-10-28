"""Temporary loopback-only CONNECT relay for the isolated validation VM.

TLS remains end to end and certificate verification stays in Docker/curl.
No credentials, signed URLs or payload bodies are logged. Only Microsoft image
registry/storage hosts on port 443 are accepted. Remove after project delivery.
"""
import http.server
import json
import select
import socket
import socketserver
import time


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_CONNECT(self):
        host, separator, port = self.path.rpartition(':')
        host = host.lower()
        allowed = host == 'mcr.microsoft.com' or host.endswith(('.data.mcr.microsoft.com', '.blob.core.windows.net'))
        if not separator or port != '443' or not allowed:
            self.send_error(403, 'Only the Microsoft validation registry is allowed')
            return
        upstream = None
        transferred = [0, 0]
        try:
            upstream = socket.create_connection((host, 443), timeout=25)
            self.send_response(200, 'Connection Established')
            self.end_headers()
            sockets = [self.connection, upstream]
            print(json.dumps({'connected': host, 'at': time.time()}), flush=True)
            while True:
                ready, _, failed = select.select(sockets, [], sockets, 180)
                if failed or not ready:
                    break
                for channel in ready:
                    chunk = channel.recv(128*1024)
                    if not chunk:
                        return
                    index = sockets.index(channel)
                    sockets[1-index].sendall(chunk)
                    transferred[index] += len(chunk)
        except (OSError, TimeoutError) as error:
            print(json.dumps({'host': host, 'error': str(error)}), flush=True)
        finally:
            if upstream:
                upstream.close()
            print(json.dumps({'closed': host, 'bytes_client_upstream': transferred, 'at': time.time()}), flush=True)


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


with Server(('127.0.0.1', 26149), Handler) as server:
    print(json.dumps({'listening': '127.0.0.1:26149', 'tls_interception': False}), flush=True)
    server.serve_forever()

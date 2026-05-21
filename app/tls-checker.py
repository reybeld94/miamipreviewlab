#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/check"):
            self.send_response(200)  # Allow all subdomains for TLS
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

HTTPServer(("localhost", 9123), Handler).serve_forever()

#!/usr/bin/env python3
"""Simple HTTP server for serving generated PPT files"""
import http.server
import socketserver
from pathlib import Path
import threading

PORT = 8765
OUTPUTS_DIR = Path(__file__).parent / "outputs"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUTPUTS_DIR), **kwargs)

def start_server():
    """Start HTTP server in background thread"""
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"📁 File server running at http://localhost:{PORT}")
        httpd.serve_forever()

def start_background():
    """Start server in background thread"""
    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()
    return f"http://localhost:{PORT}"

if __name__ == "__main__":
    start_server()

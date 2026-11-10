"""Serve the built project at its real GitHub Pages path for local review."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import argparse

ROOT = Path(__file__).resolve().parents[1]
PREFIX = '/robo-si-results'

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'dist'), **kwargs)

    def do_GET(self):
        if self.path == PREFIX:
            self.send_response(302)
            self.send_header('Location', PREFIX + '/')
            self.end_headers()
            return
        if urlsplit(self.path).path.startswith(PREFIX + '/'):
            self.path = self.path[len(PREFIX):]
        super().do_GET()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    print(f'Local: http://127.0.0.1:{args.port}{PREFIX}/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()

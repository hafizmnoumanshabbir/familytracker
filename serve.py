"""
Static file server + tiny JSON database for the Personal Tracker apps.

GET  /                  -> directory index / static files
GET  /db/<name>         -> read db/<name>.json  (empty {} if not yet created)
POST /db/<name>         -> overwrite db/<name>.json with the request body
                           and also write db/snapshots/<name>_<YYYY-MM-DD>.json

Allowed names: family_quest, noman_tracker
"""
import os, json, http.server, socketserver, urllib.parse, threading
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(ROOT, 'db')
SNAPSHOT_DIR = os.path.join(DB_DIR, 'snapshots')
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

ALLOWED = {
    'family_quest':  os.path.join(DB_DIR, 'family_quest.json'),
    'noman_tracker': os.path.join(DB_DIR, 'noman_tracker.json'),
}

# Serialize concurrent writes per file
_LOCKS = {name: threading.Lock() for name in ALLOWED}

PORT = 8123
os.chdir(ROOT)


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print('[%s] %s' % (self.log_date_time_string(), fmt % args), flush=True)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _send_json(self, code, body_bytes):
        self.send_response(code)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body_bytes)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body_bytes)

    def _send_text(self, code, msg):
        b = msg.encode('utf-8')
        self.send_response(code)
        self._cors()
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith('/db/'):
            name = parsed.path[len('/db/'):]
            if name not in ALLOWED:
                return self._send_text(404, 'unknown db: %r' % name)
            path = ALLOWED[name]
            if not os.path.exists(path):
                return self._send_json(200, b'{}')
            with _LOCKS[name]:
                with open(path, 'rb') as f:
                    data = f.read()
            return self._send_json(200, data)
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if not parsed.path.startswith('/db/'):
            return self._send_text(405, 'POST only supported on /db/*')
        name = parsed.path[len('/db/'):]
        if name not in ALLOWED:
            return self._send_text(404, 'unknown db: %r' % name)
        n = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(n) if n > 0 else b''
        try:
            json.loads(body.decode('utf-8'))
        except Exception as e:
            return self._send_text(400, 'invalid json: ' + str(e))
        path = ALLOWED[name]
        today = datetime.now().strftime('%Y-%m-%d')
        snap = os.path.join(SNAPSHOT_DIR, '%s_%s.json' % (name, today))
        with _LOCKS[name]:
            tmp = path + '.tmp'
            with open(tmp, 'wb') as f:
                f.write(body)
            os.replace(tmp, path)
            with open(snap + '.tmp', 'wb') as f:
                f.write(body)
            os.replace(snap + '.tmp', snap)
        return self._send_text(200, 'ok')


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    print('PersonalTracker server')
    print('  static root : ' + ROOT)
    print('  db          : ' + DB_DIR)
    print('  snapshots   : ' + SNAPSHOT_DIR)
    print('  listening   : http://127.0.0.1:%d' % PORT)
    with ThreadingHTTPServer(('127.0.0.1', PORT), Handler) as httpd:
        httpd.serve_forever()


if __name__ == '__main__':
    main()

"""Tiny stdlib HTTP server shared by all four model workers.

ponytail: http.server, not FastAPI — workers live inside the models' fragile
venvs (audiogen pins transformers==4.44.2), so zero extra installs there.
"""
import json
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATE = {"loaded": False, "busy": False, "stage": "idle", "progress": None,
         "started": None, "error": None}
_gen_lock = threading.Lock()


def models_dir():
    """Root of the weights/caches tree; the orchestrator passes it in the env."""
    d = os.environ.get("MUSITION_MODELS_DIR")
    if not d:
        raise SystemExit("MUSITION_MODELS_DIR не задан (см. README)")
    return d


def set_progress(done, total):
    # AudioGen's extend path reports past `total` once it starts a second segment.
    STATE["progress"] = round(min(100.0, 100.0 * done / max(total, 1)), 1)


def progress_tqdm(base_tqdm):
    """Wrap tqdm so a library's own progress bar drives STATE['progress']."""
    class _T(base_tqdm):
        def __iter__(self):
            for i, x in enumerate(super().__iter__(), 1):
                if self.total:
                    set_progress(i, self.total)
                yield x

        def update(self, n=1):
            r = super().update(n)
            if self.total:
                set_progress(self.n, self.total)
            return r
    return _T


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            self._send(200, STATE)
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            params = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self._send(400, {"error": "bad json"})

        if self.path == "/load":
            try:
                self._load()
                self._send(200, STATE)
            except Exception:
                STATE.update(stage="error", error=traceback.format_exc())
                self._send(500, {"error": STATE["error"]})
        elif self.path == "/generate":
            if not _gen_lock.acquire(blocking=False):
                return self._send(409, {"error": "worker busy"})
            try:
                self._load()
                STATE.update(busy=True, stage="generating", progress=None,
                             started=time.time(), error=None)
                paths, meta = self.server.generate(params)
                self._send(200, {"paths": paths, "meta": meta})
            except Exception:
                STATE["error"] = traceback.format_exc()
                print(STATE["error"], file=sys.stderr, flush=True)
                self._send(500, {"error": STATE["error"]})
            finally:
                STATE.update(busy=False, stage="idle", progress=None, started=None)
                _gen_lock.release()
        elif self.path == "/unload":
            # Freeing tensors leaves the CUDA context behind; exiting is the only
            # way nvidia-smi actually goes back to zero.
            self._send(200, {"ok": True})
            threading.Thread(target=self._exit_soon, daemon=True).start()
        else:
            self._send(404, {"error": "not found"})

    def _load(self):
        if STATE["loaded"]:
            return
        STATE.update(stage="loading", progress=None)
        self.server.load()
        STATE.update(loaded=True, stage="idle")

    def _exit_soon(self):
        time.sleep(0.3)
        os._exit(0)


def serve(load, generate):
    port = int(sys.argv[1])
    srv = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    srv.load, srv.generate = load, generate
    print(f"worker listening on {port}", flush=True)
    srv.serve_forever()

"""Musition orchestrator: serves the UI, owns the single GPU slot, keeps the gallery.

Only one model worker is alive at a time (12GB VRAM, ACE-Step alone takes 7.4GB).
"""
import glob
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

APP = Path(__file__).parent
ROOT = APP.parent
OUTPUTS = APP / "data" / "outputs"
UPLOADS = APP / "data" / "uploads"
DB_PATH = APP / "data" / "gallery.db"
IDLE_UNLOAD_S = 600

MODELS = {
    "audiogen": {"dir": ROOT / "audiogen", "script": "audiogen_worker.py", "port": 8101},
    "stable-audio-open": {"dir": ROOT / "stable-audio-open", "script": "sao_worker.py", "port": 8102},
    "bark": {"dir": ROOT / "bark", "script": "bark_worker.py", "port": 8103},
    "ace-step": {"dir": ROOT / "ace-step", "script": "acestep_worker.py", "port": 8104},
}


def _dotenv():
    env = {}
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


DOTENV = _dotenv()


# ---------------------------------------------------------------- worker slot

def _http(port, path, payload=None, timeout=30):
    url = "http://127.0.0.1:%d%s" % (port, path)
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method="POST" if data is not None else "GET",
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b"{}")


class Slot:
    """The one GPU seat. Starting a different model evicts the current one."""

    def __init__(self):
        self.lock = threading.RLock()
        self.gen_lock = threading.Lock()
        self.proc = None
        self.name = None
        self.last_used = 0.0
        self.stage = "idle"
        self.last_stderr = None

    def stop(self):
        with self.lock:
            if not self.proc:
                return
            self.stage = "unloading"
            try:
                _http(MODELS[self.name]["port"], "/unload", {}, timeout=10)
            except Exception:
                pass
            try:
                self.proc.wait(timeout=30)
            except Exception:
                self.proc.kill()
            self.proc = self.name = None
            self.stage = "idle"

    def ensure(self, name):
        with self.lock:
            if self.proc and self.proc.poll() is not None:
                self.proc = self.name = None
            if self.name == name:
                self.last_used = time.time()
                return
            if self.name:
                self.stop()
            self._start(name)

    def _start(self, name):
        cfg = MODELS[name]
        py = cfg["dir"] / ".venv" / "Scripts" / "python.exe"
        if not py.exists():
            raise HTTPException(500, "нет venv для %s: %s" % (name, py))

        env = dict(os.environ)
        env.setdefault("HF_HOME", r"D:\AIModels\SoundGen\hf_cache")
        env["XDG_CACHE_HOME"] = r"D:\AIModels\SoundGen\_xdg_cache"  # Bark weights live here
        env["PYTHONUNBUFFERED"] = "1"
        if DOTENV.get("HF_TOKEN"):
            env["HF_TOKEN"] = DOTENV["HF_TOKEN"]

        self.stage = "starting"
        self.last_stderr = None
        self.proc = subprocess.Popen(
            [str(py), str(APP / "workers" / cfg["script"]), str(cfg["port"])],
            cwd=str(cfg["dir"]), env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        threading.Thread(target=self._drain, args=(self.proc,), daemon=True).start()

        deadline = time.time() + 120
        while time.time() < deadline:
            if self.proc.poll() is not None:
                self.proc = None
                self.stage = "idle"
                raise HTTPException(500, "воркер %s упал при старте: %s" % (name, self.last_stderr or ""))
            try:
                _http(cfg["port"], "/status", timeout=2)
                break
            except Exception:
                time.sleep(0.3)
        else:
            self.proc.kill()
            self.proc = None
            self.stage = "idle"
            raise HTTPException(500, "воркер %s не поднялся за 120с" % name)

        self.name, self.last_used = name, time.time()
        self.stage = "idle"

    def _drain(self, proc):
        for line in iter(proc.stderr.readline, b""):
            text = line.decode("utf-8", "replace").rstrip()
            if text:
                self.last_stderr = text
                print("[worker] " + text, file=sys.stderr, flush=True)

    def status(self):
        with self.lock:
            if self.proc and self.proc.poll() is not None:
                self.proc = self.name = None
                self.stage = "idle"
            base = {"model": self.name, "stage": self.stage,
                    "busy": self.gen_lock.locked(),
                    "progress": None, "loaded": False, "started": None}
            if self.proc and self.stage not in ("starting", "unloading"):
                try:
                    w = _http(MODELS[self.name]["port"], "/status", timeout=3)
                    base.update(stage=w["stage"], progress=w["progress"],
                                loaded=w["loaded"], started=w["started"])
                except Exception:
                    pass
            return base


SLOT = Slot()


def _idle_reaper():
    while True:
        time.sleep(min(30, IDLE_UNLOAD_S))
        with SLOT.lock:
            if (SLOT.proc and not SLOT.gen_lock.locked()
                    and time.time() - SLOT.last_used > IDLE_UNLOAD_S):
                print("[idle] выгружаю " + SLOT.name, flush=True)
                SLOT.stop()


# -------------------------------------------------------------------- gallery

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("""create table if not exists gen(
        id text primary key, ts text, model text, prompt text,
        duration real, file text, params text)""")
    return con


def add_gen(model, prompt, duration, path, params):
    rel = str(Path(path).resolve().relative_to(OUTPUTS.resolve())).replace("\\", "/")
    row = {"id": uuid.uuid4().hex,
           "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "model": model, "prompt": prompt or "", "duration": duration,
           "file": rel, "params": json.dumps(params, ensure_ascii=False)}
    with db() as con:
        con.execute("insert into gen values(:id,:ts,:model,:prompt,:duration,:file,:params)", row)
    return row


# ------------------------------------------------------------------------ app

app = FastAPI(title="Musition")


@app.get("/api/status")
def api_status():
    return SLOT.status()


@app.get("/api/voices")
def api_voices():
    d = MODELS["bark"]["dir"] / ".venv" / "Lib" / "site-packages" / "bark" / "assets" / "prompts"
    names = [str(Path(f).relative_to(d).with_suffix("")).replace("\\", "/")
             for f in glob.glob(str(d / "**" / "*.npz"), recursive=True)]
    return sorted(names)


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    UPLOADS.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "ref.wav").suffix or ".wav"
    dest = UPLOADS / (uuid.uuid4().hex + ext)
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"path": str(dest)}


@app.post("/api/generate")
def api_generate(body: dict = Body(...)):
    model = body.get("model")
    if model not in MODELS:
        raise HTTPException(400, "неизвестная модель")
    params = dict(body.get("params") or {})

    if not SLOT.gen_lock.acquire(blocking=False):
        raise HTTPException(409, "генерация уже идёт (%s)" % SLOT.name)
    try:
        SLOT.ensure(model)

        out_dir = OUTPUTS / model
        out_dir.mkdir(parents=True, exist_ok=True)
        params["out_path"] = str(out_dir / (uuid.uuid4().hex + ".wav"))

        try:
            res = _http(MODELS[model]["port"], "/generate", params, timeout=3600)
        except urllib.error.HTTPError as e:
            raise HTTPException(500, json.loads(e.read() or b"{}").get("error", str(e)))
        except Exception as e:
            raise HTTPException(500, "воркер не ответил: %s\n%s" % (e, SLOT.error or ""))

        SLOT.last_used = time.time()
        saved = dict(params, **res.get("meta", {}))
        saved.pop("out_path", None)
        prompt = params.get("prompt") or params.get("text") or ""
        dur = params.get("duration") or params.get("audio_end_in_s") or params.get("audio_duration")
        return [add_gen(model, prompt, dur, p, saved) for p in res["paths"]]
    finally:
        SLOT.gen_lock.release()


@app.post("/api/unload")
def api_unload():
    if SLOT.gen_lock.locked():
        raise HTTPException(409, "идёт генерация")
    SLOT.stop()
    return {"ok": True}


@app.get("/api/gallery")
def api_gallery(model: str = None):
    q = "select * from gen"
    args = ()
    if model:
        q += " where model=?"
        args = (model,)
    with db() as con:
        return [dict(r) for r in con.execute(q + " order by ts desc, rowid desc", args)]


@app.delete("/api/gallery/{gid}")
def api_delete(gid: str):
    with db() as con:
        row = con.execute("select file from gen where id=?", (gid,)).fetchone()
        if not row:
            raise HTTPException(404, "нет такой записи")
        con.execute("delete from gen where id=?", (gid,))
    f = OUTPUTS / row["file"]
    for p in (f, f.with_name(f.stem + "_input_params.json")):
        try:
            p.unlink()
        except OSError:
            pass
    return {"ok": True}


OUTPUTS.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=OUTPUTS), name="media")
app.mount("/", StaticFiles(directory=APP / "static", html=True), name="static")


@app.on_event("startup")
def _startup():
    db().close()
    threading.Thread(target=_idle_reaper, daemon=True).start()


if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    finally:
        SLOT.stop()

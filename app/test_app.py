r"""Self-check: worker protocol, single-slot eviction and the gallery, no GPU needed.

    app\.venv\Scripts\python.exe app\test_app.py
"""
import tempfile
import threading
import time
from pathlib import Path

import orchestrator as o

# Never touch the real gallery / outputs.
_TMP = Path(tempfile.mkdtemp(prefix="musition-test-"))
o.OUTPUTS = _TMP / "outputs"
o.OUTPUTS.mkdir()
o.DB_PATH = _TMP / "gallery.db"

FAKE = {"dir": Path(__file__).parent, "script": "_dummy_worker.py", "port": 8199}
FAKE2 = dict(FAKE, port=8198)


def check_seed_parsing():
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "workers"))
    from acestep_worker import _seeds
    assert _seeds("1, 2") == [1, 2]
    assert _seeds("42") == [42]
    assert _seeds("") is None and _seeds(None) is None
    assert _seeds("случайно") is None, "мусор в поле сида должен давать случайный сид, а не падать"


def main():
    check_seed_parsing()
    o.MODELS["_fake"] = FAKE
    o.MODELS["_fake2"] = FAKE2

    # --- worker lifecycle: lazy start, one slot only, /unload really exits
    o.SLOT.ensure("_fake")
    assert o.SLOT.proc.poll() is None, "воркер не поднялся"
    first = o.SLOT.proc

    o.SLOT.ensure("_fake2")
    assert first.poll() is not None, "предыдущий воркер не был вытеснен (VRAM осталась занятой)"
    assert o.SLOT.name == "_fake2"

    # --- generate writes a file and lands in the gallery
    rows = o.api_generate({"model": "_fake2", "params": {"prompt": "тест"}})
    assert len(rows) == 1, rows
    row = rows[0]
    f = o.OUTPUTS / row["file"]
    assert f.exists(), f
    assert row["prompt"] == "тест"
    assert '"seed": 42' in row["params"], row["params"]

    assert any(r["id"] == row["id"] for r in o.api_gallery())
    assert all(r["model"] == "_fake2" for r in o.api_gallery(model="_fake2"))
    assert not any(r["id"] == row["id"] for r in o.api_gallery(model="audiogen"))

    # --- delete removes both row and file
    o.api_delete(row["id"])
    assert not f.exists(), "файл остался после удаления"
    assert not any(r["id"] == row["id"] for r in o.api_gallery())

    # --- busy slot rejects a second generation
    o.SLOT.gen_lock.acquire()
    try:
        o.api_generate({"model": "_fake2", "params": {}})
        raise AssertionError("вторая генерация должна была получить 409")
    except o.HTTPException as e:
        assert e.status_code == 409, e.status_code
    finally:
        o.SLOT.gen_lock.release()

    # --- idle reaper frees VRAM on its own
    o.SLOT.ensure("_fake")
    o.IDLE_UNLOAD_S = 1
    threading.Thread(target=o._idle_reaper, daemon=True).start()
    for _ in range(40):
        time.sleep(0.5)
        if o.SLOT.proc is None:
            break
    assert o.SLOT.proc is None, "автовыгрузка по простою не сработала"

    o.SLOT.stop()
    assert o.SLOT.proc is None and o.SLOT.name is None
    print("OK")


if __name__ == "__main__":
    main()

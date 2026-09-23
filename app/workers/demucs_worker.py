"""Demucs worker: cuts a finished render into stems (vocals / instrumental).

Runs in the shared venv like every other worker (see MODELS in orchestrator.py).
Weights (~80MB for htdemucs) land in the shared caches under
MUSITION_MODELS_DIR, which the orchestrator passes in the env.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

SEP = None
SEP_NAME = None


def _device(want):
    import torch
    if want in ("cuda", "cpu"):
        return want
    return "cuda" if torch.cuda.is_available() else "cpu"


def _progress(d):
    """demucs calls this per chunk; a bag of models runs the whole track N times."""
    total = d.get("audio_length") or 0
    models = max(1, d.get("models") or 1)
    if total:
        done = d.get("model_idx_in_bag", 0) * total + (d.get("segment_offset") or 0)
        common.set_progress(done, models * total)


def _separator(name, device, p):
    """The loaded separator, rebuilt only when a different model is asked for."""
    global SEP, SEP_NAME
    import demucs.api
    if SEP is None or SEP_NAME != name:
        SEP = demucs.api.Separator(model=name, callback=_progress)
        SEP_NAME = name
    SEP.update_parameter(
        device=device,
        # 0 keeps it deterministic; >1 averages that many random shifts, and
        # costs proportionally more.
        shifts=int(p.get("shifts", 0)),
        overlap=float(p.get("overlap", 0.25)),
        jobs=int(p.get("jobs", 0)),
    )
    return SEP


def load():
    # Downloads the weights on first use; keeps them warm between requests.
    _separator("htdemucs", _device("auto"), {})


def _wanted(stem, sources):
    """stem name -> {output file suffix: [model sources to sum]}."""
    rest = [s for s in sources if s != "vocals"]
    if stem in sources:
        return {stem: [stem]}
    if stem == "no_vocals":
        return {"no_vocals": rest}
    if stem == "both":
        return {"vocals": ["vocals"], "no_vocals": rest}
    if stem == "all":
        return {s: [s] for s in sources}
    raise ValueError("stem: ожидалось vocals/no_vocals/both/all или один из %s, получено %r"
                     % ("/".join(sources), stem))


def generate(p):
    import demucs.api
    import torch

    src = p.get("src_audio_path") or ""
    if not src or not os.path.isfile(src):
        raise ValueError("src_audio_path: нет такого файла — %r" % src)

    name = p.get("model_name") or "htdemucs"
    device = _device(p.get("device", "auto"))
    sep = _separator(name, device, p)
    wanted = _wanted(str(p.get("stem", "both")), list(sep.model.sources))

    try:
        _, parts = sep.separate_audio_file(src)
    except Exception as e:
        # The GPU slot is ours, but something outside Musition can still crowd it out.
        if device != "cuda" or "cuda" not in str(e).lower():
            raise
        torch.cuda.empty_cache()
        device = "cpu"
        sep.update_parameter(device="cpu")
        _, parts = sep.separate_audio_file(src)

    root, ext = os.path.splitext(p["out_path"])
    paths = []
    for label, sources in wanted.items():
        path = "%s_%s%s" % (root, label, ext)
        demucs.api.save_audio(sum(parts[s] for s in sources), path, samplerate=sep.samplerate)
        paths.append(path)

    frames = next(iter(parts.values())).shape[-1]
    return paths, {"device": device, "model_name": name, "stems": list(wanted),
                   "duration": round(frames / sep.samplerate, 2)}


if __name__ == "__main__":
    common.serve(load, generate)

"""Bark worker: full suno/bark weights — they fit in 12GB alongside nothing else."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common


def load():
    from bark import preload_models
    preload_models()


def generate(p):
    import numpy as np
    import torch
    from scipy.io.wavfile import write as write_wav
    from bark import SAMPLE_RATE, generate_audio

    seed = int(p["seed"]) if str(p.get("seed", "")).strip() not in ("", "-1") else \
        int.from_bytes(os.urandom(4), "little")
    torch.manual_seed(seed)
    np.random.seed(seed % (2 ** 32))

    audio = generate_audio(
        p.get("text", ""),
        history_prompt=p.get("voice") or None,
        text_temp=float(p.get("text_temp", 0.7)),
        waveform_temp=float(p.get("waveform_temp", 0.7)),
    )
    write_wav(p["out_path"], SAMPLE_RATE, audio)
    return [p["out_path"]], {"seed": seed}


if __name__ == "__main__":
    common.serve(load, generate)

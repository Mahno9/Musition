"""Stable Audio Open worker. Params mirror StableAudioPipeline.__call__."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

WEIGHTS = "D:/AIModels/SoundGen/stable-audio-open-1.0"
PIPE = None


def load():
    global PIPE
    import torch
    from diffusers import StableAudioPipeline
    PIPE = StableAudioPipeline.from_pretrained(WEIGHTS, torch_dtype=torch.float16).to("cuda")


def generate(p):
    import numpy as np
    import soundfile as sf
    import torch

    steps = int(p.get("num_inference_steps", 100))
    seed = int(p["seed"]) if str(p.get("seed", "")).strip() not in ("", "-1") else \
        int.from_bytes(os.urandom(4), "little")
    n = max(1, int(p.get("num_waveforms_per_prompt", 1)))

    kw = {}
    ref = p.get("ref_audio_path")
    if ref:
        data, sr = sf.read(ref, dtype="float32", always_2d=True)
        kw["initial_audio_waveforms"] = torch.from_numpy(data.T).unsqueeze(0).to("cuda", torch.float16)
        kw["initial_audio_sampling_rate"] = sr

    audio = PIPE(
        p.get("prompt", ""),
        negative_prompt=p.get("negative_prompt") or None,
        num_inference_steps=steps,
        audio_end_in_s=float(p.get("audio_end_in_s", 10)),
        guidance_scale=float(p.get("guidance_scale", 7.0)),
        num_waveforms_per_prompt=n,
        generator=torch.Generator("cuda").manual_seed(seed),
        callback=lambda i, t, l: common.set_progress(i + 1, steps),
        callback_steps=1,
        **kw,
    ).audios

    stem, ext = os.path.splitext(p["out_path"])
    paths = []
    for i in range(len(audio)):
        path = p["out_path"] if i == 0 else f"{stem}_{i}{ext}"
        sf.write(path, audio[i].T.float().cpu().numpy(), PIPE.vae.sampling_rate)
        paths.append(path)
    return paths, {"seed": seed}


if __name__ == "__main__":
    common.serve(load, generate)

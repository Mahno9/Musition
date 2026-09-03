"""AudioGen worker. Params mirror AudioGen.set_generation_params."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

MODEL = None


def load():
    global MODEL
    import torch
    from audiocraft.models import AudioGen
    MODEL = AudioGen.get_pretrained("facebook/audiogen-medium")
    MODEL.set_custom_progress_callback(common.set_progress)


def generate(p):
    import torch
    from audiocraft.data.audio import audio_write

    MODEL.set_generation_params(
        duration=float(p.get("duration", 5)),
        use_sampling=bool(p.get("use_sampling", True)),
        top_k=int(p.get("top_k", 250)),
        top_p=float(p.get("top_p", 0.0)),
        temperature=float(p.get("temperature", 1.0)),
        cfg_coef=float(p.get("cfg_coef", 3.0)),
        two_step_cfg=bool(p.get("two_step_cfg", False)),
    )
    seed = int(p["seed"]) if str(p.get("seed", "")).strip() not in ("", "-1") else \
        int.from_bytes(os.urandom(4), "little")
    torch.manual_seed(seed)

    wav = MODEL.generate([p.get("prompt", "")], progress=True)
    stem = os.path.splitext(p["out_path"])[0]
    path = audio_write(stem, wav[0].cpu(), MODEL.sample_rate, strategy="loudness")
    return [str(path)], {"seed": seed}


if __name__ == "__main__":
    common.serve(load, generate)

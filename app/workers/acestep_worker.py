"""ACE-Step worker. Full pipeline API: text2music, audio2audio, repaint, edit, LoRA."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

PIPE = None


def load():
    global PIPE
    import acestep.pipeline_ace_step as pas
    # Resolved here, not at import: importing this module must not need the env var.
    checkpoint = os.path.join(common.models_dir(), "ace-step-cache", "checkpoints",
                              "ACE-Step-v1-3.5B")
    pas.tqdm = common.progress_tqdm(pas.tqdm)  # real % from the diffusion loop
    PIPE = pas.ACEStepPipeline(checkpoint_dir=checkpoint, dtype="bfloat16")
    PIPE.load_checkpoint(checkpoint)


def _seeds(v):
    """'1, 2' / '' / None -> list[int] | None (pipeline randomises on None)."""
    s = str(v or "").strip()
    if not s:
        return None
    try:
        return [int(x) for x in s.replace(",", " ").split()]
    except ValueError:
        return None


def generate(p):
    task = p.get("task") or "text2music"
    a2a = bool(p.get("audio2audio_enable")) and bool(p.get("ref_audio_input"))

    # With a file save_path every batch item overwrites the same file; a
    # directory makes the pipeline emit one numbered file per item.
    bs = max(1, int(p.get("batch_size", 1)))
    save_path = p["out_path"]
    if bs > 1:
        save_path = os.path.splitext(save_path)[0]
        os.makedirs(save_path, exist_ok=True)

    out = PIPE(
        format="wav",
        audio_duration=float(p.get("audio_duration", 60)),
        prompt=p.get("prompt", ""),
        lyrics=p.get("lyrics", "") or "",
        infer_step=int(p.get("infer_step", 60)),
        guidance_scale=float(p.get("guidance_scale", 15.0)),
        scheduler_type=p.get("scheduler_type", "euler"),
        cfg_type=p.get("cfg_type", "apg"),
        omega_scale=float(p.get("omega_scale", 10.0)),
        manual_seeds=_seeds(p.get("manual_seeds")),
        guidance_interval=float(p.get("guidance_interval", 0.5)),
        guidance_interval_decay=float(p.get("guidance_interval_decay", 0.0)),
        min_guidance_scale=float(p.get("min_guidance_scale", 3.0)),
        use_erg_tag=bool(p.get("use_erg_tag", True)),
        use_erg_lyric=bool(p.get("use_erg_lyric", True)),
        use_erg_diffusion=bool(p.get("use_erg_diffusion", True)),
        oss_steps=p.get("oss_steps") or None,
        guidance_scale_text=float(p.get("guidance_scale_text", 0.0)),
        guidance_scale_lyric=float(p.get("guidance_scale_lyric", 0.0)),
        audio2audio_enable=a2a,
        ref_audio_strength=float(p.get("ref_audio_strength", 0.5)),
        ref_audio_input=p.get("ref_audio_input") or None,
        lora_name_or_path=p.get("lora_name_or_path") or "none",
        lora_weight=float(p.get("lora_weight", 1.0)),
        retake_seeds=_seeds(p.get("retake_seeds")),
        retake_variance=float(p.get("retake_variance", 0.5)),
        task=task,
        repaint_start=int(p.get("repaint_start", 0)),
        repaint_end=int(p.get("repaint_end", 0)),
        src_audio_path=p.get("src_audio_path") or None,
        edit_target_prompt=p.get("edit_target_prompt") or None,
        edit_target_lyrics=p.get("edit_target_lyrics") or None,
        edit_n_min=float(p.get("edit_n_min", 0.0)),
        edit_n_max=float(p.get("edit_n_max", 1.0)),
        edit_n_avg=int(p.get("edit_n_avg", 1)),
        save_path=save_path,
        batch_size=bs,
    )
    paths, info = out[:-1], out[-1]
    return list(paths), {"seed": info.get("actual_seeds"), "retake_seeds": info.get("retake_seeds")}


if __name__ == "__main__":
    common.serve(load, generate)

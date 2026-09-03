import sys
import torch
import soundfile as sf
from diffusers import StableAudioPipeline

prompt = sys.argv[1] if len(sys.argv) > 1 else "a warm ambient pad with soft wind"
duration = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0

pipe = StableAudioPipeline.from_pretrained(
    "D:/AIModels/SoundGen/stable-audio-open-1.0", torch_dtype=torch.float16
)
pipe = pipe.to("cuda")

audio = pipe(
    prompt,
    negative_prompt="Low quality.",
    num_inference_steps=100,
    audio_end_in_s=duration,
    num_waveforms_per_prompt=1,
    generator=torch.Generator("cuda").manual_seed(0),
).audios

output = audio[0].T.float().cpu().numpy()
sf.write("output.wav", output, pipe.vae.sampling_rate)
print("wrote output.wav")

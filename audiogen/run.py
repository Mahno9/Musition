import sys
from audiocraft.models import AudioGen
from audiocraft.data.audio import audio_write

prompt = sys.argv[1] if len(sys.argv) > 1 else "a dog barking and footsteps on gravel"
duration = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0

model = AudioGen.get_pretrained("facebook/audiogen-medium")
model.set_generation_params(duration=duration)

wav = model.generate([prompt])
audio_write("output", wav[0].cpu(), model.sample_rate, strategy="loudness")
print("wrote output.wav")

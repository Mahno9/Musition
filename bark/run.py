import sys
from scipy.io.wavfile import write as write_wav
from bark import SAMPLE_RATE, generate_audio, preload_models

text = sys.argv[1] if len(sys.argv) > 1 else "[laughs] Hey, this is Bark running locally. [sighs] Not bad!"

preload_models()
audio = generate_audio(text)
write_wav("output.wav", SAMPLE_RATE, audio)
print("wrote output.wav")

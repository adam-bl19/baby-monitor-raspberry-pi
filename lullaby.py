import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100
DURATION = 60  # seconds


def generate_lullaby(fs=SAMPLE_RATE, duration=DURATION):
    """Generate a simple DSP lullaby: 440Hz sine tone mixed with soft white noise."""
    t = np.linspace(0, duration, int(fs * duration))
    tone = 0.5 * np.sin(2 * np.pi * 440 * t)
    noise = np.random.normal(0, 0.1, size=t.shape)
    lullaby = tone + noise
    # Normalise to prevent clipping
    lullaby = lullaby / np.max(np.abs(lullaby)) * 0.8
    return lullaby.astype(np.float32)


def play_lullaby():
    print("[LULLABY] Generating and playing lullaby...")
    audio = generate_lullaby()
    sd.play(audio, samplerate=SAMPLE_RATE)
    sd.wait()
    print("[LULLABY] Playback complete.")


if __name__ == "__main__":
    play_lullaby()

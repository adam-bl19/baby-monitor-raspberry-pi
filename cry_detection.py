import sounddevice as sd
import numpy as np
import smtplib
import subprocess
import time
import os
from email.mime.text import MIMEText
from scipy.io import wavfile

# --- Configuration (set via environment variables) ---
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

LOUDNESS_THRESHOLD = 0.12   # RMS threshold for loudness detection
SIMILARITY_THRESHOLD = 0.8  # Minimum similarity score to trigger cry event
LOUD_BLOCK_THRESHOLD = 5    # Number of loud blocks in 1 second to confirm cry
EMAIL_COOLDOWN = 60         # Seconds between email alerts
LULLABY_COOLDOWN = 90       # Seconds between lullaby activations
SAMPLE_RATE = 44100
BLOCK_SIZE = 2048

# --- State ---
loud_blocks = []
last_email_time = 0
last_lullaby_time = 0
cry_reference = None


def load_reference(path="cry_samples/cry_sample_01.wav"):
    """Load a reference cry WAV file for similarity matching."""
    try:
        rate, data = wavfile.read(path)
        if data.ndim > 1:
            data = data[:, 0]
        return data.astype(np.float32) / np.iinfo(np.int16).max
    except Exception as e:
        print(f"[WARN] Could not load reference sample: {e}")
        return None


def compare(indata, reference, n=2048):
    """Simple cross-correlation similarity score between two audio buffers."""
    if reference is None:
        return 0.0
    a = indata.flatten()[:n]
    b = reference[:n]
    min_len = min(len(a), len(b))
    if min_len == 0:
        return 0.0
    a, b = a[:min_len], b[:min_len]
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(np.dot(a, b) / norm)


def send_email():
    """Send an alert email via Gmail SMTP."""
    try:
        msg = MIMEText("Baby crying detected by Raspberry Pi baby monitor.")
        msg["Subject"] = "Baby Monitor Alert"
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        print("[EMAIL] Alert sent.")
    except Exception as e:
        print(f"[EMAIL] Failed to send: {e}")


def trigger_lullaby():
    """Launch lullaby playback as a separate process."""
    subprocess.Popen(["python3", "lullaby.py"])
    print("[LULLABY] Playback started.")


def callback(indata, frames, time_info, status):
    """Audio stream callback — called by OS audio subsystem on each buffer."""
    global loud_blocks, last_email_time, last_lullaby_time

    volume_norm = np.sqrt(np.mean(indata ** 2))
    similarity_score = compare(indata, cry_reference)

    print(f"[AUDIO] Volume: {volume_norm:.5f}  Similarity: {similarity_score:.3f}", end="\r")

    if volume_norm > LOUDNESS_THRESHOLD:
        loud_blocks.append(time.time())

    # Keep only blocks within the last second
    now = time.time()
    loud_blocks = [t for t in loud_blocks if now - t < 1.0]

    if (
        volume_norm > LOUDNESS_THRESHOLD
        and similarity_score > SIMILARITY_THRESHOLD
        and len(loud_blocks) >= LOUD_BLOCK_THRESHOLD
    ):
        print("\n[DETECTED] BABY IS CRYING!")
        print(f"[AUDIO] Volume: {volume_norm:.5f}")
        print(f"[AUDIO] LoudBlocks: {len(loud_blocks)}")

        if now - last_email_time > EMAIL_COOLDOWN:
            send_email()
            last_email_time = now

        if now - last_lullaby_time > LULLABY_COOLDOWN:
            trigger_lullaby()
            last_lullaby_time = now


def main():
    global cry_reference
    cry_reference = load_reference()
    print("[INFO] Baby monitor cry detection started. Press Ctrl+C to stop.")
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=1,
        callback=callback
    ):
        while True:
            time.sleep(0.1)


if __name__ == "__main__":
    main()

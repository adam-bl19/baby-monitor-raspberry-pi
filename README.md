# Raspberry Pi Baby Monitor

An embedded baby monitor built on a **Raspberry Pi 4 Model B**. It listens for crying, responds by itself, and keeps the parent informed. This was built for the Operating Systems module at London South Bank University by team *The Honoured Ones* (two members).

The code was written jointly with my teammate [@MattOzt](https://github.com/MattOzt), whose repo is [MattOzt/raspberry-pi-baby-monitor](https://github.com/MattOzt/raspberry-pi-baby-monitor).

📄 **Full report:** [`Baby_Monitor_Report.docx`](Baby_Monitor_Report.docx)
🎥 **Video demo:** https://www.youtube.com/watch?v=MdiwGGw-gbM

## What it does

When a cry is detected, the Pi sets off three things at once:

1. **🔔 Email alert.** It sends a Gmail SMTP notification to the caregiver. In testing, alerts arrived within 1–3 seconds of the cry.
2. **🎵 Lullaby playback.** It starts a soothing lullaby, generated in code, through the speaker.
3. **📹 CCTV stream.** A live MJPEG camera feed is served over HTTP, so the parent can check from any browser.

A **Windows GUI** remote control (over SSH/HTTP) can start and stop each module without touching the Pi.

## How cry detection works

Loud isn't the same as crying, so detection works in two stages:

- **Stage 1: RMS loudness.** Audio from a USB microphone is analysed in 20–50 ms frames. A sudden jump in RMS amplitude marks a possible cry.
- **Stage 2: similarity matching.** The frame is compared against recorded cry samples. Only a score above the similarity threshold counts as a cry, and it also needs several loud blocks within one second. Both thresholds are constants at the top of `cry_detection.py`.

The second stage filters out the false positives that loudness alone would set off, such as talking, footsteps or something dropped on the floor.

## Architecture

```
USB mic ──► cry detection (RMS + similarity) ──┬──► email alert   (smtplib)
                                               ├──► lullaby        (subprocess)
                                               └──► CCTV stream    (Flask + libcamera, MJPEG)

Windows GUI ──SSH/HTTP──► start / stop modules on the Pi
```

Each module runs as its own process, and the Linux **Completely Fair Scheduler** shares CPU time between them. That means the real-time audio thread keeps getting CPU time even while video encoding is running. The report covers this OS-level behaviour in detail: process management, scheduling, buffer handling and the file system.

## Code

| File | Role |
|------|------|
| `cry_detection.py` | Main process: audio capture, RMS + similarity detection, triggers alerts and the lullaby (with cooldowns) |
| `lullaby.py` | Generates and plays the lullaby; launched as a subprocess |
| `cctv_stream.py` | Flask server for the Picamera2 MJPEG stream on port 5000 |
| `remote_gui.py` | Windows Tkinter controller that starts modules on the Pi over SSH (Paramiko) |
| `baby-monitor.service` | systemd unit: starts on boot, restarts on failure |

## Setup

On the Pi:

```bash
sudo apt install python3-venv python3-picamera2 libatlas-base-dev alsa-utils
git clone https://github.com/adam-bl19/baby-monitor-rasberry-pi ~/baby_monitor
cd ~/baby_monitor
python3 -m venv --system-site-packages venv   # system site-packages so picamera2 is visible
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env    # then fill in your Gmail app password etc.
mkdir cry_samples       # put a reference cry as cry_samples/cry_sample_01.wav
```

Run manually. The scripts read config from environment variables, so load `.env` first:

```bash
set -a; source .env; set +a
python3 cry_detection.py          # main module
python3 cctv_stream.py            # stream at http://<pi-ip>:5000
```

Or run it as a service. The unit loads `.env` itself through `EnvironmentFile`:

```bash
sudo cp baby-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now baby-monitor
```

On Windows, set `PI_HOST`, `PI_USER` and `PI_PASSWORD` in your environment, then run `python remote_gui.py`.

## Hardware

- Raspberry Pi 4 Model B (quad-core Cortex-A72)
- Raspberry Pi Camera Module
- USB microphone + USB sound card
- 32 GB microSD card, Raspberry Pi OS 64-bit, set up headless over SSH

## Software

Python 3 (in a venv) · sounddevice · NumPy · Flask · libcamera · smtplib · SSH · htop for benchmarking

## Performance (measured on the Pi)

| Workload | CPU | Memory |
|----------|-----|--------|
| Idle | 0–1% | ~260 MB baseline |
| Cry detection only | ~2.5–8% (depends on ambient noise) | — |
| All modules combined | Scales predictably, no starvation | ~340 MB |

Temperatures stayed stable under long combined runs, and there were no resource leaks or growing memory use.

## Possible extensions

The report's scalability section names further features the system could take on, such as more sensors and cloud-based logging. It also notes the extra CPU load these would add.

---

*This is academic work published for portfolio purposes. Copying or resubmitting it counts as plagiarism, and university similarity checkers will flag it.*

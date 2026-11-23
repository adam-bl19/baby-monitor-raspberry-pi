import tkinter as tk
from tkinter import messagebox
import paramiko
import threading
import os

# --- Configuration ---
PI_HOST = os.environ.get("PI_HOST", "192.168.x.x")
PI_USER = os.environ.get("PI_USER", "pi")
PI_PASSWORD = os.environ.get("PI_PASSWORD", "")


def get_ssh():
    """Create and return an SSH connection to the Raspberry Pi."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_HOST, username=PI_USER, password=PI_PASSWORD)
    return ssh


def run_remote(command, feedback="Command sent."):
    """Execute a command on the Pi in a background thread."""
    def task():
        try:
            ssh = get_ssh()
            ssh.exec_command(command)
            ssh.close()
            status_var.set(feedback)
        except Exception as e:
            messagebox.showerror("SSH Error", str(e))
    threading.Thread(target=task, daemon=True).start()


# --- GUI ---
root = tk.Tk()
root.title("Baby Monitor Remote Control")
root.geometry("360x280")
root.resizable(False, False)

status_var = tk.StringVar(value="Ready.")

tk.Label(root, text="Baby Monitor Remote Control", font=("Arial", 14, "bold")).pack(pady=10)

tk.Button(root, text="▶ Start Cry Detection", width=28,
          command=lambda: run_remote("python3 cry_detection.py &", "Cry detection started.")).pack(pady=4)

tk.Button(root, text="⏹ Stop Cry Detection", width=28,
          command=lambda: run_remote("pkill -f cry_detection.py", "Cry detection stopped.")).pack(pady=4)

tk.Button(root, text="📷 Start CCTV Stream", width=28,
          command=lambda: run_remote("python3 cctv_stream.py &", "CCTV stream started.")).pack(pady=4)

tk.Button(root, text="⏹ Stop CCTV Stream", width=28,
          command=lambda: run_remote("pkill -f cctv_stream.py", "CCTV stream stopped.")).pack(pady=4)

tk.Button(root, text="🎵 Play Lullaby", width=28,
          command=lambda: run_remote("python3 lullaby.py &", "Lullaby playing.")).pack(pady=4)

tk.Label(root, textvariable=status_var, fg="green").pack(pady=8)

root.mainloop()

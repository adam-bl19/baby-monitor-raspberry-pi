from flask import Flask, Response
from picamera2 import Picamera2
import cv2

app = Flask(__name__)
camera = Picamera2()
camera.configure(camera.create_video_configuration(main={"size": (640, 480)}))
camera.start()


def generate_frames():
    """Continuously yield JPEG-encoded frames for MJPEG streaming."""
    while True:
        frame = camera.capture_array()
        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


@app.route("/")
def index():
    return """
    <html><body>
    <h2>Baby Monitor CCTV Feed</h2>
    <img src="/video_feed" width="640" height="480" />
    </body></html>
    """


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    print("[CCTV] Server running on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True)

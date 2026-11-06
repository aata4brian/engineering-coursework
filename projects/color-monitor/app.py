"""Dashboard lokal untuk ESP32-CAM: streaming, rotasi, dan deteksi warna.

Jalankan: python app.py --ip 192.0.2.10
URL: http://127.0.0.1:5000
"""

import argparse
import json
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 5000
STALE_SECONDS = 5

# Hue HSV OpenCV: 0 sampai 179. Merah melewati batas 0/179.
COLORS = {
    "Merah": [(0, 10), (170, 179)],
    "Oranye": [(11, 22)],
    "Kuning": [(23, 36)],
    "Hijau": [(37, 85)],
    "Biru": [(90, 135)],
}
PALETTE = {
    "Merah": (60, 70, 240),
    "Oranye": (40, 155, 255),
    "Kuning": (50, 230, 255),
    "Hijau": (75, 210, 70),
    "Biru": (245, 150, 45),
}


class CameraProcessor:
    def __init__(self, stream_url):
        self.stream_url = stream_url
        self.lock = threading.Lock()
        self.selected_color = "Semua"
        self.min_area = 180
        self.connected = False
        self.status = "Menunggu koneksi kamera..."
        self.jpeg = None
        self.frame_id = 0
        self.last_frame_at = 0.0
        self.fps = 0.0
        self.detections = []
        self.closest = None

    def set_settings(self, color=None, min_area=None):
        if color is not None and color not in ("Semua", *COLORS):
            raise ValueError("Pilihan warna tidak dikenali")
        if min_area is not None and (type(min_area) is not int or not 30 <= min_area <= 5000):
            raise ValueError("Luas minimum harus bilangan bulat 30 sampai 5000")
        with self.lock:
            if color is not None:
                self.selected_color = color
            if min_area is not None:
                self.min_area = min_area

    def get_snapshot(self):
        with self.lock:
            age = time.monotonic() - self.last_frame_at
            fresh = self.connected and age < STALE_SECONDS
            return self.frame_id, self.jpeg if fresh else None

    def get_state(self):
        with self.lock:
            age = time.monotonic() - self.last_frame_at if self.last_frame_at else None
            fresh = self.connected and age is not None and age < STALE_SECONDS
            return {
                "connected": fresh,
                "status": "Frame terakhir kedaluwarsa" if self.connected and not fresh else self.status,
                "fps": round(self.fps, 1) if fresh else 0,
                "color": self.selected_color,
                "min_area": self.min_area,
                "detections": self.detections if fresh else [],
                "closest": self.closest if fresh else None,
                "age_seconds": round(age, 1) if age is not None else None,
            }

    def process_frame(self, frame):
        # Rotasi benar-benar dilakukan pada frame hasil kamera, ke kanan 90 derajat.
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        height, width = frame.shape[:2]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        with self.lock:
            color_mode = self.selected_color
            min_area = self.min_area

        names = list(COLORS) if color_mode == "Semua" else [color_mode]
        kernel = np.ones((3, 3), np.uint8)
        detections = []

        for name in names:
            mask = np.zeros((height, width), dtype=np.uint8)
            for low_hue, high_hue in COLORS[name]:
                mask |= cv2.inRange(
                    hsv,
                    np.array([low_hue, 80, 65], dtype=np.uint8),
                    np.array([high_hue, 255, 255], dtype=np.uint8),
                )
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < min_area:
                    continue
                x, y, w, h = cv2.boundingRect(contour)
                bottom_y = y + h - 1
                gap_px = max(0, (height - 1) - bottom_y)
                gap_pct = gap_px * 100.0 / max(1, height - 1)
                detections.append({
                    "warna": name,
                    "luas_px2": round(float(area)),
                    "x": int(x), "y": int(y),
                    "lebar": int(w), "tinggi": int(h),
                    "jarak_bawah_px": int(gap_px),
                    "jarak_bawah_persen": round(gap_pct, 1),
                    "kedekatan_bawah_persen": round(100.0 - gap_pct, 1),
                })

        detections.sort(key=lambda d: (d["jarak_bawah_px"], -d["luas_px2"]))
        closest = detections[0] if detections else None

        # Overlay anotasi
        cv2.line(frame, (0, height - 1), (width - 1, height - 1), (235, 235, 235), 2)
        for index, det in enumerate(detections[:20]):
            x, y, w, h = det["x"], det["y"], det["lebar"], det["tinggi"]
            color = PALETTE[det["warna"]]
            thickness = 3 if index == 0 else 2
            cv2.rectangle(frame, (x, y), (x + w - 1, y + h - 1), color, thickness)
            label = f'{det["warna"]}  {det["jarak_bawah_px"]} px'
            cv2.putText(
                frame, label, (max(0, x), max(16, y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.44, color, 1, cv2.LINE_AA
            )
            if index == 0:
                cx = min(width - 1, x + w // 2)
                cv2.line(frame, (cx, y + h - 1), (cx, height - 1), color, 2)

        banner = "ROTASI 90 DERAJAT KANAN"
        cv2.rectangle(frame, (0, 0), (width, 22), (15, 22, 35), -1)
        cv2.putText(frame, banner, (6, 15), cv2.FONT_HERSHEY_SIMPLEX,
                    0.38, (245, 245, 245), 1, cv2.LINE_AA)

        ok, output = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
        if not ok:
            return

        with self.lock:
            self.jpeg = output.tobytes()
            self.frame_id += 1
            self.last_frame_at = time.monotonic()
            self.connected = True
            self.status = "Streaming aktif"
            self.detections = detections
            self.closest = closest

    def receive_forever(self):
        count, start = 0, time.monotonic()
        while True:
            try:
                with self.lock:
                    self.status = "Menghubungkan ke ESP32-CAM..."
                    self.connected = False

                req = Request(self.stream_url, headers={"User-Agent": "RobotColorMonitor/1.0"})
                with urlopen(req, timeout=10) as response:
                    if response.status != 200:
                        raise RuntimeError(f"HTTP {response.status}")
                    raw = bytearray()
                    while True:
                        chunk = response.read(4096)
                        if not chunk:
                            raise ConnectionError("Aliran kamera terputus")
                        raw.extend(chunk)
                        # Ekstraksi JPEG dari multipart MJPEG (ffd8...ffd9)
                        while True:
                            start_jpg = raw.find(b"\xff\xd8")
                            if start_jpg < 0:
                                if len(raw) > 4096:
                                    del raw[:-2]
                                break
                            end_jpg = raw.find(b"\xff\xd9", start_jpg + 2)
                            if end_jpg < 0:
                                if start_jpg > 0:
                                    del raw[:start_jpg]
                                if len(raw) > 2_000_000:
                                    raw.clear()
                                break
                            jpg = bytes(raw[start_jpg:end_jpg + 2])
                            del raw[:end_jpg + 2]
                            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if frame is not None:
                                self.process_frame(frame)
                                count += 1
                                now = time.monotonic()
                                if now - start >= 1.0:
                                    with self.lock:
                                        self.fps = count / (now - start)
                                    count, start = 0, now
            except Exception as exc:
                with self.lock:
                    self.connected = False
                    self.fps = 0
                    self.status = f"Tidak dapat menerima video: {exc}"
                time.sleep(1.5)


class Handler(BaseHTTPRequestHandler):
    server_version = "RobotMonitor/1.0"

    def log_message(self, fmt, *args):
        # Tidak mencetak satu baris log untuk setiap frame dan polling.
        if not self.path.startswith(("/video", "/api/state")):
            super().log_message(fmt, *args)

    def send_bytes(self, content, mimetype, code=200):
        self.send_response(code)
        self.send_header("Content-Type", mimetype)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path == "/":
            return self.send_bytes((ROOT / "dashboard.html").read_bytes(),
                                   "text/html; charset=utf-8")
        if self.path == "/api/state":
            return self.send_bytes(json.dumps(self.server.camera.get_state()).encode(),
                                   "application/json")
        if self.path == "/video":
            return self.video_stream()
        self.send_error(404, "Tidak ditemukan")

    def do_POST(self):
        if self.path != "/api/settings":
            return self.send_error(404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1024:
                raise ValueError("Ukuran permintaan tidak valid")
            data = json.loads(self.rfile.read(length).decode())
            if not isinstance(data, dict):
                raise ValueError("Pengaturan harus berupa objek JSON")
            self.server.camera.set_settings(data.get("color"), data.get("min_area"))
            self.send_bytes(b'{"ok":true}', "application/json")
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.send_bytes(json.dumps({"error": str(exc)}).encode(),
                            "application/json", 400)

    def video_stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.end_headers()
        previous_id = -1
        try:
            while True:
                frame_id, jpeg = self.server.camera.get_snapshot()
                if jpeg and frame_id != previous_id:
                    previous_id = frame_id
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(jpeg)}\r\n\r\n".encode())
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
                time.sleep(0.035)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass


def main():
    parser = argparse.ArgumentParser(description="Dashboard deteksi warna ESP32-CAM")
    parser.add_argument("--ip", required=True, help="IP ESP32-CAM dari Serial Monitor")
    parser.add_argument("--port", type=int, default=PORT, help="Port dashboard lokal")
    args = parser.parse_args()
    ip = args.ip.strip()
    # Terima alamat IP saja, atau URL lengkap jika diperlukan.
    if ip.startswith("http://"):
        stream_url = ip.rstrip("/")
        if not stream_url.endswith("/stream"):
            stream_url += ":81/stream" if ":" not in stream_url.split("//", 1)[1] else "/stream"
    else:
        stream_url = f"http://{ip}:81/stream"

    camera = CameraProcessor(stream_url)
    threading.Thread(target=camera.receive_forever, daemon=True).start()

    httpd = ThreadingHTTPServer((HOST, args.port), Handler)
    httpd.camera = camera
    print("\n=== MONITOR ESP32-CAM ===")
    print(f"Sumber video : {stream_url}")
    print(f"Dashboard    : http://{HOST}:{args.port}")
    print("Putar kanan 90 derajat + deteksi warna dilakukan di laptop.")
    print("Tekan Ctrl+C untuk menghentikan.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()

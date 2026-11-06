import json
import sys
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import cv2
import numpy as np

from app import CameraProcessor, Handler

# Buat frame dalam orientasi dashboard, lalu balik rotasi untuk meniru sumber.
upright = np.zeros((120, 160, 3), dtype=np.uint8)
upright[75:100, 20:50] = (0, 0, 255)
upright[25:50, 80:120] = (255, 0, 0)
upright[110:112, 140:142] = (0, 255, 0)
source = cv2.rotate(upright, cv2.ROTATE_90_COUNTERCLOCKWISE)
camera = CameraProcessor(None)

with patch("app.time.monotonic", return_value=100):
    camera.process_frame(source)
    state = camera.get_state()
    _, jpeg = camera.get_snapshot()
    image = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
    assert image.shape == upright.shape
    assert state["connected"]
    assert [(d["warna"], d["jarak_bawah_px"]) for d in state["detections"]] == [
        ("Merah", 20), ("Biru", 70)
    ]
    assert state["closest"]["warna"] == "Merah"
    try:
        camera.set_settings("Biru", 0)
    except ValueError:
        assert camera.get_state()["color"] == "Semua"
    else:
        raise AssertionError("Luas minimum 0 diterima.")
    camera.set_settings("Biru", 180)
    camera.process_frame(source)
    assert camera.get_state()["closest"]["warna"] == "Biru"
    camera.process_frame(np.zeros_like(source))
    assert camera.get_state()["closest"] is None

with patch("app.time.monotonic", return_value=104):
    camera.process_frame(source)
    camera.fps = 12
with patch("app.time.monotonic", return_value=109):
    stale = camera.get_state()
    assert stale["connected"] is False
    assert stale["closest"] is None and stale["detections"] == []
    assert stale["fps"] == 0 and camera.get_snapshot()[1] is None

camera = CameraProcessor(None)
camera.set_settings("Biru", 180)
with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
    server.camera = camera
    worker = Thread(target=server.serve_forever)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base, timeout=2) as response:
            assert b'id="camera-frame"' in response.read()
        with urlopen(base + "/api/state", timeout=2) as response:
            assert not json.load(response)["connected"]
        for body in (b"[]", b'{"color":"Merah","min_area":0}'):
            request = Request(base + "/api/settings", data=body, method="POST")
            try:
                urlopen(request, timeout=2).close()
            except HTTPError as error:
                assert error.code == 400
                error.close()
            else:
                raise AssertionError("Pengaturan invalid diterima.")
        assert camera.get_state()["color"] == "Biru"
        request = Request(base + "/api/settings", data=b'{"color":"Merah","min_area":30}')
        with urlopen(request, timeout=2) as response:
            assert json.load(response)["ok"]
        assert camera.get_state()["color"] == "Merah"
    finally:
        server.shutdown()
        worker.join()

if __name__ == "__main__":
    print(json.dumps(state["detections"], indent=2))
    if "--save-example" in sys.argv:
        Path("example.jpg").write_bytes(jpeg)

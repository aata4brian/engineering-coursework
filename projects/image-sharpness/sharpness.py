"""Empat ukuran fokus dari latihan citra PCB."""

import argparse
import json

import numpy as np
from PIL import Image


def brenner(I):
    d = I[:,2:] - I[:,:-2]
    return np.sum(d*d, dtype=np.float64)

def squared_gradient(I):
    d = I[:,1:] - I[:,:-1]
    return np.sum(d*d, dtype=np.float64)

def tenenbaum(I):
    # valid Sobel responses, written as pairwise differences to match analytical FLOPs
    a00=I[:-2,:-2]; a01=I[:-2,1:-1]; a02=I[:-2,2:]
    a10=I[1:-1,:-2]; a12=I[1:-1,2:]
    a20=I[2:,:-2]; a21=I[2:,1:-1]; a22=I[2:,2:]
    gx=(a02-a00)+2*(a12-a10)+(a22-a20)
    gy=(a20-a00)+2*(a21-a01)+(a22-a02)
    return np.sum(gx*gx + gy*gy, dtype=np.float64)

def mdct(I):
    # K = v v^T, v=[1,1,-1,-1]. Correlation/convolution sign flip is irrelevant after squaring.
    h = (I[:,:-3] + I[:,1:-2]) - (I[:,2:-1] + I[:,3:])
    r = (h[:-3,:] + h[1:-2,:]) - (h[2:-1,:] + h[3:,:])
    return np.sum(r*r, dtype=np.float64)

METHODS={'Brenner':brenner,'Tenenbaum':tenenbaum,'Squared gradient':squared_gradient,'MDCT':mdct}


def measure(image):
    image = np.asarray(image, dtype=np.float64)
    if image.ndim != 2 or min(image.shape) < 4:
        raise ValueError("Masukan harus grayscale dengan ukuran minimal 4 × 4.")
    if not np.isfinite(image).all():
        raise ValueError("Intensitas harus bernilai hingga.")
    return {name: float(method(image)) for name, method in METHODS.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    args = parser.parse_args()
    with Image.open(args.image) as picture:
        rgb = np.asarray(picture.convert("RGB"), dtype=np.float64)
    gray = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    print(json.dumps(measure(gray), indent=2))

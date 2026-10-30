#!/usr/bin/env python3
"""Seven-second portal-only animation cut from the user's exact reference image.

The original crystal C, full-screen scenery and Android-drawn wordmark are
unchanged. ONLY a feathered vortex in the C's opening is animated. In
particular, never bake a second wordmark into the video: Android's
CrystalWordmark view is drawn ABOVE this silent video, at all times.
"""
from pathlib import Path
import importlib.util
import math
import subprocess
import tempfile

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Charoite_Reference_Portal_Only_7s.mp4"
SOURCE = ROOT / "next-generation/assets/charoite_portal_reference_inner.jpg"
WIDTH, HEIGHT, FPS, SECONDS = 480, 920, 24, 7

# Placement is relative to the same 960x1840 portrait art used by
# CrystalArtwork; these are 480x920 coordinates in the C's open center.
PORTAL_X, PORTAL_Y = 292, 416
PORTAL_RX, PORTAL_RY = 78, 89


def make_base():
    """Exact same derived portrait art as the native boot ImageView."""
    spec = importlib.util.spec_from_file_location(
        "approved_portrait", ROOT / "next-generation/make_portrait_boot.py")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    master = ROOT / "next-generation/assets/charoite_next_boot_reference.jpg"
    with tempfile.TemporaryDirectory() as tmp:
        portrait = Path(tmp) / "portrait.jpg"
        generator.generate(master, portrait)
        with Image.open(portrait) as art:
            # Do NOT draw a title plaque here. Android draws the original
            # one ON TOP of the video, with no frame-to-frame replacement.
            return np.asarray(art.convert("RGB").resize(
                (WIDTH, HEIGHT), Image.Resampling.LANCZOS), dtype=np.float32)


def make_portal_source():
    """Real swirled violet/black cloud texture cropped from the user screenshot."""
    with Image.open(SOURCE) as image:
        image.load()
        assert image.size == (192, 192), "Unexpected reference crop geometry"
        return np.asarray(image.convert("RGB"), dtype=np.float32)


def smoothstep(a, b, x):
    x = np.clip((x-a)/(b-a), 0, 1)
    return x*x*(3-2*x)


def portal_phase(t):
    # Starts clean and reaches full invisibility by the sound's quiet tail.
    return float(smoothstep(.45, 1.6, t) *
                 (1. - smoothstep(5.05, 6.30, t)))


def render_overlay(t, base, portal_source):
    """Composite the ACTUAL user-provided portal ONLY within the C opening.

    Smooth inner-vortex counterclockwise motion is applied to the cropped
    reference, NOT to the crystal, photo background or wordmark. The ellipse
    is exclusively an alpha feather; no black circular disk is painted.
    Every pixel OUTSIDE the localized portal ROI remains identical to base.
    """
    phase = portal_phase(t)
    if phase == 0.:
        return base
    scene = base.copy()
    x0, y0 = PORTAL_X-PORTAL_RX, PORTAL_Y-PORTAL_RY
    width, height = PORTAL_RX*2, PORTAL_RY*2
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    dx = (xx - PORTAL_RX) / PORTAL_RX
    dy = (yy - PORTAL_RY) / PORTAL_RY
    radius = np.sqrt(dx*dx + dy*dy)
    theta = np.arctan2(-dy, dx)

    # Inverse-map a gently counterclockwise, radially varying rotation.
    # The outer rim is almost stationary, while the purple-black cloud
    # texture spins inward. The source portal's authentic spiral survives.
    twist = .78 * t * np.maximum(0., 1.-radius)**1.3
    sample_angle = theta - twist
    src_x = (96. + 91.*radius*np.cos(sample_angle)).astype(np.float32)
    src_y = (96. - 91.*radius*np.sin(sample_angle)).astype(np.float32)
    warped = cv2.remap(portal_source, src_x, src_y, cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_REFLECT)

    opacity = (1.-smoothstep(.86, .99, radius))*phase
    target = scene[y0:y0+height, x0:x0+width]
    target[:] = (target*(1.-opacity[:,:,None]) +
                 warped*opacity[:,:,None])
    return scene


def main():
    base = make_base()
    portal = make_portal_source()
    ffmpeg = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
              "-f", "rawvideo", "-pixel_format", "rgb24",
              "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", str(FPS),
              "-i", "-", "-an", "-c:v", "libx264", "-preset", "fast",
              "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
              str(OUT)]
    proc = subprocess.Popen(ffmpeg, stdin=subprocess.PIPE)
    storyboard = []
    for frame_index in range(FPS*SECONDS):
        t = frame_index/FPS
        frame = np.uint8(np.clip(render_overlay(t, base, portal), 0, 255))
        proc.stdin.write(frame.tobytes())
        if frame_index in (0, 27, 60, 96, 136, 167):
            storyboard.append(Image.fromarray(frame, "RGB").resize(
                (240, 460), Image.Resampling.LANCZOS))
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("Portal-only MP4 H.264 encoding failed")
    cap = cv2.VideoCapture(str(OUT))
    assert cap.isOpened() and round(cap.get(cv2.CAP_PROP_FRAME_COUNT)) == 168
    assert round(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) == WIDTH
    assert round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) == HEIGHT
    cap.release()
    contact = Image.new("RGB", (720, 920))
    for index, img in enumerate(storyboard):
        contact.paste(img, ((index%3)*240, (index//3)*460))
    contact.save(ROOT / "Charoite_Reference_Portal_Only_7s_Storyboard.jpg", quality=89)
    print("CHAROITE_REFERENCE_PORTAL_ONLY_7_SECONDS=PASS", OUT.stat().st_size)


if __name__ == "__main__":
    main()

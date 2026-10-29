#!/usr/bin/env python3
"""Create a sharper splash-only upscale of the EXISTING approved icon.

This does not invent or change the Charoite launcher artwork. The tiny JPEG
contains limited source detail; sharpening cannot reconstruct unseen pixels.
The splash-only 768px PNG keeps the original composition and is isolated to
Charoite Next. Requires Pillow==11.3.0 in the CI build environment.
"""
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import hashlib
import sys

EXPECTED_SHA256 = "28668d5426e7d7977880b6e8406c14a47972565a7f637a8c16fcd1cde2788aa5"
SIZE = 768

def generate(source, destination):
    source, destination = Path(source), Path(destination)
    if not source.is_file() or destination.exists():
        raise ValueError("Expected verified launcher icon and unused PNG path")
    if hashlib.sha256(source.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Refusing to process unapproved launcher art")
    with Image.open(source) as image:
        if image.format != "JPEG":
            raise ValueError("Approved source must be a JPEG")
        image = image.convert("RGB")
        # Lanczos at a moderate intermediate size gives better edge quality
        # than scaling the tiny JPEG directly with Android bilinear filtering.
        image = image.resize((384, 384), Image.Resampling.LANCZOS)
        image = image.filter(ImageFilter.UnsharpMask(radius=1.45, percent=122,
                                                     threshold=3))
        image = image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
        image = image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=132,
                                                     threshold=2))
        image = ImageEnhance.Contrast(image).enhance(1.04)
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, format="PNG", optimize=True)
    with Image.open(destination) as check:
        if check.size != (SIZE, SIZE) or check.format != "PNG":
            raise ValueError("Invalid boot PNG")
    return SIZE, SIZE

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: generate_high_res_boot_icon.py INPUT.jpg OUTPUT.png")
    print("APPROVED_LAUNCHER_ART_UPSCALE=" + str(generate(sys.argv[1], sys.argv[2])))

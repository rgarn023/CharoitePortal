#!/usr/bin/env python3
"""Recover and enhance the *same* approved art used by Next's launcher icon.

The repository's 128x128 JPEG has a known 12-byte transfer defect.
The stable overlay.py already restores the exact approved launcher bytes.
Next now uses that identical, SHA-256 verified restoration for the boot art.
Neither the stable app nor the original tracked file is modified.

Upscaling is source-faithful and cannot recreate fine details that did not
survive the original 128-pixel JPEG. A true high-resolution source master
would be necessary for a fully sharp large-screen version.
"""
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO
import hashlib

SIZE = 1536
SOURCE_SIZE = (128, 128)
APPROVED_SOURCE_SHA256 = "28668d5426e7d7977880b6e8406c14a47972565a7f637a8c16fcd1cde2788aa5"
# The JPEG has an incomplete 67-byte second quantization table. It is 12
# bytes short before its subsequent valid progressive SOF2 marker.
MISSING_QUANTIZER_BYTES = bytes([24] * 12)


def repaired_jpeg(source):
    # Match the existing, long-standing overlay.py restoration byte for byte.
    # The broken *repository* JPG differs from the intact launcher icon
    # already shipped by Charoite; do not invent replacement quantizers.
    data = Path(source).read_bytes()
    bad_sha = "7c5c8fdf88b71fd23fb01740f516b866108edbf57af962aa50bca599bdd1b338"
    good_sha = APPROVED_SOURCE_SHA256
    digest = hashlib.sha256(data).hexdigest()
    if digest == bad_sha:
        data = data[:108] + bytes([0x82]) * 12 + data[108:]
    elif digest != good_sha:
        raise RuntimeError("Unknown launcher JPEG source; refuse artwork substitution")
    if hashlib.sha256(data).hexdigest() != good_sha:
        raise RuntimeError("Launcher JPEG restoration does not match approved image")
    with Image.open(BytesIO(data)) as verified:
        verified.load()
        if verified.format != "JPEG" or verified.size != SOURCE_SIZE:
            raise RuntimeError("Approved icon is not a complete 128px JPEG")
    return data


def stage_launcher_icon(source, destination):
    dest = Path(destination)
    if not dest.is_file() or dest.suffix != ".jpg":
        raise RuntimeError("Expected Next-only icon resource not present")
    original = Path(source).read_bytes()
    approved = repaired_jpeg(source)
    current = dest.read_bytes()
    if current not in (original, approved):
        raise RuntimeError("Icon resource changed unexpectedly before Next staging")
    # In real Actions, overlay.py already wrote these *exact* approved bytes.
    # Next leaves that same launcher artwork intact, never invents a new icon.
    if current != approved:
        dest.write_bytes(approved)
    return SOURCE_SIZE


def render(destination, source):
    dest = Path(destination)
    if dest.exists() or dest.suffix.lower() != ".png":
        raise ValueError("Require an unused PNG destination")
    with Image.open(BytesIO(repaired_jpeg(source))) as original:
        icon = original.convert("RGB")
    # Preserve the unique spiral, crystalline skyline, lake, and exact colors
    # of the app icon instead of drawing a second unrelated portal.
    intermediate = icon.resize((512, 512), Image.Resampling.LANCZOS)
    intermediate = intermediate.filter(ImageFilter.GaussianBlur(0.28))
    enhanced = intermediate.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    enhanced = enhanced.filter(ImageFilter.UnsharpMask(
        radius=2.7, percent=155, threshold=2))
    enhanced = ImageEnhance.Contrast(enhanced).enhance(1.04)
    dest.parent.mkdir(parents=True, exist_ok=True)
    enhanced.save(dest, "PNG", optimize=True)
    with Image.open(dest) as actual:
        if actual.format != "PNG" or actual.size != (SIZE, SIZE):
            raise RuntimeError("Icon-aligned splash failed to render")
    return SIZE, SIZE


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("Usage: recreate_crystal_portal.py SOURCE_ICON.jpg OUTPUT.png")
    print("CHAROITE_ICON_MATCHED_BOOT_ART=" + str(render(sys.argv[2], sys.argv[1])))

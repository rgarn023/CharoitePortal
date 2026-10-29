#!/usr/bin/env python3
"""Recover and enhance the *same* approved art used by Next's launcher icon.

The repository's 128x128 approved JPEG has a damaged second DQT segment:
12 quantizer bytes are missing immediately before the SOF0 marker. A narrow,
strictly structure-guarded in-memory repair makes it decodable without substituting a
different illustration. The fixed JPEG is staged only into Charoite Next;
the stable app and original tracked file are not modified.

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
# bytes short before its subsequent valid SOF marker.
MISSING_QUANTIZER_BYTES = bytes([24] * 12)


def repaired_jpeg(source):
    data = Path(source).read_bytes()
    # Validate the damaged JPEG's exact segment layout rather than rely on
    # an APK digest from the earlier, separate stable packaging step.
    if len(data) < 1000 or len(data) > 10000:
        raise RuntimeError("Unexpected launcher icon length; inspect artwork")
    if not (data.startswith(bytes.fromhex("ffd8ffe0"))
            and data[89:93] == bytes.fromhex("ffdb0043")
            and data[146:148] == bytes.fromhex("ffc0")
            and data.endswith(bytes.fromhex("ffd9"))):
        raise RuntimeError("Expected recoverable JPEG structure was not found")
    recovered = data[:146] + MISSING_QUANTIZER_BYTES + data[146:]
    with Image.open(BytesIO(recovered)) as image:
        image.load()
        if image.format != "JPEG" or image.size != SOURCE_SIZE:
            raise RuntimeError("Approved icon recovery failed validation")
    return recovered


def stage_launcher_icon(source, destination):
    dest = Path(destination)
    if not dest.is_file() or dest.suffix != ".jpg":
        raise RuntimeError("Expected Next-only icon resource not present")
    # Never alter the repository's tracked source. This is called only after
    # stable overlay.py copied the original resource into Next's build tree.
    if dest.read_bytes() != Path(source).read_bytes():
        raise RuntimeError("Icon resource changed before Next-specific staging")
    dest.write_bytes(repaired_jpeg(source))
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

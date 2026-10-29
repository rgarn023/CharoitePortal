#!/usr/bin/env python3
"""Create the Next splash from the exact artwork used by the installed icon.

The approved launcher asset is a 128x128 JPEG. The previous 1536x1536
procedurally drawn portal had different shapes, so it could never match the
app icon. This source-faithful enhancement preserves the exact composition.
It can improve screen rendering but CANNOT restore detail absent from the
original 128px file; obtain the original high-resolution master when possible.
No network or user files are involved.
"""
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

SIZE = 1536
SOURCE_SIZE = (128, 128)


def render(destination, source):
    dest = Path(destination)
    icon_path = Path(source)
    if dest.exists() or dest.suffix.lower() != ".png":
        raise ValueError("Require an unused PNG destination")
    if not icon_path.is_file():
        raise FileNotFoundError(f"Approved Charoite icon is missing: {icon_path}")
    with Image.open(icon_path) as original:
        if original.format != "JPEG" or original.size != SOURCE_SIZE:
            raise RuntimeError("Approved launcher icon changed; inspect before generating")
        icon = original.convert("RGB")
    # Intermediate steps reduce JPEG compression block edges without adding
    # a new design. High-quality resampling then restores local contrast.
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
            raise RuntimeError("Icon-aligned Charoite Next splash failed to render")
    return SIZE, SIZE


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("Usage: recreate_crystal_portal.py SOURCE_ICON.jpg OUTPUT.png")
    print("CHAROITE_ICON_MATCHED_BOOT_ART=" + str(render(sys.argv[2], sys.argv[1])))

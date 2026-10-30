#!/usr/bin/env python3
"""Prepare Next-only unframed boot art from the EXACT approved launcher image.

The supplied source is an app icon with black, rounded-square outside corners.
Keep the launcher JPG byte-for-byte identical. Flood-remove only the connected
black outside of that outline in a transparent boot foreground, and extend the
approved cosmic image as a purple softly blurred full-screen backdrop.
No new invented artwork and no Photoshop/web dependency.
"""
from collections import deque
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

EXPECTED_SIZE = (1536, 1536)
BLACK_THRESHOLD = 26


def generate(source, foreground, backdrop):
    source = Path(source)
    foreground = Path(foreground)
    backdrop = Path(backdrop)
    if foreground.exists() or backdrop.exists():
        raise ValueError("Refuse to replace previously generated boot art")
    with Image.open(source) as original:
        if original.size != EXPECTED_SIZE:
            raise RuntimeError("Unexpected approved Charoite icon dimensions")
        src = original.convert("RGB")

    w, h = src.size
    pix = src.load()
    alpha = bytearray([255]) * (w*h)
    visited = bytearray(w*h)
    queue = deque(((0,0), (w-1,0), (0,h-1), (w-1,h-1)))
    # Flood ONLY black pixels connected to the outside corners. Interior dark
    # starfields and the picture inside the purple icon border remain intact.
    while queue:
        x, y = queue.popleft()
        k = y*w+x
        if visited[k]:
            continue
        visited[k] = 1
        r, g, b = pix[x,y]
        if max(r,g,b) > BLACK_THRESHOLD:
            continue
        alpha[k] = 0
        if x > 0: queue.append((x-1,y))
        if y > 0: queue.append((x,y-1))
        if x+1 < w: queue.append((x+1,y))
        if y+1 < h: queue.append((x,y+1))

    a = Image.frombytes("L", (w,h), bytes(alpha))
    a = a.filter(ImageFilter.GaussianBlur(1.3))
    front = src.convert("RGBA")
    front.putalpha(a)
    foreground.parent.mkdir(parents=True, exist_ok=True)
    front.save(foreground, format="PNG", optimize=True)
    # This is deliberately a blurred continuation of the same approved scene:
    # full-screen art beyond the sharply rendered foreground, never black.
    inset = 140
    background = ImageOps.fit(src.crop((inset,inset,w-inset,h-inset)),
                              (900,1600), method=Image.Resampling.LANCZOS)
    background = ImageEnhance.Brightness(
        background.filter(ImageFilter.GaussianBlur(34))).enhance(.74)
    backdrop.parent.mkdir(parents=True, exist_ok=True)
    background.save(backdrop, "JPEG", quality=91, optimize=True)
    return foreground, backdrop


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        raise SystemExit("Usage: make_fullbleed_boot.py APPROVED.jpg FOREGROUND.png BACKDROP.jpg")
    print("CHAROITE_NEXT_FULLBLEED_BOOT=" + str(generate(*sys.argv[1:])))

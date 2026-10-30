#!/usr/bin/env python3
"""Generate a single seamless Charoite portrait composition from approved art.

v0.22 used a sharp square overlay on a procedurally painted sky and a
separately mirrored floor. Although the alpha mask was feathered, its straight
top/bottom transitions remained obvious on the Galaxy phone. v0.23 instead
resamples the SAME continuous source scene, taking more visual height from
its native star field and floor and protecting the gateway by stretching it
much less. There is no rectangular foreground layer or separate background.

This does not modify the approved source artwork or launcher icon.
"""
from pathlib import Path

from PIL import Image

PORTRAIT_SIZE = (960, 1840)
SOURCE_SIZE = (1536, 1536)

# The rounded square launcher frame lives outside this crop. Its interior
# contains the original sky, the full crystal gateway and the glass floor.
# Side crop deliberately reaches close to outer crystal edges, without
# reproducing the purple rounded-square icon border.
SOURCE_X = (114, 1422)
# Each contiguous source band is mapped to a portrait band: a little more sky
# and considerably more floor, with little change to the central gateway.
SOURCE_Y = (113, 360, 1160, 1434)
DEST_Y = (0, 385, 1230, 1840)


def generate(source, destination):
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise ValueError("Refuse to overwrite existing portrait art")
    with Image.open(source) as opened:
        if opened.size != SOURCE_SIZE or opened.format != "JPEG":
            raise ValueError("Unexpected approved Charoite artwork")
        master = opened.convert("RGB")

    width, height = PORTRAIT_SIZE
    # Scale horizontally only. Every output row is actual approved artwork,
    # never a fabricated flat-color sky or a mirrored copy of the icon.
    interior = master.crop((SOURCE_X[0], 0, SOURCE_X[1], SOURCE_SIZE[1]))
    interior = interior.resize((width, SOURCE_SIZE[1]), Image.Resampling.LANCZOS)
    portrait = Image.new("RGB", PORTRAIT_SIZE)
    for band in range(len(SOURCE_Y)-1):
        sy0, sy1 = SOURCE_Y[band], SOURCE_Y[band+1]
        dy0, dy1 = DEST_Y[band], DEST_Y[band+1]
        # Adjacent bands overlap by their exact shared source pixel. Using
        # 2px of crossfade at the join removes even a one-row resample seam
        # without leaving a large visible rectangular matte.
        top = max(0, sy0-1) if band else sy0
        bottom = min(SOURCE_SIZE[1], sy1+2)
        block = interior.crop((0, top, width, bottom))
        dest_h = dy1-dy0
        block = block.resize((width, dest_h+2), Image.Resampling.LANCZOS)
        block = block.crop((0, 1, width, dest_h+1))
        portrait.paste(block, (0, dy0))

    # Extremely narrow blending only at the two internal row-mapping anchors:
    # both inputs come from neighboring rows of the *same source image*.
    for seam in DEST_Y[1:-1]:
        upper = portrait.crop((0, seam-3, width, seam))
        lower = portrait.crop((0, seam, width, seam+3))
        upper_edge = upper.crop((0, 2, width, 3))
        lower_edge = lower.crop((0, 0, width, 1))
        for k in range(3):
            blend = Image.blend(upper_edge, lower_edge, (k+1)/7)
            portrait.paste(blend, (0, seam-3+k))
        for k in range(3):
            blend = Image.blend(upper_edge, lower_edge, (k+4)/7)
            portrait.paste(blend, (0, seam+k))

    destination.parent.mkdir(parents=True, exist_ok=True)
    portrait.save(destination, "JPEG", quality=95, subsampling=0, optimize=True)
    return destination


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("Usage: make_portrait_boot.py APPROVED.jpg OUTPUT.jpg")
    print("CHAROITE_NEXT_SEAMLESS_PORTRAIT=" + str(generate(*sys.argv[1:])))

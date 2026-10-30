#!/usr/bin/env python3
"""Build a true portrait Charoite Next splash, keeping the approved launcher untouched.

The 1536x1536 approved square contains its own rounded icon framing. Simply
CENTER_CROPPING or applying a matrix exposes those hard boundaries. This
deterministic compositor builds a 960x1840 scene: the unaltered central
crystalline gateway, surrounding original stars and floor reflections, plus
procedural cosmic sky/floor extension outside the square. No second square
overlay, blur-card, text baked into the art, or new external asset is required.
"""
from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageOps

PORTRAIT_SIZE = (960, 1840)
SOURCE_SIZE = (1536, 1536)
SEED = 0xC4A2017


def generate(source, destination):
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise ValueError("Refuse to overwrite existing portrait art")
    with Image.open(source) as opened:
        if opened.size != SOURCE_SIZE:
            raise ValueError("Unexpected approved Charoite art dimensions")
        master = opened.convert("RGB")

    width, height = PORTRAIT_SIZE
    rng = random.Random(SEED)

    # Remove the square-icon perimeter while retaining the central crystal tip
    # and portal. Fit to width, NOT screen height, so the gateway is truly
    # smaller and more of the original sides remain visible.
    inner = master.crop((65, 72, 1471, 1464))
    source_width = 1020
    source_height = round(inner.height * source_width / inner.width)
    inner = inner.resize((source_width, source_height), Image.Resampling.LANCZOS)
    core = inner.crop(((source_width-width)//2, 0,
                       (source_width-width)//2+width, source_height))
    core_top = 398
    core_bottom = core_top + core.height

    # Build the sky/floor as ONE portrait canvas. Subtle nebulae and a
    # deterministic star field avoid the former repeated, blurred icon image.
    canvas = Image.new("RGB", PORTRAIT_SIZE)
    pixels = canvas.load()
    for y in range(height):
        f = y / (height - 1)
        if y < core_top:
            # Dark indigo above the gateway; no curved square-icon border.
            c = (15 + int(17*f), 9 + int(9*f), 45 + int(31*f))
        elif y < core_bottom:
            c = (24, 13, 62)
        else:
            fade = (y-core_bottom) / max(1,height-core_bottom)
            c = (30-int(10*fade), 15-int(8*fade), 72-int(27*fade))
        for x in range(width):
            wave = 4 * math.sin(x*.006 + y*.004) * math.sin(y*.008 + 2.4)
            pixels[x,y] = tuple(max(0,min(255,int(v + wave))) for v in c)

    haze = Image.new("RGBA", PORTRAIT_SIZE, (0,0,0,0))
    hd = ImageDraw.Draw(haze)
    for j in range(38):
        x = rng.randint(-100,width+100)
        y = rng.choice([rng.randint(-100,core_top+90),
                        rng.randint(core_bottom-80,height+100)])
        r = rng.randint(65,260)
        hd.ellipse((x-r,y-r//2,x+r,y+r//2),
                   fill=rng.choice([(105,43,212,17),(54,66,204,15),
                                    (146,53,196,12),(52,97,206,10)]))
    haze = haze.filter(ImageFilter.GaussianBlur(62))
    canvas = Image.alpha_composite(canvas.convert("RGBA"),haze)

    starfield = Image.new("RGBA", PORTRAIT_SIZE, (0,0,0,0))
    stars = ImageDraw.Draw(starfield)
    for _ in range(610):
        x,y=rng.randrange(width),rng.randrange(height)
        # The detailed center comes from the approved master, not fake stars.
        if core_top+75 < y < core_bottom-75:
            continue
        radius=rng.choices([0,1,2],[45,52,3])[0]
        alpha=rng.randint(48,180)
        stars.ellipse((x-radius,y-radius,x+radius,y+radius),
                      fill=(210,201,255,alpha))
    canvas=Image.alpha_composite(canvas,starfield)

    # Continue the original luminous floor into the lower extension. Mirror
    # glass light, darken gradually, then feather at the join.
    lower_h = height-core_bottom
    if lower_h>0:
        floor = core.crop((0,max(0,core.height-285),width,core.height))
        floor = ImageOps.flip(floor).resize((width,lower_h),
                         Image.Resampling.BICUBIC)
        reflection = Image.new("L",(width,lower_h))
        mp=reflection.load()
        for y in range(lower_h):
            opacity=int(145*(1-y/max(1,lower_h))**1.2)
            for x in range(width): mp[x,y]=opacity
        canvas.alpha_composite(Image.merge("RGBA",(*floor.split(),reflection)),
                               (0,core_bottom))

    # Feather away the *square source perimeter*; this is the essential
    # difference from a cropped icon. The portal center stays sharp at 1:1
    # art quality; there is no rectangle sitting over blurred purple.
    mask=Image.new("L",core.size,255)
    m=mask.load()
    feather_top=130
    feather_bottom=155
    for y in range(core.height):
        a=min(255,round(255*y/feather_top),
              round(255*(core.height-1-y)/feather_bottom))
        for x in range(width):
            # Only 16px at the sides: keep both side crystals visible while
            # removing any residual hard icon-frame strip.
            edge=min(x,width-1-x)
            m[x,y]=max(0,min(a,round(255*edge/16)))
    canvas.alpha_composite(Image.merge("RGBA",(*core.split(),mask)),(0,core_top))

    destination.parent.mkdir(parents=True,exist_ok=True)
    canvas.convert("RGB").save(destination,"JPEG",quality=94,
                               subsampling=0,optimize=True)
    return destination


if __name__=="__main__":
    import sys
    if len(sys.argv)!=3:
        raise SystemExit("Usage: make_portrait_boot.py APPROVED.jpg OUTPUT.jpg")
    print("CHAROITE_NEXT_PORTRAIT_ART="+str(generate(*sys.argv[1:])))

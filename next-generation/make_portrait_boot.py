#!/usr/bin/env python3
"""Create the Next portrait boot without distorting the approved crystal portal.

The v0.23 screenshot exposed a tall, narrow gateway because source height was
stretched 1.4-3x more than source width. Keep the actual approved illustration
at ONE uniform scale instead. Extend only the *exterior*, with softly blended
starfield above and perspective glass-floor reflections below; both boundaries
derive directly from adjacent pixels of the original artwork. There is no
second square icon layer, hard rectangular seam, nor content-area squeeze.

The exact approved 1536px image and launcher icon are never overwritten.
"""
from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps

PORTRAIT_SIZE = (960, 1840)
SOURCE_SIZE = (1536, 1536)
SOURCE_X = (114, 1422)
SOURCE_Y = (113, 1434)
TOP_EXTENSION = 410
STAR_SEED = 0xCA4012E


def _repair_corner_frame(interior):
    """Only heal residual connected black corners from the rounded app icon."""
    width, height = interior.size
    pixels = interior.load()
    for y in range(height):
        if 165 < y < height-155:
            continue
        left = 0
        while left < width//3 and max(pixels[left, y]) < 32:
            left += 1
        right = width-1
        while right > 2*width//3 and max(pixels[right, y]) < 32:
            right -= 1
        for x in range(left):
            pixels[x, y] = pixels[min(width-1, 2*left-x), y]
        for x in range(right+1, width):
            pixels[x, y] = pixels[max(0, 2*right-x), y]
    return interior


def _sky_extension(core, height):
    """Reflect the actual adjoining sky, and progressively diffuse into space.

    Mirroring the first source row at the join gives an exact color-continuous
    boundary. Distant repetition is softened, so the top crystal isn't copied
    as a second visible portal. Small stars restore atmospheric detail there.
    """
    width = core.width
    sample = core.crop((0,0,width, min(125,core.height)))
    extension = ImageOps.flip(sample).resize((width,height),Image.Resampling.BICUBIC)
    blurred = extension.filter(ImageFilter.GaussianBlur(52))
    # Cosmic atmosphere color derived from the top edge, not a second scaled
    # copy of the square image. Blend is zero *at* the artwork boundary.
    atmosphere = Image.new("RGB",(width,height))
    gradient = atmosphere.load()
    for y in range(height):
        depth = (height-1-y)/max(1,height-1)
        for x in range(width):
            c = (15+int(17*depth), 9+int(8*depth), 53+int(27*depth))
            gradient[x,y] = c
    fade = Image.new("L",(width,height))
    mask = ImageDraw.Draw(fade)
    for y in range(height):
        d = (height-1-y)/max(1,height-1)
        # Adjacent pixels are unmodified; far sky becomes more painterly.
        alpha = int(242*min(1, d**1.15))
        mask.line((0,y,width,y),fill=alpha)
    extension.paste(Image.blend(blurred,atmosphere,.55),(0,0),fade)
    # Add cosmic pinpoints away from the transition; reproducible build.
    sky = extension.convert("RGBA")
    points = Image.new("RGBA",(width,height),(0,0,0,0))
    draw = ImageDraw.Draw(points)
    rng = random.Random(STAR_SEED)
    for _ in range(630):
        x,y = rng.randrange(width),rng.randrange(max(1,height-70))
        size = rng.choices([0,1,2], [50,44,6])[0]
        a = rng.randint(45,195)
        draw.ellipse((x-size,y-size,x+size,y+size),
                     fill=(208,190,255,a))
    sky = Image.alpha_composite(sky,points)
    return sky.convert("RGB")


def _glass_extension(core,height):
    """Extend the lower scene using neighboring reflective glass pixels.

    Only the floor, never the crystal gateway, is reprojected. A mirrored
    *edge strip* makes the transition color-continuous rather than introducing
    a pasted rectangular photograph. Its reflections fade naturally into
    violet black, as a large polished floor recedes toward the viewer.
    """
    width=core.width
    sample=core.crop((0,max(0,core.height-165),width,core.height))
    floor=ImageOps.flip(sample).resize((width,height),Image.Resampling.BICUBIC)
    softer=floor.filter(ImageFilter.GaussianBlur(24))
    shadow=Image.new("RGB",(width,height),(17,9,46))
    # Never change the border row. Gradually dim/diffuse *only* farther down.
    mix=Image.new("L",(width,height))
    d=ImageDraw.Draw(mix)
    for y in range(height):
        depth=y/max(1,height-1)
        d.line((0,y,width,y),fill=int(155*depth**1.15))
    floor.paste(Image.blend(softer,shadow,.45),(0,0),mix)

    # Dim luminous facets while keeping glass reflections visible.
    floor=ImageEnhance.Contrast(floor).enhance(1.04)
    return floor


def generate(source, destination):
    source,destination=Path(source),Path(destination)
    if destination.exists():
        raise ValueError("Refuse to overwrite existing portrait art")
    with Image.open(source) as original:
        if original.size!=SOURCE_SIZE or original.format!="JPEG":
            raise ValueError("Unexpected approved source art")
        art=original.convert("RGB")

    width,height=PORTRAIT_SIZE
    # This is the *only* resizing of the portal illustration. Apply the SAME
    # factor to X and Y, preventing the v0.23 stretched-portal defect.
    src_width=SOURCE_X[1]-SOURCE_X[0]
    src_height=SOURCE_Y[1]-SOURCE_Y[0]
    uniform_scale=width/src_width
    core_height=round(src_height*uniform_scale)
    assert TOP_EXTENSION+core_height<height
    core=art.crop((SOURCE_X[0],SOURCE_Y[0],SOURCE_X[1],SOURCE_Y[1]))
    core=core.resize((width,core_height),Image.Resampling.LANCZOS)
    core=_repair_corner_frame(core)

    bottom_height=height-TOP_EXTENSION-core_height
    picture=Image.new("RGB",PORTRAIT_SIZE)
    picture.paste(_sky_extension(core,TOP_EXTENSION),(0,0))
    picture.paste(core,(0,TOP_EXTENSION))
    picture.paste(_glass_extension(core,bottom_height),
                  (0,TOP_EXTENSION+core_height))

    # No rectangular matte, blurred square background or alternate image.
    # The extensions reflect adjoining edge pixels and meet with no color
    # discontinuity; only the new sky/floor take extra vertical screen space.
    destination.parent.mkdir(parents=True,exist_ok=True)
    picture.save(destination,"JPEG",quality=95,subsampling=0,optimize=True)
    return destination


if __name__=="__main__":
    import sys
    if len(sys.argv)!=3:
        raise SystemExit("Usage: make_portrait_boot.py APPROVED.jpg OUTPUT.jpg")
    print("CHAROITE_NEXT_UNDISTORTED_PORTRAIT="+str(generate(*sys.argv[1:])))

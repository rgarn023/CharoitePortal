#!/usr/bin/env python3
"""Five-second Charoite v0.24 motion CONCEPT preview; never changes app assets.

This produces an MP4 preview directly in GitHub Actions so it can be
downloaded through GitHub rather than ChatGPT's unreliable sandbox links.
The source is the exact approved boot master and its deterministic portrait
compositor. No change to the released/installed Charoite Android app.
"""
from pathlib import Path
import math
import subprocess
import tempfile

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Charoite_Crystal_Awakening_Preview.mp4"
WIDTH, HEIGHT, FPS, SECONDS = 480, 920, 20, 5


def draw_plaque(canvas):
    """Match the native dark-amethyst boot wordmark at preview scale."""
    width, height = canvas.size
    d = ImageDraw.Draw(canvas, "RGBA")
    cy = int(height * .85)
    x0, x1 = int(width * .08), int(width * .92)
    y0, y1 = cy - 40, cy + 31
    d.rounded_rectangle((x0-2,y0-2,x1+2,y1+2),radius=16,
                        fill=(12,5,40,242),outline=(205,159,255,255),width=3)
    d.rounded_rectangle((x0+3,y0+3,x1-3,y1-3),radius=11,
                        outline=(240,221,255,200),width=1)
    fontpath = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    font = ImageFont.truetype(fontpath, 31)
    label = "CHAROITE PORTAL"
    while d.textbbox((0, 0), label, font=font, stroke_width=2)[2] > width*.79:
        font = ImageFont.truetype(fontpath, font.size-1)
    d.text((width/2, cy-5), label, font=font, anchor="mm",
           fill=(236,205,255,255),stroke_width=2,stroke_fill=(42,12,94,255))


def make_base():
    import importlib.util
    p = ROOT / "next-generation" / "make_portrait_boot.py"
    spec = importlib.util.spec_from_file_location("approved_portrait", p)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    source = ROOT / "next-generation" / "assets" / "charoite_next_boot_reference.jpg"
    with tempfile.TemporaryDirectory() as tmp:
        portrait = Path(tmp) / "portrait.jpg"
        generator.generate(source, portrait)
        art = Image.open(portrait).convert("RGBA")
        art = art.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        draw_plaque(art)
        return np.asarray(art.convert("RGB"), dtype=np.float32)


def ellipse(x, y, cx, cy, rx, ry):
    return np.exp(-.5 * (((x-cx)/rx)**2 + ((y-cy)/ry)**2))


def smooth(a, b, x):
    v = np.clip((x-a)/(b-a),0,1)
    return v*v*(3-2*v)


def main():
    base = make_base()
    yy, xx = np.mgrid[0:HEIGHT,0:WIDTH].astype("float32")
    xn, yn = xx/WIDTH, yy/HEIGHT
    lum = base[:,:,0]*.29+base[:,:,1]*.58+base[:,:,2]*.13
    highlight = np.clip((base.max(axis=2)-110)/115,0,1)**1.4
    purple = np.clip((base[:,:,2]-base[:,:,1]+30)/110,0,1)
    painted = highlight*(.35+.65*purple)
    portal_area = ellipse(xn,yn,.49,.45,.17,.115)
    portal_area *= smooth(.31,.39,yn)*(1-smooth(.55,.62,yn))
    portal_area = cv2.GaussianBlur(portal_area.astype("float32"),(0,0),5)
    rx,ry=.27,.19
    u,v=(xn-.49)/rx,(yn-.45)/ry
    ang=np.arctan2(v,u)
    rim = np.exp(-.5*((np.sqrt(u*u+v*v)-1)/.17)**2)*painted
    rim *= smooth(.25,.34,yn)*(1-smooth(.6,.67,yn))
    crystals = (ellipse(xn,yn,.47,.22,.15,.12)
                +ellipse(xn,yn,.21,.39,.09,.13)
                +ellipse(xn,yn,.76,.39,.09,.12)) * painted
    floor = smooth(.59,.70,yn)*(1-smooth(.94,1.,yn))*painted
    title = (smooth(.803,.821,yn)*(1-smooth(.866,.885,yn))
             *smooth(.11,.2,xn)*(1-smooth(.8,.9,xn))
             *np.clip((lum-110)/110,0,1)**1.5)

    command = [imageio_ffmpeg.get_ffmpeg_exe(),"-y","-loglevel","error","-f","rawvideo",
               "-pixel_format","rgb24","-video_size",f"{WIDTH}x{HEIGHT}",
               "-framerate",str(FPS),"-i","-","-an","-c:v","libx264",
               "-preset","fast","-crf","21","-pix_fmt","yuv420p",
               "-movflags","+faststart",str(OUT)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    for i in range(FPS*SECONDS):
        t=i/FPS
        dx=portal_area*(1.5*np.sin(yn*45-t*2.5)+.6*np.sin(xn*30+t))
        floor_dx=floor*(.5*np.sin(yn*70-t*2))
        frame=cv2.remap(base,(xx-dx-floor_dx).astype("float32"), yy,
                        cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
        phase=t*.85-1.4
        arc=np.arctan2(np.sin(ang-phase),np.cos(ang-phase))
        sweep=np.exp(-.5*(arc/.55)**2)
        moving_rim=rim*(5+22*sweep)
        breathing=portal_area*painted*(3+9*(.5+.5*math.sin(t*1.6)))
        facet_x=.15+.75*np.clip((t-.5)/2.5,0,1)
        facet=crystals*(3+18*np.exp(-.5*((xn-facet_x)/.085)**2))
        reflection=floor*(3+8*np.clip(np.sin(yn*55-t*2),0,1))
        light=moving_rim+breathing+facet+reflection
        frame+=light[:,:,None]*np.array([.75,.76,1.0],dtype="float32")
        if 3.15<t<4.55:
            pt=(t-3.15)/1.4
            glint=np.exp(-.5*((xn-(.12+.76*pt))/.05)**2)
            frame+=(title*glint*37*math.sin(math.pi*pt))[:,:,None]
        proc.stdin.write(np.uint8(np.clip(frame,0,255)).tobytes())
    proc.stdin.close()
    if proc.wait()!=0:
        raise RuntimeError("ffmpeg preview render failed")
    print(f"CHAROITE_CONCEPT_MP4={OUT.name} bytes={OUT.stat().st_size}")


if __name__=="__main__":
    main()

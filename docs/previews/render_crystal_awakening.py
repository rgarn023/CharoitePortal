#!/usr/bin/env python3
"""Seven-second C-crystal glow and inner black-purple portal; preserves approved art.

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
OUT = ROOT / "Charoite_Crystal_Portal_7s.mp4"
WIDTH, HEIGHT, FPS, SECONDS = 480, 920, 24, 7


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



# Hand-traced outlines of the approved C-crystal. Its material stays still;
# light is added only along the facets, with the portal within the inner void.
OUTER = np.array([
    (699,614),(681,578),(618,522),(538,505),(452,514),(371,533),
    (295,591),(234,677),(211,761),(226,867),(276,960),(359,1020),
    (455,1061),(572,1053)], dtype=np.float32)
INNER = np.array([
    (681,688),(648,640),(597,602),(537,577),(468,573),(399,606),
    (342,659),(304,737),(301,823),(323,907),(374,976),(450,1012),
    (527,1020),(610,995)], dtype=np.float32)


def resample_curve(points, count=1050):
    chunks = []
    for i in range(len(points)-1):
        a,b,c,d=points[max(0,i-1)],points[i],points[i+1],points[min(len(points)-1,i+2)]
        t=np.linspace(0,1,18,endpoint=False,dtype=np.float32)[:,None]
        chunks.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+
                           (-a+3*b-3*c+d)*t*t*t))
    raw=np.vstack(chunks+[points[-1:]])
    dist=np.r_[0,np.cumsum(np.linalg.norm(np.diff(raw,axis=0),axis=1))]
    u=np.linspace(0,dist[-1],count)
    curve=np.stack([np.interp(u,dist,raw[:,0]),
                    np.interp(u,dist,raw[:,1])],axis=1)
    tangent=np.gradient(curve,axis=0)
    tangent/=np.maximum(1e-5,np.linalg.norm(tangent,axis=1,keepdims=True))
    normal=np.stack([-tangent[:,1],tangent[:,0]],axis=1)
    scale=np.array([WIDTH/960,HEIGHT/1840],dtype=np.float32)
    return curve*scale,normal



def smoothstep(a, b, x):
    x=np.clip((x-a)/(b-a),0,1)
    return x*x*(3-2*x)


def make_energy_sources(paths):
    """Precompute a localized facet glow; never paint drifting clouds."""
    thin = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    for curve, _ in paths:
        pts = np.rint(curve).astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(thin, [pts], False, 255, 9, cv2.LINE_AA)
    narrow = cv2.GaussianBlur(thin, (0, 0), 7).astype(np.float32) / 255
    wide = cv2.GaussianBlur(thin, (0, 0), 22).astype(np.float32) / 255
    return narrow, wide


def portal_phase(t):
    # The source soundtrack is fully silent at t=6.35. Complete the portal
    # fade by 6.25 so it never pops away when Android closes the boot at 7s.
    appear = smoothstep(1.15, 2.65, t)
    disappear = 1.0 - smoothstep(5.05, 6.25, t)
    return float(appear * disappear)


def crystal_phase(t):
    return float(smoothstep(.08, 1.40, t) *
                 (1.0 - smoothstep(5.12, 6.30, t)))


def render_overlay(t, base, xx, yy, paths, sources):
    """C glow and softly shaded inner vortex; NO clouds, lightning or zoom.

    The portal is a carefully feathered ellipse within the negative space of
    the original C. It never obscures the title, sky or outer crystal tips.
    At the first and final frames this returns the untouched approved image.
    """
    narrow, wide = sources
    glow_amount = crystal_phase(t)
    portal_amount = portal_phase(t)
    if glow_amount == 0.0 and portal_amount == 0.0:
        return base

    # Gentle, breathing violet-lavender light on the two crystal contours.
    breathing = 0.94 + 0.06 * math.sin(2.0 * math.pi * .28 * t)
    bright = glow_amount * breathing * (.72 * narrow + .38 * wide)
    scene = base + bright[:, :, None] * np.array([105., 49., 150.], np.float32)

    if portal_amount > 0:
        # Coordinates in original 960x1840 artwork: C void near (496, 780).
        # Confining the radius keeps the portal inside the opening, not over
        # the facets, its right-hand tips, title plaque or exterior scenery.
        u = (xx - 248.) / 74.
        v = (yy - 391.) / 88.
        radius = np.sqrt(u*u + v*v)
        angle = np.arctan2(v, u)

        # Soft black-amethyst center blended WITH the existing picture. No
        # opaque flat black disk and no sharp edge that could suddenly vanish.
        inside = 1.0 - smoothstep(.77, 1.025, radius)
        darkness = portal_amount * inside * .83
        scene = scene * (1.0 - darkness[:, :, None])

        # Two subtly rotating folds, distant violet light inside the vortex.
        swirl = 0.5 + 0.5 * np.cos(14.0*radius + 2.2*angle - 1.0*t)
        inner = np.exp(-1.8*radius*radius) * inside
        folds = portal_amount * inner * (.12 + .15 * swirl)
        scene += folds[:, :, None] * np.array([57., 20., 128.], np.float32)

        # Luminous inner lip and restrained halo, with extremely slow pulse.
        # These are smooth ellipses, NEVER jagged lightning/electric branches.
        lip = np.exp(-.5*((radius - .91)/.065)**2)
        halo = np.exp(-.5*((radius - 1.04)/.17)**2)
        pulse = 0.94 + .06 * math.sin(2.0*math.pi*.36*t)
        edge = portal_amount * pulse * (.41*lip + .22*halo)
        scene += edge[:, :, None] * np.array([97., 35., 171.], np.float32)

    return scene


def main():
    base=make_base()
    yy,xx=np.mgrid[0:HEIGHT,0:WIDTH].astype(np.float32)
    paths=[resample_curve(OUTER),resample_curve(INNER)]
    sources=make_energy_sources(paths)
    command=[imageio_ffmpeg.get_ffmpeg_exe(),"-y","-loglevel","error",
             "-f","rawvideo","-pixel_format","rgb24",
             "-video_size",f"{WIDTH}x{HEIGHT}","-framerate",str(FPS),
             "-i","-","-an","-c:v","libx264","-preset","fast",
             "-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(OUT)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    frames=(0,1,2.5,4.5,5.8,6.9)
    stills=[]
    for n in range(FPS*SECONDS):
        t=n/FPS
        frame=np.uint8(np.clip(render_overlay(t,base,xx,yy,paths,sources),0,255))
        proc.stdin.write(frame.tobytes())
        if any(abs(t-s)<=.02 for s in frames):
            stills.append(Image.fromarray(frame,"RGB").resize(
                (240,460),Image.Resampling.LANCZOS))
    proc.stdin.close()
    if proc.wait()!=0:
        raise RuntimeError("ffmpeg encoding failed")
    capture=cv2.VideoCapture(str(OUT))
    framecount=capture.get(cv2.CAP_PROP_FRAME_COUNT)
    capture.release()
    assert abs(framecount-FPS*SECONDS)<1

    # Optional visual contact sheet for preview review on Github.
    if len(stills)>=4:
        sheet=Image.new("RGB",(240*len(stills),460),(9,8,27))
        for j,still in enumerate(stills):
            sheet.paste(still,(j*240,0))
        sheet.save(ROOT/"Charoite_Crystal_Portal_7s_Storyboard.jpg",
                   quality=90)
    print(f"CHAROITE_CRYSTAL_PORTAL_7_SECONDS=PASS {OUT.name} {OUT.stat().st_size} bytes")


if __name__=="__main__":
    main()

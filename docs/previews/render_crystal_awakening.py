#!/usr/bin/env python3
"""Seven-second crystal C glowing with inward counterclockwise purple-black smoke vortex.

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
OUT = ROOT / "Charoite_Crystal_Smoke_Vortex_7s.mp4"
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
    x = np.clip((x-a)/(b-a), 0, 1)
    return x*x*(3-2*x)


def crystal_phase(t):
    return float(smoothstep(.08, 1.35, t) * (1-smoothstep(5.1, 6.3, t)))


def portal_phase(t):
    # Seven-second soundtrack fades to full digital silence by 6.35s.
    return float(smoothstep(.75, 2.25, t) * (1-smoothstep(5.0, 6.25, t)))


def advect_cloud(source, age, seed=0.):
    """Smoke starts at an actual inner-C edge and spirals inward CCW.

    The Y axis is inverted when calculating theta: increasing theta really
    does move counterclockwise on the phone display.
    """
    cx, cy = 248., 391.
    dx = (source[0]-cx)/86.
    dy = -(source[1]-cy)/104.
    radius0 = max(.12, math.hypot(dx, dy))
    theta0 = math.atan2(dy, dx)
    radius = radius0 * math.exp(-.58*age)
    theta = theta0 + 1.72*age + .16*age*age + .09*math.sin(2.3*age+seed)
    return (cx+86*radius*math.cos(theta),
            cy-104*radius*math.sin(theta))


def make_energy_sources(paths):
    """Crystal-facet/edge bloom; precompute from real traced C geometry."""
    thin = np.zeros((HEIGHT, WIDTH), np.uint8)
    facet = np.zeros((HEIGHT, WIDTH), np.uint8)
    for curve, _ in paths:
        cv2.polylines(thin, [np.rint(curve).astype(np.int32)],
                      False, 255, 13, cv2.LINE_AA)
    band = np.vstack([paths[0][0], paths[1][0][::-1]])
    cv2.fillPoly(facet, [np.rint(band).astype(np.int32)], 255)
    return (cv2.GaussianBlur(thin, (0, 0), 3).astype(np.float32)/255,
            cv2.GaussianBlur(thin, (0, 0), 14).astype(np.float32)/255,
            cv2.GaussianBlur(thin, (0, 0), 32).astype(np.float32)/255,
            cv2.GaussianBlur(facet, (0, 0), 6).astype(np.float32)/255)


def render_overlay(t, base, xx, yy, paths, sources):
    """Purple/black smoke streamed FROM the C rim, pulled INWARD counterclockwise.

    No disk, circular portal lip or global darkening of a geometric ellipse.
    Smoke itself is made of irregular moving billows; no background remap.
    """
    glow_amount = crystal_phase(t)
    portal_amount = portal_phase(t)
    if glow_amount == 0 and portal_amount == 0:
        return base
    thin, mid, wide, facet = sources
    scene = base.copy()
    if glow_amount:
        pulse = .90 + .10*math.sin(t*1.8)**2
        # The C crystal itself lights up: broad violet bloom, brighter facets
        # and white-lilac edge highlights, not a faint outline-only change.
        light = glow_amount*pulse*(1.1*thin + 1.30*mid + 1.5*wide)
        scene += np.clip(light, 0, 1.4)[:,:,None] * np.array(
            [80., 43., 118.], np.float32)
        scene += glow_amount*facet[:,:,None]*np.array(
            [24., 12., 34.], np.float32)
        highlight = np.clip(thin*glow_amount*.38, 0, .42)
        scene = (scene*(1-highlight[:,:,None]) +
                 np.array([251., 207., 255.], np.float32)*highlight[:,:,None])

    if portal_amount:
        dark = np.zeros((HEIGHT, WIDTH), np.uint8)
        purple = np.zeros((HEIGHT, WIDTH), np.uint8)
        inner_curve = paths[1][0]
        # Emit short smoke trails continuously from widely spaced inner C
        # facets. Each wisp follows a tightening CCW spiral as it is pulled
        # toward the center. No circular painted fill is ever drawn.
        for i in range(50):
            launch = .70 + .098*i
            age = t - launch
            if age <= 0 or age >= 2.65:
                continue
            source = inner_curve[int(((i*.61803398875) % 1) *
                                     (len(inner_curve)-1))]
            seed = i*.83
            birth = float(smoothstep(0, .30, age))
            death = float(1-smoothstep(2.15, 2.65, age))
            weight = birth*death
            for j in range(10):
                a = max(0., age-j*.075)
                x, y = advect_cloud(source, a, seed)
                x += 2.7*math.sin(i*2.57+j*1.31+a*4)
                y += 2.9*math.cos(i*1.71+j*.91+a*3.2)
                opacity = weight*(1-j/12)
                size = (9+4*math.sin(i*1.73+j*.91)**2)*(.6+.38*a)
                cv2.circle(dark, (int(x), int(y)), int(size),
                           int(185*opacity), -1, cv2.LINE_AA)
                cv2.circle(purple, (int(x+2), int(y-1)),
                           max(2, int(size*.55)), int(112*opacity),
                           -1, cv2.LINE_AA)

        dark = cv2.GaussianBlur(dark, (0, 0), 6).astype(np.float32)/255
        purple = cv2.GaussianBlur(purple, (0, 0), 4).astype(np.float32)/255
        turbulence = (np.sin(xx*.068+yy*.037+2.3*t) *
                      np.sin(yy*.085-xx*.045-2.9*t))
        dark = np.clip(dark*(.84+.30*turbulence)*2.55, 0, .9)
        purple = np.clip(purple*(.84+.24*turbulence)*2.35, 0, .9)
        # Wisps are physically dark black smoke laced with luminous purple.
        # Keep the moving smoke from hiding the luminous crystal facets.
        allow = 1-np.clip(facet*.75, 0, .75)
        scene *= (1-portal_amount*dark*allow)[:,:,None]
        scene += (portal_amount*purple*allow)[:,:,None] * np.array(
            [119., 24., 221.], np.float32)
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
        sheet.save(ROOT/"Charoite_Crystal_Smoke_Vortex_7s_Storyboard.jpg",
                   quality=90)
    print(f"CHAROITE_CRYSTAL_SMOKE_VORTEX_7_SECONDS=PASS {OUT.name} {OUT.stat().st_size} bytes")


if __name__=="__main__":
    main()

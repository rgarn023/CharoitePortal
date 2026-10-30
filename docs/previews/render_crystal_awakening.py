#!/usr/bin/env python3
"""Ten-second Charoite v0.24 CLOUD-ONLY CONCEPT preview; never changes app assets.

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
OUT = ROOT / "Charoite_Mystic_C_Cloud_Only_10s.mp4"
WIDTH, HEIGHT, FPS, SECONDS = 480, 920, 24, 10


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



# Curve points follow the approved `C` crystal silhouette. Only
# additive light is painted; the actual artwork never shifts or warps.
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


def cloud_noise(seed, low_shape):
    """Soft multi-octave, reproducible volumetric noise, not image distortion."""
    rng=np.random.default_rng(seed)
    small=rng.random(low_shape,dtype=np.float32)
    return cv2.GaussianBlur(cv2.resize(small,(WIDTH,HEIGHT),
                        interpolation=cv2.INTER_CUBIC),(0,0),7)


def make_cloud_sources(paths):
    """Cloud envelopes hug the C silhouette, not the entire screen."""
    fine=np.zeros((HEIGHT,WIDTH),dtype=np.uint8)
    broad=np.zeros_like(fine)
    for path,_ in paths:
        pts=np.rint(path).astype(np.int32).reshape(-1,1,2)
        cv2.polylines(fine,[pts],False,255,43,cv2.LINE_AA)
        cv2.polylines(broad,[pts],False,255,104,cv2.LINE_AA)
    fine=cv2.GaussianBlur(fine,(0,0),18).astype(np.float32)/255
    broad=cv2.GaussianBlur(broad,(0,0),34).astype(np.float32)/255
    # Keep the energy entirely near the outer crystal C and inner crescent,
    # out of the title, stars, planets and open portal center.
    return fine,broad,cloud_noise(814,(24,13)),cloud_noise(191,(53,31))



def overlay(t, xx, yy, paths, sources):
    fine,broad,noise_a,noise_b=sources
    ramp=smoothstep(.15,2.1,t)
    # A bright but gentle crescendo at the end; no full-screen flash.
    finale=1+.22*math.exp(-.5*((t-9.25)/.34)**2)
    tail=1-.88*smoothstep(9.72,10.0,t)
    envelope=ramp*finale*tail

    # Animate the CLOUD textures, never the original illustration. The
    # two drifting noise fields make wispy violet fog curl around the C.
    dx=int(12*t+9*math.sin(t*.57))
    dy=int(-13*t+5*math.sin(t*.72))
    a=np.roll(noise_a,(dy,dx),(0,1))
    b=np.roll(noise_b,(-dy*2,dx//2),(0,1))
    cloud=np.clip((a*.78+b*.55-.31)*3.2,0,1)
    cloud=cv2.GaussianBlur(cloud.astype(np.float32),(0,0),3)
    density=(.38*broad + 1.3*fine)*cloud
    density=np.clip(density*envelope,0,.93)
    # Layer luminous lavender smoke over the C, retaining artwork details.
    color=np.array([164,64,246],dtype=np.float32)
    cloudy=(color[None,None,:]*density[:,:,None]*.78)
    cloudy+=density[:,:,None]*np.array([37,12,82],dtype=np.float32)

    # Three floating masses flow along the curved crystal. Broad
    # Gaussian plumes, no drawn tracer lines or screen-scale distortions.
    cloud_mass=np.zeros((HEIGHT,WIDTH),dtype=np.float32)
    for k,(path,norm) in enumerate((paths[0],paths[1],paths[0])):
        phase=(t*(.047+.013*k)+(.09,.55,.77)[k])%1
        center=int(phase*(len(path)-1))
        p=path[center]
        offset=(11 if k!=1 else -7)+7*math.sin(1.25*t+k*2)
        x,y=(p+norm[center]*offset)
        r2=((xx-x)/28)**2+((yy-y)/35)**2
        patch=np.exp(-.5*r2)*(.65+.35*math.sin(t*1.15+k*2)**2)
        cloud_mass+=patch*cloud
    cloudy+=np.clip(cloud_mass*envelope,0,1)[:,:,None]*np.array([44,17,98],dtype=np.float32)

    # Crystal edge glow responds gently to the drifting, magical cloud.
    illumination=(fine*.35+broad*.12)*envelope
    cloudy+=illumination[:,:,None]*np.array([29,12,56],dtype=np.float32)

    # No electrical discharges, bolts, filaments, flashes, or image warping.
    return cloudy


def main():
    base=make_base()
    yy,xx=np.mgrid[0:HEIGHT,0:WIDTH].astype(np.float32)
    paths=[resample_curve(OUTER),resample_curve(INNER)]
    sources=make_cloud_sources(paths)
    command=[imageio_ffmpeg.get_ffmpeg_exe(),"-y","-loglevel","error",
             "-f","rawvideo","-pixel_format","rgb24",
             "-video_size",f"{WIDTH}x{HEIGHT}","-framerate",str(FPS),
             "-i","-","-an","-c:v","libx264","-preset","fast",
             "-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(OUT)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    frames=(0,2.5,5,7.5,9.25)
    stills=[]
    for n in range(FPS*SECONDS):
        t=n/FPS
        frame=np.uint8(np.clip(base+overlay(t,xx,yy,paths,sources),0,255))
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
        sheet.save(ROOT/"Charoite_Mystic_C_Cloud_Only_10s_Storyboard.jpg",
                   quality=90)
    print(f"CHAROITE_MYSTIC_C_CLOUD_ONLY_10_SECONDS=PASS {OUT.name} {OUT.stat().st_size} bytes")


if __name__=="__main__":
    main()

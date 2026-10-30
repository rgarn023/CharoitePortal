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
OUT = ROOT / "Charoite_Mystic_C_Preview.mp4"
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


def overlay(t, xx, yy, paths):
    w,h=WIDTH,HEIGHT
    energy=np.zeros((h,w,3),dtype=np.float32)
    smoke=np.zeros((h,w),dtype=np.uint8)
    ignite=np.clip((t-.15)/.9,0,1)*np.clip((5.1-t)/.5,0,1)
    flows=[(paths[0],.04,1.04,.32,1.),(paths[1],.16,.71,.23,.82),
           (paths[0],.48,.77,.15,.52)]
    for k,((path,norm),offset,speed,length,power) in enumerate(flows):
        progress=(t*speed/5+offset)%1.
        u=np.linspace(progress-length,progress,140)
        u=u[(u>=0)&(u<=1)]
        if not len(u):
            continue
        ix=np.clip((u*(len(path)-1)).astype(int),0,len(path)-1)
        phase=np.linspace(0,1,len(ix))
        curl=np.sin(u*32+t*1.9+k*2.3)*(.6+3.2*phase)
        push=(-1 if k==1 else 1)*(11.5+7*np.sin(np.pi*phase)**2)
        pos=path[ix]+norm[ix]*(curl+push)[:,None]
        line=np.zeros((h,w),dtype=np.uint8)
        cv2.polylines(line,[np.rint(pos).astype(np.int32).reshape(-1,1,2)],
                      False,255,3 if k==0 else 2,cv2.LINE_AA)
        cv2.polylines(smoke,[np.rint(pos+norm[ix]*2.9).astype(np.int32).reshape(-1,1,2)],
                      False,255,7,cv2.LINE_AA)
        blur=cv2.GaussianBlur(line,(0,0),3.5)
        halo=cv2.GaussianBlur(line,(0,0),12)
        amount=ignite*power
        energy+=halo[:,:,None]*np.array([2.1,.80,3.4])*amount
        energy+=blur[:,:,None]*np.array([.95,.66,1.75])*amount
        energy+=line[:,:,None]*np.array([.25,.42,.55])*amount
        x,y=pos[-1]
        rr=(xx-x)**2+(yy-y)**2
        bloom=np.exp(-rr/(2*7**2))*ignite*power
        glint=np.exp(-rr/(2*1.55**2))*ignite*power
        energy+=bloom[:,:,None]*np.array([50,24,87])
        energy+=glint[:,:,None]*np.array([155,202,245])
    halo=cv2.GaussianBlur(smoke,(0,0),21)
    energy+=halo[:,:,None]*np.array([.95,.30,1.6])*ignite

    # Four crystal-tip glints; no random full-screen particle overlay.
    tips=[(.47,.278),(.71,.34),(.22,.39),(.48,.589)]
    for i,(nx,ny) in enumerate(tips):
        peak=max(0,math.sin(t*2.2-i*.93))**9
        r2=(xx-nx*w)**2+(yy-ny*h)**2
        fine=np.exp(-r2/(2*2.9**2))
        broad=np.exp(-r2/(2*13**2))
        energy+=(fine[:,:,None]*[33,46,62]+broad[:,:,None]*[8,5,16])*peak*.65*ignite
    return energy


def main():
    base=make_base()
    yy,xx=np.mgrid[0:HEIGHT,0:WIDTH].astype(np.float32)
    paths=[resample_curve(OUTER),resample_curve(INNER)]
    command=[imageio_ffmpeg.get_ffmpeg_exe(),"-y","-loglevel","error",
             "-f","rawvideo","-pixel_format","rgb24",
             "-video_size",f"{WIDTH}x{HEIGHT}","-framerate",str(FPS),
             "-i","-","-an","-c:v","libx264","-preset","fast",
             "-crf","19","-pix_fmt","yuv420p","-movflags","+faststart",str(OUT)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    for n in range(FPS*SECONDS):
        t=n/FPS
        # STATIC background: pixel coordinates unchanged for every frame.
        # All motion is additional spectral light following the C's curves.
        frame=np.uint8(np.clip(base+overlay(t,xx,yy,paths),0,255))
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    if proc.wait()!=0:
        raise RuntimeError("ffmpeg encoding failed")
    capture=cv2.VideoCapture(str(OUT))
    framecount=capture.get(cv2.CAP_PROP_FRAME_COUNT)
    capture.release()
    assert abs(framecount-FPS*SECONDS)<1
    print(f"CHAROITE_MYSTIC_C_PREVIEW=PASS {OUT.name} {OUT.stat().st_size} bytes")


if __name__=="__main__":
    main()

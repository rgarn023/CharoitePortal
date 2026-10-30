#!/usr/bin/env python3
"""Seven-second reference vortex fed by purple-black clouds from the existing C rim.

The original crystal C, full-screen scenery and Android-drawn wordmark are
unchanged. ONLY clouds in the C opening and its feathered vortex are animated. In
particular, never bake a second wordmark into the video: Android's
CrystalWordmark view is drawn ABOVE this silent video, at all times.
"""
from pathlib import Path
import importlib.util
import math
import subprocess
import tempfile

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Charoite_C_Edge_Fed_Portal_7s.mp4"
SOURCE = ROOT / "next-generation/assets/charoite_portal_reference_inner.jpg"
WIDTH, HEIGHT, FPS, SECONDS = 480, 920, 24, 7

# Placement is relative to the same 960x1840 portrait art used by
# CrystalArtwork; these are 480x920 coordinates in the C's open center.
PORTAL_X, PORTAL_Y = 292, 416
PORTAL_RX, PORTAL_RY = 78, 89


def make_base():
    """Exact same derived portrait art as the native boot ImageView."""
    spec = importlib.util.spec_from_file_location(
        "approved_portrait", ROOT / "next-generation/make_portrait_boot.py")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    master = ROOT / "next-generation/assets/charoite_next_boot_reference.jpg"
    with tempfile.TemporaryDirectory() as tmp:
        portrait = Path(tmp) / "portrait.jpg"
        generator.generate(master, portrait)
        with Image.open(portrait) as art:
            # Do NOT draw a title plaque here. Android draws the original
            # one ON TOP of the video, with no frame-to-frame replacement.
            return np.asarray(art.convert("RGB").resize(
                (WIDTH, HEIGHT), Image.Resampling.LANCZOS), dtype=np.float32)


def make_portal_source():
    """Real swirled violet/black cloud texture cropped from the user screenshot."""
    with Image.open(SOURCE) as image:
        image.load()
        assert image.size == (160, 160), "Unexpected reference crop geometry"
        return np.asarray(image.convert("RGB"), dtype=np.float32)


def smoothstep(a, b, x):
    x = np.clip((x-a)/(b-a), 0, 1)
    return x*x*(3-2*x)


def portal_phase(t):
    # Starts clean and reaches full invisibility by the sound's quiet tail.
    return float(smoothstep(.90, 2.55, t) *
                 (1. - smoothstep(4.85, 6.25, t)))


# Hand-traced INNER rim of the actual crystal C, in the 480x920 portrait.
# These are separate geometry references: the crystal artwork is NEVER drawn
# or modified by these paths, including at the emitter locations.
INNER_C_RIM = np.array([
    (340.,344.), (324.,320.), (299.,301.), (268.,289.),
    (234.,286.), (199.,303.), (171.,329.), (152.,368.),
    (150.,411.), (161.,454.), (187.,488.), (225.,506.),
    (263.,510.), (305.,497.)
], dtype=np.float32)

# This narrow ROI contains the inward-moving clouds plus the reference
# vortex. Everything beyond it, including the C's crystalline facets,
# the landscape and the native Android title, remains an exact base copy.
FEED_X0, FEED_Y0, FEED_X1, FEED_Y1 = 138, 280, 380, 521


def smoke_phase(t):
    """Clouds start first; begin dissipating exactly at the audio fade."""
    return float(smoothstep(.22, 1.20, t) *
                 (1. - smoothstep(4.85, 6.25, t)))


def rim_source(i):
    """Continuously-spaced points along the full curved inner edge of C."""
    segments = np.linalg.norm(np.diff(INNER_C_RIM, axis=0), axis=1)
    arc = np.r_[0., np.cumsum(segments)]
    u = (i * .61803398875) % 1.
    target = u * arc[-1]
    return (float(np.interp(target, arc, INNER_C_RIM[:, 0])),
            float(np.interp(target, arc, INNER_C_RIM[:, 1])))


def advect_cloud(source, age, seed=0.):
    """Move from the C's inner rim TOWARD the portal with CCW angular flow.

    The crystal point itself isn't painted: first move 5px into the opening.
    With screen-Y inverted, increasing theta is visually counterclockwise.
    The exponential radius decay makes each strand visibly spiral inward.
    """
    cx, cy = float(PORTAL_X), float(PORTAL_Y)
    dx, dy = cx-source[0], cy-source[1]
    length = max(1., math.hypot(dx,dy))
    x0 = source[0] + 5.*dx/length
    y0 = source[1] + 5.*dy/length
    xscale, yscale = 127., 130.
    theta0 = math.atan2(-(y0-cy)/yscale, (x0-cx)/xscale)
    radius0 = math.hypot((x0-cx)/xscale, (y0-cy)/yscale)
    radius = radius0*math.exp(-.68*age)
    theta = theta0 + 1.55*age + .16*age*age + .025*math.sin(2.*age+seed)
    return (cx+xscale*radius*math.cos(theta),
            cy-yscale*radius*math.sin(theta))


def opening_mask():
    """Soft inner-C aperture mask: never brighten/darken crystal material."""
    hh, ww = FEED_Y1-FEED_Y0, FEED_X1-FEED_X0
    stencil = np.zeros((hh,ww),np.uint8)
    # Trace the boundary immediately INWARD from the crystal's inner facets,
    # then close around the existing central portal's open right-hand region.
    points = np.array(
        [(349.,345.), (332.,330.), (302.,310.), (268.,299.),
         (237.,297.), (207.,314.), (180.,337.), (164.,370.),
         (161.,411.), (173.,451.), (198.,476.), (228.,495.),
         (263.,499.), (310.,486.), (369.,481.), (375.,351.)],
        dtype=np.float32)
    points[:,0] -= FEED_X0
    points[:,1] -= FEED_Y0
    cv2.fillPoly(stencil, [np.rint(points).astype(np.int32)], 255)
    return cv2.GaussianBlur(stencil, (0,0), 3).astype(np.float32)/255.


def make_clouds(t):
    """Many staggered smoke releases: purple highlights and dark billows.

    New smoke stops being emitted during the soundtrack's ending fade.
    Existing wisps continue winding inward while their alpha/contrast and
    coherence dissipate; there is no circular fade mask or abrupt cut.
    """
    hh, ww = FEED_Y1-FEED_Y0, FEED_X1-FEED_X0
    black = np.zeros((hh, ww), np.uint8)
    violet = np.zeros_like(black)
    for i in range(67):
        launch = .18 + i*.071
        age = t-launch
        if age <= 0 or age >= 2.8 or launch >= 4.85:
            continue
        source = rim_source(i)
        birth = float(smoothstep(0., .28, age))
        death = float(1.-smoothstep(2.15,2.8,age))
        strength = birth*death
        for j in range(8):
            trailing_age = max(0.,age-j*.078)
            x,y = advect_cloud(source, trailing_age, i*.73)
            # Mild curling/noise to produce irregular CLOUDS, never
            # straight tracer lines or rigid concentric rings.
            x += 2.6*math.sin(2.7*i+j*1.3+age*3.7)
            y += 2.2*math.cos(1.9*i+j*1.1+age*3.1)
            x -= FEED_X0
            y -= FEED_Y0
            opacity = strength*(1.-j/11.)
            size = (7.7+3.*math.sin(i*1.73+j*.93)**2)*(1.+.10*trailing_age)
            if -20 < x < ww+20 and -20 < y < hh+20:
                cv2.circle(black,(int(x),int(y)),max(2,int(size)),
                           min(255,int(200*opacity)),-1,cv2.LINE_AA)
                cv2.circle(violet,(int(x+2),int(y-2)),max(2,int(size*.70)),
                           min(255,int(170*opacity)),-1,cv2.LINE_AA)
    # Bloom into soft, layered cloud masses with a few detailed purple wisps.
    late = float(smoothstep(4.85,6.25,t))
    black = cv2.GaussianBlur(black, (0,0), 4.+late*5.).astype(np.float32)/255.
    violet = cv2.GaussianBlur(violet, (0,0), 2.8+late*5.).astype(np.float32)/255.
    return black, violet

def render_overlay(t, base, portal_source):
    """Composite ONLY cloud feeder streams and the reference portal within C.

    All other pixels remain identical to the derived original portrait.
    Android's unchanged native title is always rendered above this movie.
    """
    portal_opacity = portal_phase(t)
    cloud_opacity = smoke_phase(t)
    if portal_opacity == 0. and cloud_opacity == 0.:
        return base
    scene = base.copy()
    x0,y0,x1,y1 = FEED_X0,FEED_Y0,FEED_X1,FEED_Y1
    target = scene[y0:y1,x0:x1]
    mask = opening_mask()

    if cloud_opacity > 0:
        black,violet = make_clouds(t)
        # A soft, slightly turbulent black-purple cloud layer originates
        # at the C's inside edge, then curls inward to feed the vortex.
        darkness = np.clip(black*2.15*cloud_opacity*mask,0.,.78)
        glow = np.clip(violet*1.55*cloud_opacity*mask,0.,.92)
        target *= (1.-darkness[:,:,None])
        target += glow[:,:,None]*np.array([125.,31.,215.],np.float32)

    if portal_opacity > 0:
        # Inverse map the user's actual purple/black vortex photo.
        # The center rotates CCW while its luminous rim remains aligned;
        # fade with the cloud feeder as the soundtrack fades from 4.85s.
        xx,yy = np.mgrid[0:2*PORTAL_RY,0:2*PORTAL_RX][::-1]
        xx=xx.astype(np.float32)
        yy=yy.astype(np.float32)
        dx=(xx-PORTAL_RX)/PORTAL_RX
        dy=(yy-PORTAL_RY)/PORTAL_RY
        radius=np.sqrt(dx*dx+dy*dy)
        theta=np.arctan2(-dy,dx)
        twist=.78*t*np.maximum(0.,1.-radius)**1.3
        angle=theta-twist
        src_x=(80.+76.*radius*np.cos(angle)).astype(np.float32)
        src_y=(80.-76.*radius*np.sin(angle)).astype(np.float32)
        warped=cv2.remap(portal_source,src_x,src_y,cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT)
        alpha=(1.-smoothstep(.86,.99,radius))*portal_opacity
        # This soft alpha is not a painted circle: every color comes from
        # the actual user's reference. Keep C facets outside the mask.
        px0=PORTAL_X-PORTAL_RX-FEED_X0
        py0=PORTAL_Y-PORTAL_RY-FEED_Y0
        patch=target[py0:py0+2*PORTAL_RY,px0:px0+2*PORTAL_RX]
        aperture=mask[py0:py0+2*PORTAL_RY,px0:px0+2*PORTAL_RX]
        alpha*=aperture
        patch[:]=patch*(1.-alpha[:,:,None])+warped*alpha[:,:,None]
    return scene


def main():
    base = make_base()
    portal = make_portal_source()
    ffmpeg = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
              "-f", "rawvideo", "-pixel_format", "rgb24",
              "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", str(FPS),
              "-i", "-", "-an", "-c:v", "libx264", "-preset", "fast",
              "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
              str(OUT)]
    proc = subprocess.Popen(ffmpeg, stdin=subprocess.PIPE)
    storyboard = []
    for frame_index in range(FPS*SECONDS):
        t = frame_index/FPS
        frame = np.uint8(np.clip(render_overlay(t, base, portal), 0, 255))
        proc.stdin.write(frame.tobytes())
        if frame_index in (0, 27, 60, 96, 136, 167):
            storyboard.append(Image.fromarray(frame, "RGB").resize(
                (240, 460), Image.Resampling.LANCZOS))
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("Portal-only MP4 H.264 encoding failed")
    cap = cv2.VideoCapture(str(OUT))
    assert cap.isOpened() and round(cap.get(cv2.CAP_PROP_FRAME_COUNT)) == 168
    assert round(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) == WIDTH
    assert round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) == HEIGHT
    cap.release()
    contact = Image.new("RGB", (720, 920))
    for index, img in enumerate(storyboard):
        contact.paste(img, ((index%3)*240, (index//3)*460))
    contact.save(ROOT / "Charoite_C_Edge_Fed_Portal_7s_Storyboard.jpg", quality=89)
    print("CHAROITE_C_EDGE_FED_PORTAL_7_SECONDS=PASS", OUT.stat().st_size)


if __name__ == "__main__":
    main()

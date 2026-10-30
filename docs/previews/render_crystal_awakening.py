#!/usr/bin/env python3
"""Seven-second brilliant crystalline C and inward-flowing violet energy feeding the reference vortex.

The original crystal C geometry, full-screen scenery and native Android wordmark
remain fixed. Only strong luminous violet light on the C, flowing energy ribbons and the
portal texture change; the boot art and title never switch. In
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
OUT = ROOT / "Charoite_C_Energy_Reference_Portal_7s.mp4"
SOURCE = ROOT / "next-generation/assets/charoite_user_edited_portal_v33.webp"
WIDTH, HEIGHT, FPS, SECONDS = 480, 920, 30, 7

# Placement is relative to the same 960x1840 portrait art used by
# CrystalArtwork; these are 480x920 coordinates in the C's open center.
# Portal center and extent are measured against the user's red-spiral
# placement guide: it must FILL the opening, not look like a small circle.
PORTAL_X, PORTAL_Y = 278, 417
PORTAL_RX, PORTAL_RY = 103, 114


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
    """Actual vortex texture cropped from the newly approved edited boot image."""
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


# Hand-traced outer and INNER crystalline C rims in the 480x920 portrait.
# Only the existing crystal changes in brightness, never shape or position.
OUTER_C_RIM = np.array([
    (361.,322.), (334.,289.), (298.,268.), (256.,260.),
    (208.,270.), (166.,294.), (129.,332.), (113.,374.),
    (113.,431.), (128.,482.), (162.,531.), (213.,563.),
    (271.,576.), (333.,558.)
],dtype=np.float32)

# Hand-traced INNER rim of the actual crystal C, in the 480x920 portrait.
# These are separate geometry references: the crystal artwork is NEVER drawn
# or modified by these paths, including at the emitter locations.
INNER_C_RIM = np.array([
    (340.,344.), (324.,320.), (299.,301.), (268.,289.),
    (234.,286.), (199.,303.), (171.,329.), (152.,368.),
    (150.,411.), (161.,454.), (187.,488.), (225.,506.),
    (263.,510.), (305.,497.)
], dtype=np.float32)

# This localized aperture contains flowing energy feeding the portal.
# The C itself glows via a separate geometry-matched bloom; the original
# background, title and underlying C geometry remain untouched.
FEED_X0, FEED_Y0, FEED_X1, FEED_Y1 = 111, 262, 408, 569


def energy_phase(t):
    """Energy grows from the C's rim, then fades with the audio tail."""
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


def advect_energy(source, age, seed=0.):
    """Move luminous ribbons from the C's inner rim toward the portal CCW.

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
        [(358.,331.), (336.,307.), (304.,287.), (270.,278.),
         (231.,279.), (197.,296.), (168.,324.), (147.,361.),
         (145.,414.), (158.,456.), (185.,494.), (222.,525.),
         (274.,538.), (334.,534.), (402.,551.), (403.,308.)],
        dtype=np.float32)
    points[:,0] -= FEED_X0
    points[:,1] -= FEED_Y0
    cv2.fillPoly(stencil, [np.rint(points).astype(np.int32)], 255)
    return cv2.GaussianBlur(stencil, (0,0), 3).astype(np.float32)/255.


def crystal_phase(t):
    """Unmistakable crystal bloom rises with the energy and fades with audio."""
    return float(smoothstep(.12, 1.20, t) *
                 (1.-smoothstep(4.85, 6.30, t)))


def crystal_glow_layers():
    """Strong but geometry-matched crystal illumination, without any redesign.

    The crystal's actual inner/outer edges are bright lilac-white and cast
    broad violet bloom. No motion, stretching or modification to source art.
    """
    if hasattr(crystal_glow_layers, "_cache"):
        return crystal_glow_layers._cache
    fill = np.zeros((HEIGHT,WIDTH),np.uint8)
    band = np.vstack([OUTER_C_RIM, INNER_C_RIM[::-1]])
    cv2.fillPoly(fill,[np.rint(band).astype(np.int32)],255)
    edge = np.zeros_like(fill)
    for rim in (OUTER_C_RIM, INNER_C_RIM):
        cv2.polylines(edge,[np.rint(rim).astype(np.int32)],False,255,10,cv2.LINE_AA)
    material = cv2.GaussianBlur(fill,(0,0),5).astype(np.float32)/255.
    aura = cv2.GaussianBlur(edge,(0,0),20).astype(np.float32)/255.
    highlights = cv2.GaussianBlur(edge,(0,0),2).astype(np.float32)/255.
    result = (material,aura,highlights)
    crystal_glow_layers._cache = result
    return result



def make_energy_streams(t):
    """Continuous electric ribbons, not puffs, fog, smoke or dark circles.

    Staggered strands physically join the C's inner facets to the vortex.
    Thin luminous cores, halo and moving bright pulses travel along
    contracting CCW paths; no black compositing is used for these streams.
    """
    hh, ww = FEED_Y1-FEED_Y0, FEED_X1-FEED_X0
    halo = np.zeros((hh,ww),np.uint8)
    filaments = np.zeros_like(halo)
    sparks = np.zeros_like(halo)
    growth = float(smoothstep(.2, 2.0, t))
    for i in range(32):
        source = rim_source(i)
        seed=i*.81
        max_age = .13 + 1.98*growth
        points=[]
        for j in range(31):
            age = max_age*j/30.
            x,y = advect_energy(source,age,seed)
            # Gentle flowing wave along the strand; it stays rooted at C.
            wobble=3.3*math.sin(age*5.1-i*.61+t*1.4)*(age/max_age)*(.9-age/3.)
            x+=wobble*math.sin(age*1.9+seed)
            y+=wobble*math.cos(age*1.9+seed)
            points.append((int(x-FEED_X0),int(y-FEED_Y0)))
        path=np.asarray(points,np.int32).reshape(-1,1,2)
        # A few bright continuous strands are preferable to a blurry cloud.
        cv2.polylines(halo,[path],False,115+(i%4)*18,7,cv2.LINE_AA)
        cv2.polylines(filaments,[path],False,178+(i%3)*25,2,cv2.LINE_AA)

        # Light travels from C to the portal: each pulse advances inward.
        travel = (.32*t + .107*i) % 1.
        pulse_age=.12+max_age*travel
        px,py=advect_energy(source,pulse_age,seed)
        px-=FEED_X0
        py-=FEED_Y0
        cv2.circle(sparks,(int(px),int(py)),3,255,-1,cv2.LINE_AA)
        cv2.circle(sparks,(int(px),int(py)),6,125,-1,cv2.LINE_AA)

    broad = cv2.GaussianBlur(halo,(0,0),8).astype(np.float32)/255.
    fine = cv2.GaussianBlur(filaments,(0,0),1.2).astype(np.float32)/255.
    particles = cv2.GaussianBlur(sparks,(0,0),2).astype(np.float32)/255.
    return broad, fine, particles



def render_overlay(t, base, portal_source):
    """Glow only the C; animate reference vortex and electric energy in C.

    The portrait art itself and Android-native title remain the same pixels.
    All light and vortex layers reach zero before the seven-second dismissal.
    """
    portal_opacity = portal_phase(t)
    energy_opacity = energy_phase(t)
    glow_opacity = crystal_phase(t)
    if portal_opacity == 0. and energy_opacity == 0. and glow_opacity == 0.:
        return base
    scene = base.copy()
    if glow_opacity:
        material,aura,highlights = crystal_glow_layers()
        breathe = .91 + .09*math.sin(t*1.6)**2
        energy = glow_opacity*breathe
        # Strong visible aura wrapping the crystal's true C contours.
        scene += (material*.38+aura*3.2)[:,:,None]*energy*np.array(
            [119.,54.,185.],np.float32)
        # Bring the edge and facet highlights toward violet-white, rather
        # than merely tinting already-saturated purple material.
        whiten = np.clip(highlights*energy*.88,0.,.88)
        scene = scene*(1.-whiten[:,:,None])+np.array(
            [250.,218.,255.],np.float32)*whiten[:,:,None]
        scene += highlights[:,:,None]*energy*np.array(
            [44.,35.,66.],np.float32)

    x0,y0,x1,y1 = FEED_X0,FEED_Y0,FEED_X1,FEED_Y1
    target = scene[y0:y1,x0:x1]
    mask = opening_mask()
    if portal_opacity > 0:
        # Keep exact reference texture and expanded vortex placement.
        xx,yy = np.mgrid[0:2*PORTAL_RY,0:2*PORTAL_RX][::-1]
        xx=xx.astype(np.float32)
        yy=yy.astype(np.float32)
        dx=(xx-PORTAL_RX)/PORTAL_RX
        dy=(yy-PORTAL_RY)/PORTAL_RY
        radius=np.sqrt(dx*dx+dy*dy)
        theta=np.arctan2(-dy,dx)
        twist=1.05*t*np.maximum(0.,1.-radius)**1.10
        angle=theta-twist
        src_x=(80.+76.*radius*np.cos(angle)).astype(np.float32)
        src_y=(80.-76.*radius*np.sin(angle)).astype(np.float32)
        warped=cv2.remap(portal_source,src_x,src_y,cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT)
        alpha=(1.-smoothstep(.87,.995,radius))*portal_opacity
        px0=PORTAL_X-PORTAL_RX-FEED_X0
        py0=PORTAL_Y-PORTAL_RY-FEED_Y0
        patch=target[py0:py0+2*PORTAL_RY,px0:px0+2*PORTAL_RX]
        aperture=mask[py0:py0+2*PORTAL_RY,px0:px0+2*PORTAL_RX]
        alpha*=aperture
        patch[:]=patch*(1.-alpha[:,:,None])+warped*alpha[:,:,None]

    if energy_opacity > 0:
        # Draw the energy ABOVE the vortex so streams visibly merge into it.
        # Alpha-aperture prevents the animated lines covering C material.
        broad,fine,particles = make_energy_streams(t)
        broad=np.clip(broad*energy_opacity*mask*2.9,0.,.85)
        fine=np.clip(fine*energy_opacity*mask*1.45,0.,.95)
        particles=np.clip(particles*energy_opacity*mask*1.9,0.,1.)
        target += broad[:,:,None]*np.array([100.,32.,186.],np.float32)
        target += fine[:,:,None]*np.array([190.,116.,232.],np.float32)
        target += particles[:,:,None]*np.array([140.,111.,228.],np.float32)
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
        if frame_index in (0, 33, 75, 120, 170, 209):
            storyboard.append(Image.fromarray(frame, "RGB").resize(
                (240, 460), Image.Resampling.LANCZOS))
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("Portal-only MP4 H.264 encoding failed")
    cap = cv2.VideoCapture(str(OUT))
    assert cap.isOpened() and round(cap.get(cv2.CAP_PROP_FRAME_COUNT)) == FPS * SECONDS
    assert round(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) == WIDTH
    assert round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) == HEIGHT
    cap.release()
    contact = Image.new("RGB", (720, 920))
    for index, img in enumerate(storyboard):
        contact.paste(img, ((index%3)*240, (index//3)*460))
    contact.save(ROOT / "Charoite_C_Energy_Reference_Portal_7s_Storyboard.jpg", quality=89)
    print("CHAROITE_C_ENERGY_REFERENCE_PORTAL_7_SECONDS=PASS", OUT.stat().st_size)


if __name__ == "__main__":
    main()

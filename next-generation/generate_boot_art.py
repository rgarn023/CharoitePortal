#!/usr/bin/env python3
"""Deterministic, high-resolution Charoite Next splash artwork.

Original procedural 768px crystal-vortex scene. Uses only Python's standard
library. This is a splash-only asset; the user's approved launcher icon stays
unaltered in stable Portal and Next's launcher icon.
"""
from pathlib import Path
import math
import random
import struct
import zlib

SIZE = 768
TAU = math.tau

def clamp(n):
    return max(0, min(255, int(n + .5)))

def generate(path):
    path = Path(path)
    if path.exists():
        raise ValueError("Refusing to overwrite existing Charoite artwork")
    rng = random.Random(4261029)
    stars = [(rng.randrange(SIZE), rng.randrange(550), rng.choice([1, 1, 1, 2, 3]),
              rng.uniform(.3, .9)) for _ in range(190)]
    buf = bytearray()
    for y in range(SIZE):
        buf.append(0)  # PNG filter: None
        v = y / SIZE
        for x in range(SIZE):
            u = x / SIZE
            dx = (x - 384) / 265
            dy = (y - 314) / 265
            r = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            # Midnight-violet nebula and a luminous crystalline circular gate.
            nebula = max(0, 1 - r / 1.9)
            cloud = .5 + .5 * math.sin(6.3 * u + 5.1 * v +
                                      2.3 * math.sin(8.6 * v))
            ring_r = 0.84 + .047 * math.sin(7 * angle) + .023 * math.cos(17 * angle)
            ring = math.exp(-((r - ring_r) / .056)**2)
            halo = math.exp(-((r - ring_r) / .18)**2)
            inner = max(0, 1 - r / .84)
            spiral = max(0, math.sin(angle * 3.0 - 5.9 * r +
                                     .7 * math.sin(angle * 8)))
            spiral *= math.exp(-((r - .7) / .23)**2)
            shimmer = .76 + .24 * math.sin(angle * 11 + r * 42)
            ring *= shimmer
            purple = 26 * nebula + 28 * cloud * nebula + 116 * ring + 39 * halo + 56 * spiral
            blue = 12 * nebula + 17 * cloud + 78 * inner + 55 * spiral
            hot = 92 * ring + 22 * spiral
            red = 9 + .46 * purple + .8 * hot
            green = 5 + .15 * purple + .48 * hot + .24 * blue
            blue_ch = 25 + purple + blue + .65 * hot
            # The central far-world horizon and icy-blue distant glow.
            central = math.exp(-(dx * dx / .2 + (dy - .04)**2 / .14))
            red += 23 * central
            green += 55 * central
            blue_ch += 100 * central
            # Dark crystal silhouettes rising around the portal.
            edge = abs(x - 384) / 384
            ridge = 500 - 190 * edge - 32 * math.sin(x / 37) - 18 * math.sin(x / 16)
            if y > ridge and y < 575 and edge > .54:
                shade = max(.17, .42 - .25 * (y - ridge) / 190)
                red *= shade
                green *= shade
                blue_ch *= shade
            # Water below the portal: horizontal violet reflection ribbons.
            if y > 568:
                t = (y - 568) / 200
                wave = math.sin(y * .27 + math.sin(x * .035) * 2.4)
                reflection = math.exp(-((x - 384) / (155 + 255 * t))**2)
                streak = max(0, wave)**12 * (1 - .56 * t) * reflection
                red = 6 + .28 * red + 106 * streak
                green = 4 + .2 * green + 58 * streak
                blue_ch = 17 + .38 * blue_ch + 155 * streak
                # Subtle vertical reflection of the gateway.
                glint = max(0, math.cos((x-384) / (27 + t*150)))**14
                red += 34 * glint * reflection
                green += 17 * glint * reflection
                blue_ch += 62 * glint * reflection
            buf.extend((clamp(red), clamp(green), clamp(blue_ch)))
    # Pinpoint stars, using bounded per-star writes (no photo/third-party files).
    pitch = 1 + 3 * SIZE
    for cx, cy, radius, power in stars:
        for oy in range(-radius*2, radius*2+1):
            py = cy + oy
            if py < 0 or py >= SIZE: continue
            for ox in range(-radius*2, radius*2+1):
                px = cx + ox
                if px < 0 or px >= SIZE: continue
                d = math.hypot(ox, oy)
                strength = 200 * power * math.exp(-(d / max(.7, radius))**2)
                index = py * pitch + 1 + 3*px
                for channel, boost in enumerate((.74, .83, 1.0)):
                    buf[index+channel] = clamp(buf[index+channel] + strength * boost)
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(
            ">I", zlib.crc32(kind + data) & 0xffffffff)
    header = b"\x89PNG\r\n\x1a\n"
    image = (header
             + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
             + chunk(b"IDAT", zlib.compress(buf, level=9))
             + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image)
    return (SIZE, SIZE)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: generate_boot_art.py OUTPUT.png")
    print(generate(sys.argv[1]))

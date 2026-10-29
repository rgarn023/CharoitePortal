#!/usr/bin/env python3
"""Produce an original deterministic crystal / glass-chime startup sound.

Standard library only. Called during the isolated Next APK CI build.
Never reads or writes user/app storage.
"""
import math
from pathlib import Path
import struct
import sys
import wave

RATE = 44100
DURATION_SECONDS = 1.85
NOTES = (
    # Delayed, upward resonant glass tones. No copyrighted samples.
    (0.00, 783.9909, 0.43),  # G5
    (0.12, 1046.5023, 0.34), # C6
    (0.25, 1318.5102, 0.30), # E6
    (0.39, 1567.9817, 0.24), # G6
)

def sample(t):
    value = 0.0
    for onset, hz, strength in NOTES:
        elapsed = t - onset
        if elapsed < 0:
            continue
        # Fast glass attack, exponential resonant tail and airy beating.
        attack = 1.0 - math.exp(-elapsed * 145.0)
        decay = math.exp(-elapsed * 3.9)
        body = (
            0.78 * math.sin(2 * math.pi * hz * elapsed) +
            0.16 * math.sin(2 * math.pi * hz * 2.014 * elapsed + 0.16) +
            0.075 * math.sin(2 * math.pi * hz * 3.977 * elapsed + 0.53)
        )
        value += strength * attack * decay * body
        # Quiet delayed glass reflection, not an external audio sample.
        if elapsed > .095:
            echo = elapsed - .095
            value += strength * 0.13 * math.exp(-echo * 4.8) * math.sin(
                2 * math.pi * hz * echo + 0.35)
    # Sound is deliberately subtle; final fade avoids PCM clicks.
    fade = min(1.0, max(0.0, (DURATION_SECONDS - t) / 0.16))
    return max(-1.0, min(1.0, value * fade * 0.72))

def generate(path):
    path = Path(path)
    if path.suffix != ".wav" or path.exists():
        raise ValueError("Expected an unused WAV build output path")
    path.parent.mkdir(parents=True, exist_ok=True)
    count = round(RATE * DURATION_SECONDS)
    pcm = bytearray()
    for i in range(count):
        pcm.extend(struct.pack("<h", round(sample(i / RATE) * 32767)))
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(RATE)
        audio.writeframes(pcm)
    return count

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: generate_crystal_startup.py NEW_OUTPUT.wav")
    count = generate(sys.argv[1])
    print(f"CHAROITE_CRYSTAL_CHIME_GENERATED=PASS frames={count}")

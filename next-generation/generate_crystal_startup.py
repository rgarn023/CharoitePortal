#!/usr/bin/env python3
"""Original, slow and mysterious Charoite Core arrival atmosphere.

A warm crystalline resonance blooms gradually out of a quiet nebula drone,
then dissolves into a long shimmer. No notification-style repeated ring,
no borrowed samples, and no licensed/copyrighted musical motifs.
Standard-library PCM synthesis; isolated to experimental Next build.
"""
import math
from pathlib import Path
import struct
import sys
import wave

RATE = 44100
DURATION_SECONDS = 4.2
# Sparse original tones: low suspended foundation, two slowly emerging
# harmonic glass voices, with gentle pitch drift; no fast-note arpeggio.
VOICES = (
    (0.00, 146.83, 0.25, 0.42, 2.3),  # low D, distant
    (0.24, 220.00, 0.15, 0.85, 2.35),
    (0.78, 293.66, 0.13, 0.95, 2.25),
    (1.18, 440.00, 0.08, 0.80, 1.78),
)

def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)

def sample(t):
    value = 0.0
    for onset, hz, amp, attack, tail in VOICES:
        elapsed = t - onset
        if elapsed <= 0.0:
            continue
        envelope = smoothstep(elapsed / attack) * math.exp(-max(0.0, elapsed-attack)/tail)
        phase = 2.0 * math.pi * hz * (elapsed + 0.00055 * math.sin(2 * math.pi * .31 * elapsed))
        # Slight inharmonicity supplies a mysterious glass color without a ding.
        body = (0.82 * math.sin(phase) +
                0.16 * math.sin(2.013 * phase + 0.28) +
                0.07 * math.sin(3.021 * phase + 1.18))
        value += amp * envelope * body
        # Soft echo across the crystal, deliberately quieter than the body.
        if elapsed > .36:
            reflection = elapsed - .36
            value += (amp * .105 * math.exp(-reflection / 1.9) *
                      math.sin(2 * math.pi * hz * reflection + .72))
    # 700 ms of silence-free fade-out avoids a hard ending.
    fade = smoothstep((DURATION_SECONDS-t)/.82)
    return max(-1.0, min(1.0, value * fade * .88))

def generate(path):
    path = Path(path)
    if path.suffix != ".wav" or path.exists():
        raise ValueError("Expected unused WAV build output path")
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
    print(f"CHAROITE_MYSTERIOUS_CRYSTAL_STARTUP=PASS frames={generate(sys.argv[1])}")

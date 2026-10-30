#!/usr/bin/env python3
"""Ten-second, slow and mysterious Charoite crystal BOOT atmosphere.

A warm crystalline resonance blooms gradually out of a quiet nebula drone,
then dissolves into a long ten-second shimmer. No notification-style repeated ring,
no borrowed samples, and no licensed/copyrighted musical motifs.
Standard-library PCM synthesis; isolated to experimental Next build.
"""
import math
from pathlib import Path
import struct
import sys
import wave

RATE = 44100
DURATION_SECONDS = 10.0
# Sparse original tones: low suspended foundation, two slowly emerging
# harmonic glass voices, with gentle pitch drift; no fast-note arpeggio.
VOICES = (
    (0.00, 146.83, 0.25, 0.42, 5.4),  # low D, distant
    (0.24, 220.00, 0.15, 0.85, 5.0),
    (0.78, 293.66, 0.13, 0.95, 5.3),
    (1.18, 440.00, 0.08, 0.80, 4.7),
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
        # Soft crystalline partials, kept close to harmonics so the sound
        # feels mysterious without the raspy interference heard as static.
        body = (0.90 * math.sin(phase) +
                0.095 * math.sin(2.003 * phase + 0.28) +
                0.025 * math.sin(3.006 * phase + 1.18))
        value += amp * envelope * body
        # Avoid an instantaneous echo onset: a delayed sine starting at
        # nonzero phase creates a discontinuity (audible click/crackle).
        # A 140 ms smooth envelope preserves the distant crystal reflection.
        if elapsed > .36:
            reflection = elapsed - .36
            echo_attack = smoothstep(reflection / .14)
            value += (amp * .085 * echo_attack *
                      math.exp(-reflection / 1.9) *
                      math.sin(2 * math.pi * hz * reflection + .72))
    # The prolonged suspended resonance is most audible through seconds 4–9.
    # A softly swelling glass overtone keeps the energy present under the
    # 10-second cloudy animation rather than leaving its last half silent.
    airy_attack = smoothstep((t-2.3)/2.1)
    breath = (0.022 * math.sin(2 * math.pi * 293.66 * t + .12 *
                math.sin(2 * math.pi * .21 * t)) +
              0.013 * math.sin(2 * math.pi * 440.0 * t + .06 *
                math.sin(2 * math.pi * .13 * t)))
    value += airy_attack * breath * (0.82 + .18 * math.sin(.62*t)**2)

    # 1.4 seconds of smooth fade reaches digital silence at the EXACT end.
    # The animation and PCM WAV share the same 10,000 ms duration.
    fade = smoothstep((DURATION_SECONDS-t)/1.40)
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

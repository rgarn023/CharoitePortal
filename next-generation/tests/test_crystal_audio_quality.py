"""Regression tests for unwanted startup-sound crackle in Charoite Next.

The old delayed echo began at a nonzero sine phase with no onset envelope.
That caused discontinuities at 0.36, 0.60, 1.14 and 1.54 seconds.
These tests check *actual samples*, not just presence of string markers.
"""
from pathlib import Path
import importlib.util
import math
import tempfile
import unittest
import wave

SCRIPT = Path(__file__).resolve().parents[1] / "generate_crystal_startup.py"
spec = importlib.util.spec_from_file_location("next_crystal_quality", SCRIPT)
crystal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crystal)


class CrystalAudioQualityTest(unittest.TestCase):
    def test_echo_onsets_have_no_abrupt_sample_steps(self):
        dt = 1.0 / crystal.RATE
        for onset, *_ in crystal.VOICES:
            t = onset + .36
            samples = [crystal.sample(t + k * dt) for k in (-2, -1, 0, 1, 2)]
            # Second difference catches the 0.015 abrupt echo jump in v0.14.
            for i in range(1, 4):
                change = abs(samples[i+1] - 2*samples[i] + samples[i-1])
                self.assertLess(change, .004, f"Echo click at {t:.3f}s")

    def test_quiet_mysterious_tone_with_no_digital_clipping(self):
        # Sample across whole recording; clipping/static should not be part
        # of the generated source, independent of the Android playback route.
        values = [crystal.sample(i / crystal.RATE)
                  for i in range(0, round(crystal.RATE*crystal.DURATION_SECONDS), 20)]
        self.assertTrue(all(math.isfinite(v) for v in values))
        self.assertGreater(max(abs(v) for v in values), .04)
        self.assertLess(max(abs(v) for v in values), .70)
        self.assertLess(abs(crystal.sample(0)), 1e-6)
        self.assertLess(abs(crystal.sample(crystal.DURATION_SECONDS-1/crystal.RATE)), .001)

    def test_deferred_android_audio_start_has_safe_silent_tail(self):
        # Android starts audio after the splash timer, so the last 650ms
        # must be completely silent even after modest startup delay.
        self.assertEqual(crystal.DURATION_SECONDS, 7.0)
        self.assertGreater(abs(crystal.sample(5.0)), .001)
        for t in (6.36, 6.65, 6.95, 6.999):
            self.assertEqual(crystal.sample(t), 0.0)

    def test_output_format_is_compatible_with_static_audio_track(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/"startup.wav"
            frames = crystal.generate(output)
            self.assertEqual(frames, 308700)  # seven seconds at 44.1 kHz PCM
            with wave.open(str(output), "rb") as audio:
                self.assertEqual(audio.getnchannels(), 1)
                self.assertEqual(audio.getsampwidth(), 2)
                self.assertEqual(audio.getframerate(), 44100)
                self.assertEqual(audio.getnframes(), frames)
            data=output.read_bytes()
            self.assertEqual(data[:4], b"RIFF")
            self.assertEqual(data[8:12], b"WAVE")
            self.assertEqual(data[36:40], b"data")
            self.assertEqual(len(data), 44 + frames*2)


if __name__ == "__main__":
    unittest.main()

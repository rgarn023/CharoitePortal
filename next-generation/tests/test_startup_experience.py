"""Next-only five-second branded cold start and original crystal sound contracts."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
import wave
import struct

ROOT = Path(__file__).resolve().parents[1]
BOOT = (ROOT / "CharoiteNextBootActivity.java").read_text(encoding="utf-8")
PREP = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
OVERLAY = (ROOT.parent / "runtime-preview/overlay.py").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("charoite_crystal",ROOT/"generate_crystal_startup.py")
sound=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sound)

class StartupExperienceTest(unittest.TestCase):
    def test_five_second_cold_start_only(self):
        self.assertIn("BOOT_DURATION_MS = 5000L", BOOT)
        self.assertIn("handler.postDelayed(openMain, BOOT_DURATION_MS)", BOOT)
        self.assertIn("handler.removeCallbacksAndMessages(null)",BOOT)
        self.assertIn("new Intent(this, com.winlator.TouhouEntryActivity.class)",BOOT)
        self.assertIn("finish();",BOOT)
        self.assertIn('com.winlator.R.drawable.charoite_portal_icon',BOOT)
        self.assertIn("Gravity.CENTER",BOOT)
        self.assertIn("CHAROITE CORE",BOOT)
        self.assertIn('com.charoitx',PREP)
        self.assertIn('versionCode 36',PREP)
        self.assertIn('11.2-next.0.5',PREP)

    def test_main_screen_sound_only_and_silent_mode(self):
        self.assertIn('main.putExtra(EXTRA_PLAY_CHIME, true)',BOOT)
        self.assertIn("playArrivalChimeIfRequested(Activity activity)",BOOT)
        self.assertIn("intent.removeExtra(EXTRA_PLAY_CHIME)",BOOT)
        self.assertIn("activity.hasWindowFocus()",BOOT)
        self.assertIn("AudioManager.RINGER_MODE_SILENT",BOOT)
        self.assertIn("com.winlator.R.raw.charoite_crystal_startup", BOOT)
        self.assertIn("player.setOnCompletionListener(MediaPlayer::release)",BOOT)
        self.assertIn("playArrivalChimeIfRequested(this)",PREP)
        self.assertIn("generate_crystal_chime(chime)",PREP)
        self.assertIn("android.intent.category.LAUNCHER",PREP)
        self.assertIn('entry.remove(filters)',PREP)
        self.assertIn('boot.append(filters)',PREP)
        # Neither Wine, games nor installed prefixes are part of splash/audio.
        for bad in ("WINEPREFIX", "ProcessBuilder", "Runtime.getRuntime()", "deleteRecursively",
                    "wineboot", "clearApplicationUserData", "startGame", "loadLibrary"):
            self.assertNotIn(bad,BOOT)
        self.assertIn("charoite_portal_icon.jpg",OVERLAY)

    def test_original_wav_is_valid_small_pcm(self):
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/"crystal.wav"
            frames=sound.generate(output)
            self.assertEqual(frames,round(sound.RATE*sound.DURATION_SECONDS))
            with wave.open(str(output),"rb") as wav:
                self.assertEqual(wav.getframerate(),44100)
                self.assertEqual(wav.getnchannels(),1)
                self.assertEqual(wav.getsampwidth(),2)
                self.assertEqual(wav.getnframes(),frames)
                pcm=wav.readframes(frames)
                samples=struct.unpack("<"+str(frames)+"h",pcm)
                self.assertGreater(max(abs(s) for s in samples),400)
                self.assertTrue(all(abs(s) < 200 for s in samples[-10:]))
            with self.assertRaises(ValueError):
                sound.generate(output)

if __name__=="__main__":unittest.main()

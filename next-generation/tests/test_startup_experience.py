"""Next-only five-second branded cold start and original crystal sound contracts."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
import wave
import struct
import zlib
import hashlib

ROOT = Path(__file__).resolve().parents[1]
BOOT = (ROOT / "CharoiteNextBootActivity.java").read_text(encoding="utf-8")
PREP = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
OVERLAY = (ROOT.parent / "runtime-preview/overlay.py").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("charoite_crystal",ROOT/"generate_crystal_startup.py")
sound=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sound)

art_spec=importlib.util.spec_from_file_location("charoite_art",ROOT/"generate_boot_art.py")
art=importlib.util.module_from_spec(art_spec)
art_spec.loader.exec_module(art)

class StartupExperienceTest(unittest.TestCase):
    def test_five_second_start_with_reentry_support(self):
        self.assertIn("BOOT_DURATION_MS = 5000L", BOOT)
        self.assertIn("handler.postDelayed(openMain, BOOT_DURATION_MS)", BOOT)
        self.assertIn("handler.removeCallbacksAndMessages(null)",BOOT)
        self.assertIn("new Intent(this, com.winlator.TouhouEntryActivity.class)",BOOT)
        self.assertIn("finish();",BOOT)
        self.assertIn('com.winlator.R.drawable.charoite_portal_icon',BOOT)
        self.assertIn("Gravity.CENTER",BOOT)
        self.assertIn("CHAROITE CORE",BOOT)
        self.assertIn('com.charoitx',PREP)
        self.assertIn('versionCode 38',PREP)
        self.assertIn('11.2-next.0.7',PREP)

    def test_reentry_requires_whole_application_background(self):
        self.assertIn("ComponentCallbacks2.TRIM_MEMORY_UI_HIDDEN",BOOT)
        self.assertIn("REENTRY_NEEDED.getAndSet(false)",BOOT)
        self.assertIn("showOnBackgroundReentryIfNeeded(Activity activity)",BOOT)
        self.assertIn("createBootView(activity)",BOOT)
        self.assertIn("splash.dismiss()",BOOT)
        self.assertIn("playCrystalChime(activity)",BOOT)
        self.assertIn(".showOnBackgroundReentryIfNeeded(this)", PREP)
        self.assertIn(".noteAppVisibility(level)", PREP)
        self.assertIn("super.onTrimMemory(level)", PREP)
        self.assertNotIn("finishAffinity()",BOOT)
        self.assertNotIn("finishAndRemoveTask()",BOOT)

    def test_crystal_progress_takes_five_seconds(self):
        self.assertIn("new ProgressBar(activity",BOOT)
        self.assertIn("progress.setIndeterminate(false)",BOOT)
        self.assertIn("ObjectAnimator.ofInt(progress",BOOT)
        self.assertIn("animation.setDuration(BOOT_DURATION_MS)",BOOT)
        self.assertIn("LinearInterpolator()",BOOT)
        self.assertIn("STARTING CHAROITE CORE",BOOT)
        self.assertIn("charoite_next_boot_art",BOOT)

    def test_original_high_resolution_splash_is_valid_png(self):
        with tempfile.TemporaryDirectory() as td:
            image=Path(td)/"charoite_next_boot_art.png"
            self.assertEqual(art.generate(image),(768,768))
            raw=image.read_bytes()
            self.assertEqual(raw[:8],b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II",raw[16:24]),(768,768))
            self.assertGreater(len(raw),40000)
            self.assertLess(len(raw),2000000)
            with self.assertRaises(ValueError):
                art.generate(image)
            self.assertIn("generate_boot_art(boot_art)",PREP)
            self.assertIn("drawable-nodpi/charoite_next_boot_art.png",PREP)

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

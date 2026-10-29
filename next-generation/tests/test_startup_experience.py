"""Next-only five-second branded cold start and original crystal sound contracts."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
import wave
import struct
import hashlib

ROOT = Path(__file__).resolve().parents[1]
BOOT = (ROOT / "CharoiteNextBootActivity.java").read_text(encoding="utf-8")
PREP = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
OVERLAY = (ROOT.parent / "runtime-preview/overlay.py").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("charoite_crystal",ROOT/"generate_crystal_startup.py")
sound=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sound)
art_spec=importlib.util.spec_from_file_location('charoite_icon_upscale',ROOT/'generate_high_res_boot_icon.py')
art=importlib.util.module_from_spec(art_spec)
art_spec.loader.exec_module(art)

class StartupExperienceTest(unittest.TestCase):
    def test_five_second_start_with_reentry_support(self):
        self.assertIn("BOOT_DURATION_MS = 5000L", BOOT)
        self.assertIn("handler.postDelayed(openMain, BOOT_DURATION_MS)", BOOT)
        self.assertIn("handler.removeCallbacksAndMessages(null)",BOOT)
        self.assertIn("new Intent(this, com.winlator.TouhouEntryActivity.class)",BOOT)
        self.assertIn("finish();",BOOT)
        self.assertIn('com.winlator.R.drawable.charoite_next_boot_icon_hd',BOOT)
        self.assertIn("Gravity.CENTER",BOOT)
        self.assertIn("CHAROITE CORE",BOOT)
        self.assertIn('com.charoitx',PREP)
        self.assertIn('versionCode 41',PREP)
        self.assertIn('11.2-next.0.10',PREP)

    def test_home_and_recents_reopen_with_internal_navigation_suppressed(self):
        self.assertIn("Application.ActivityLifecycleCallbacks", BOOT)
        self.assertIn("registerActivityLifecycleCallbacks", BOOT)
        self.assertIn("onActivityStopped(Activity a)", BOOT)
        self.assertIn("onActivityStarted(Activity a)", BOOT)
        self.assertIn("onUserLeaveHint()", PREP)
        self.assertIn("noteUserLeaving(this)", PREP)
        self.assertIn("onPause()", PREP)
        self.assertIn("notePortalPaused(this)", PREP)
        self.assertIn("REENTRY_NEEDED.compareAndSet(true, false)", BOOT)
        self.assertIn("!activity.hasWindowFocus()", BOOT)
        self.assertIn("onWindowFocusChanged(boolean hasFocus)", PREP)
        self.assertIn(".onPortalWindowFocusChanged(this, hasFocus)", PREP)
        self.assertIn("onPortalWindowFocusChanged(Activity portal, boolean focused)", BOOT)
        self.assertIn("onNewIntent(Intent intent)", PREP)
        self.assertIn("noteLauncherIntent(intent)", PREP)
        self.assertIn("Intent.ACTION_MAIN", BOOT)
        self.assertIn("Intent.CATEGORY_LAUNCHER", BOOT)
        self.assertIn("started.isEmpty()", BOOT)
        self.assertIn("REENTRY_NEEDED.set(appBackground)", BOOT)
        self.assertIn("!a.isChangingConfigurations()", BOOT)
        self.assertIn("noteDocumentPickerReturn(this)", PREP)
        self.assertIn("REENTRY_NEEDED.set(false)", BOOT)
        self.assertNotIn("TRIM_MEMORY_UI_HIDDEN", BOOT)
        self.assertNotIn("onTrimMemory(", PREP)

    def test_no_unwanted_process_or_prefix_effects(self):
        self.assertIn("showOnBackgroundReentryIfNeeded(Activity activity)", BOOT)
        self.assertIn("createBootView(activity)", BOOT)
        self.assertIn("splash.dismiss()", BOOT)
        self.assertNotIn("ProcessBuilder", BOOT)
        self.assertNotIn("finishAffinity()", BOOT)
        self.assertNotIn("finishAndRemoveTask()", BOOT)

    def test_crystal_progress_takes_five_seconds(self):
        self.assertIn("new ProgressBar(activity",BOOT)
        self.assertIn("progress.setIndeterminate(false)",BOOT)
        self.assertIn("ObjectAnimator.ofInt(progress",BOOT)
        self.assertIn("animation.setDuration(BOOT_DURATION_MS)",BOOT)
        self.assertIn("LinearInterpolator()",BOOT)
        self.assertIn("STARTING CHAROITE CORE",BOOT)
        self.assertIn("charoite_next_boot_icon_hd",BOOT)

    def test_splash_uses_upscaled_original_verified_icon(self):
        self.assertIn("icon.setImageResource(com.winlator.R.drawable.charoite_next_boot_icon_hd)", BOOT)
        self.assertIn("generate_boot_icon(icon, boot_png)", PREP)
        self.assertIn("charoite_portal_icon.jpg", OVERLAY)
        self.assertIn("sha256(image_bytes).hexdigest() == good_sha", OVERLAY)
        self.assertIn("EXPECTED_SHA256", (ROOT/"generate_high_res_boot_icon.py").read_text())
        from PIL import Image
        source = (ROOT.parent/"runtime-preview/charoite_portal_icon.jpg").read_bytes()
        bad = hashlib.sha256(source).hexdigest()
        if bad == "7c5c8fdf88b71fd23fb01740f516b866108edbf57af962aa50bca599bdd1b338":
            source = source[:108] + bytes([0x82])*12 + source[108:]
        self.assertEqual(hashlib.sha256(source).hexdigest(), art.EXPECTED_SHA256)
        with tempfile.TemporaryDirectory() as td:
            inp = Path(td)/"approved.jpg"
            inp.write_bytes(source)
            dest = Path(td)/"boot.png"
            self.assertEqual(art.generate(inp,dest),(768,768))
            with Image.open(dest) as image:
                self.assertEqual(image.size,(768,768))
                self.assertEqual(image.format,"PNG")
            self.assertGreater(dest.stat().st_size, 20000)
            self.assertEqual(inp.read_bytes(),source)
            with self.assertRaises(ValueError):
                art.generate(inp,dest)

    def test_slow_mysterious_sound_after_resume_and_diagnostics(self):
        self.assertIn('main.putExtra(EXTRA_PLAY_CHIME, true)', BOOT)
        self.assertIn("playArrivalChimeIfRequested(Activity activity)", BOOT)
        self.assertIn("intent.removeExtra(EXTRA_PLAY_CHIME)", BOOT)
        self.assertIn("playArrivalChimeIfRequested(this)", PREP)
        self.assertIn("AudioAttributes.USAGE_MEDIA", BOOT)
        self.assertIn("AudioManager.STREAM_MUSIC", BOOT)
        self.assertNotIn("AudioManager.RINGER_MODE_SILENT", BOOT)
        self.assertIn("if (activity.isFinishing() || activity.isDestroyed()", BOOT)
        self.assertIn("!activity.hasWindowFocus()", BOOT)
        self.assertNotIn("activity.hasWindowFocus()", BOOT.split("private static void playCrystalChime(Activity activity) {")[1])
        self.assertIn("player.setOnCompletionListener", BOOT)
        self.assertIn("playCrystalChime(activity)", BOOT)
        self.assertIn("startupReport(Context ctx)", BOOT)
        self.assertIn("Startup / audio diagnostics", PREP)
        self.assertIn("charoite_crystal_startup", BOOT)
        self.assertIn("generate_crystal_chime(chime)", PREP)
        self.assertEqual(sound.DURATION_SECONDS,4.2)
        self.assertLess(max(f for (_, f, _, _, _) in sound.VOICES),500)
        self.assertGreater(min(attack for (_, _, _, attack, _) in sound.VOICES),0.35)
        self.assertIn("mysterious", sound.__doc__.lower())
        self.assertIn("android.intent.category.LAUNCHER", PREP)
        self.assertIn("entry.remove(filters)", PREP)
        self.assertIn("boot.append(filters)", PREP)
        for bad in ("WINEPREFIX", "ProcessBuilder", "Runtime.getRuntime()",
                    "deleteRecursively", "wineboot", "clearApplicationUserData",
                    "startGame", "loadLibrary"):
            self.assertNotIn(bad, BOOT)

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

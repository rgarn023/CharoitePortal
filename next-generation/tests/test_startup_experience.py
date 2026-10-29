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
art_spec=importlib.util.spec_from_file_location('charoite_icon_upscale',ROOT/'recreate_crystal_portal.py')
art=importlib.util.module_from_spec(art_spec)
art_spec.loader.exec_module(art)

class StartupExperienceTest(unittest.TestCase):
    def test_five_second_start_with_reentry_support(self):
        self.assertIn("BOOT_DURATION_MS = 5000L", BOOT)
        self.assertIn("handler.postDelayed(openMain, BOOT_DURATION_MS)", BOOT)
        self.assertIn("handler.removeCallbacksAndMessages(null)",BOOT)
        self.assertIn("new Intent(this, com.winlator.TouhouEntryActivity.class)",BOOT)
        self.assertIn("finish();",BOOT)
        self.assertIn('com.winlator.R.drawable.charoite_next_boot_scene',BOOT)
        self.assertIn("Gravity.CENTER",BOOT)
        self.assertIn("CHAROITE CORE",BOOT)
        self.assertIn('com.charoitx',PREP)
        self.assertIn('versionCode 43',PREP)
        self.assertIn('11.2-next.0.12',PREP)

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
        self.assertNotIn("|| !activity.hasWindowFocus()) return;", BOOT)
        self.assertIn("Window not ready; replay still pending", BOOT)
        self.assertIn("onWindowFocusChanged(boolean hasFocus)", PREP)
        self.assertIn(".onPortalWindowFocusChanged(this, hasFocus)", PREP)
        self.assertIn("onPortalWindowFocusChanged(Activity portal, boolean focused)", BOOT)
        self.assertIn("onNewIntent(Intent intent)", PREP)
        self.assertIn("noteLauncherIntent(intent)", PREP)
        self.assertIn("Intent.ACTION_MAIN", BOOT)
        self.assertIn("Intent.CATEGORY_LAUNCHER", BOOT)
        self.assertIn("started.isEmpty()", BOOT)
        self.assertIn("if (appBackground) REENTRY_NEEDED.set(true)", BOOT)
        self.assertIn("Portal stopped; preserving pending user leave", BOOT)
        self.assertNotIn("REENTRY_NEEDED.set(appBackground)", BOOT)
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
        self.assertIn("charoite_next_boot_scene",BOOT)

    def test_boot_uses_original_recreated_crystal_scene_not_tiny_jpeg(self):
        self.assertIn("icon.setImageResource(com.winlator.R.drawable.charoite_next_boot_scene)",BOOT)
        self.assertIn("render_crystal_portal(boot_png, approved_icon)",PREP)
        self.assertIn("recreate_crystal_portal", PREP)
        self.assertNotIn("generate_boot_icon", PREP)
        source = (ROOT/"recreate_crystal_portal.py").read_text(encoding="utf-8")
        self.assertIn("SIZE = 1536",source)
        self.assertIn("exact artwork",source)
        self.assertIn("SOURCE_SIZE = (128, 128)",source)
        self.assertIn("Image.Resampling.LANCZOS",source)
        self.assertIn("ImageFilter.UnsharpMask",source)
        self.assertIn("stage_launcher_icon",PREP)
        self.assertIn("repaired_jpeg(source)",source)
        self.assertIn('source_dir.parent / "runtime-preview/charoite_portal_icon.jpg"',PREP)
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/"crystal.png"
            icon_source=ROOT.parent / "runtime-preview/charoite_portal_icon.jpg"
            self.assertEqual(art.render(dest,icon_source),(1536,1536))
            with Image.open(dest) as image:
                self.assertEqual(image.size,(1536,1536))
                self.assertEqual(image.format,"PNG")
            self.assertGreater(dest.stat().st_size,100000)
            next_icon = Path(td)/"charoite_portal_icon.jpg"
            next_icon.write_bytes(icon_source.read_bytes())
            self.assertEqual(art.stage_launcher_icon(icon_source,next_icon),(128,128))
            with Image.open(next_icon) as repaired:
                repaired.load()
                self.assertEqual(repaired.size,(128,128))
            # A visually different scene must fail this source-equivalence test.
            from PIL import Image, ImageChops, ImageStat
            from io import BytesIO
            with Image.open(dest) as enhanced, Image.open(BytesIO(art.repaired_jpeg(icon_source))) as original:
                preview=enhanced.convert("RGB").resize((128,128),Image.Resampling.LANCZOS)
                diff=ImageStat.Stat(ImageChops.difference(preview,original.convert("RGB")))
                self.assertLess(max(diff.mean),22, "Boot artwork must match the icon")
            with self.assertRaises(ValueError):
                art.render(dest,icon_source)

    def test_slow_mysterious_sound_after_resume_and_diagnostics(self):
        self.assertIn('main.putExtra(EXTRA_PLAY_CHIME, true)', BOOT)
        self.assertIn("playArrivalChimeIfRequested(Activity activity)", BOOT)
        self.assertIn("intent.removeExtra(EXTRA_PLAY_CHIME)", BOOT)
        self.assertIn("playArrivalChimeIfRequested(this)", PREP)
        self.assertIn("AudioAttributes.USAGE_MEDIA", BOOT)
        self.assertIn("AudioManager.STREAM_MUSIC", BOOT)
        self.assertNotIn("AudioManager.RINGER_MODE_SILENT", BOOT)
        self.assertIn("if (activity.isFinishing() || activity.isDestroyed()", BOOT)
        self.assertNotIn("|| !activity.hasWindowFocus()) return;", BOOT)
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

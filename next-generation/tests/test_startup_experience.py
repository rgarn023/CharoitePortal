"""Next boot: exact approved launcher icon, full-bleed splash, no warm replay."""
from pathlib import Path
import hashlib
import importlib.util
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
BOOT = (ROOT / "CharoiteNextBootActivity.java").read_text(encoding="utf-8")
PREP = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
ART = ROOT / "assets/charoite_next_boot_reference.jpg"
ART_SHA = "2f368b7731f8ff96db03842e0f36b62bc9d22c48fcdb77ed864846d6be44b748"
spec = importlib.util.spec_from_file_location("startup_audio", ROOT / "generate_crystal_startup.py")
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)
art_spec = importlib.util.spec_from_file_location("boot_art", ROOT / "make_fullbleed_boot.py")
art = importlib.util.module_from_spec(art_spec)
art_spec.loader.exec_module(art)


class StartupExperienceTest(unittest.TestCase):
    def test_original_launcher_artwork_preserved_exactly(self):
        from PIL import Image
        with Image.open(ART) as picture:
            picture.load()
            self.assertEqual(picture.size, (1536,1536))
            self.assertEqual(picture.format, "JPEG")
        self.assertEqual(hashlib.sha256(ART.read_bytes()).hexdigest(), ART_SHA)
        self.assertIn("boot_art.write_bytes(image_bytes)", PREP)
        self.assertIn("next_launcher_icon.write_bytes(image_bytes)", PREP)
        self.assertIn("generate_fullbleed_boot(approved_art", PREP)
        self.assertIn("charoite_next_boot_unframed.png", PREP)
        self.assertIn("charoite_next_boot_backdrop.jpg", PREP)
        self.assertIn("versionCode 48", PREP)
        self.assertIn("11.2-next.0.17", PREP)

    def test_boot_foreground_has_no_black_outside_and_backdrop_fills_screen(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            front = Path(td) / "unframed.png"
            back = Path(td) / "backdrop.jpg"
            art.generate(ART, front, back)
            with Image.open(front) as image:
                self.assertEqual(image.size, (1536,1536))
                self.assertEqual(image.mode, "RGBA")
                for xy in ((0,0),(0,1535),(1535,0),(1535,1535)):
                    self.assertLess(image.getpixel(xy)[3], 8)
                self.assertGreater(image.getpixel((768,768))[3], 250)
            with Image.open(back) as image:
                self.assertEqual(image.size, (900,1600))
                for xy in ((0,0),(899,0),(0,1599),(899,1599)):
                    self.assertGreater(max(image.getpixel(xy)), 12)
        self.assertIn("R.drawable.charoite_next_boot_unframed", BOOT)
        self.assertIn("R.drawable.charoite_next_boot_backdrop", BOOT)
        self.assertIn("ImageView.ScaleType.CENTER_CROP", BOOT)
        self.assertIn("ViewGroup.LayoutParams.MATCH_PARENT", BOOT)

    def test_five_second_boot_once_per_real_session(self):
        self.assertIn("BOOT_DURATION_MS = 5000L", BOOT)
        self.assertIn("handler.postDelayed(openMain, BOOT_DURATION_MS)", BOOT)
        self.assertIn("ObjectAnimator.ofInt(progress", BOOT)
        self.assertIn("animation.setDuration(BOOT_DURATION_MS)", BOOT)
        self.assertIn("hasLivePortalInSameTask(this)", BOOT)
        self.assertIn("portal.getTaskId() == launcher.getTaskId()", BOOT)
        self.assertIn("onPortalCreated(Activity portal, Bundle state)", BOOT)
        self.assertIn("showColdPortalFallback(portal, 0)", BOOT)
        self.assertIn("markBootShown(this)", BOOT)
        self.assertIn("LAST_BOOT_VERSION", BOOT)
        self.assertIn("installedVersion(portal)", BOOT)
        self.assertIn("if (state != null && seen == version) return;", BOOT)
        self.assertIn("portal.isTaskRoot()", BOOT)
        self.assertIn("activeColdFallback", BOOT)
        self.assertIn("Portal exited; launcher task root closed", BOOT)
        self.assertIn("if (completed)", BOOT)
        self.assertIn("super.onResume()", BOOT)
        # The root boot Activity must not finish immediately after opening
        # Portal; otherwise Samsung can resume Portal forever without boot.
        launch = BOOT.split("startActivity(main);",1)[1].split("};\n        handler.postDelayed(openMain",1)[0]
        self.assertNotIn("finish();", launch)
        fallback = BOOT.split("public static void onPortalCreated(Activity portal, Bundle state) {",1)[1].split("private static void showColdPortalFallback",1)[0]
        self.assertIn("showColdPortalFallback(portal, 0)", fallback)
        self.assertIn("portal.isChangingConfigurations()", fallback)
        self.assertIn('Already running in same task; boot skipped', BOOT)
        self.assertIn("currentPortal.get()", BOOT)
        self.assertIn("portal.isDestroyed()", BOOT)
        self.assertIn("notePortalDestroyed(this)", PREP)
        self.assertIn(".onPortalResumed(this)", PREP)
        self.assertIn(".onPortalCreated(this, savedInstanceState)", PREP)
        self.assertNotIn("showOnBackgroundReentryIfNeeded", BOOT)
        self.assertNotIn("activeReentryOverlay", BOOT)
        self.assertNotIn("REENTRY_NEEDED", BOOT)
        self.assertNotIn(".notePortalPaused(this)", PREP)
        self.assertNotIn(".onPortalRestart(this)", PREP)
        self.assertNotIn(".noteUserLeaving(this)", PREP)
        self.assertNotIn(".noteLauncherIntent(intent)", PREP)
        resume = BOOT.split("public static void onPortalResumed(Activity portal) {",1)[1].split("\n    }",1)[0]
        self.assertNotIn("createBootView(",resume)
        self.assertIn("playArrivalChimeIfRequested(portal)",resume)

    def test_direct_task_fallback_occurs_only_on_creation(self):
        # Regression for 0.16: finishing the launcher while Portal remains
        # alive prevented the next genuinely fresh task from showing splash.
        direct = BOOT.split("public static void onPortalCreated(Activity portal, Bundle state) {",1)[1].split("private static void showColdPortalFallback",1)[0]
        self.assertIn("onPortalCreated", BOOT)
        self.assertIn("state != null && seen == version", direct)
        self.assertIn("showColdPortalFallback(portal, 0)", direct)
        self.assertIn("portal.isTaskRoot()", direct)
        self.assertIn("installedVersion", direct)
        self.assertIn("intent.getBooleanExtra(EXTRA_PLAY_CHIME, false)", direct)
        resume = BOOT.split("public static void onPortalResumed(Activity portal) {",1)[1].split("\n    }",1)[0]
        self.assertNotIn("showColdPortalFallback", resume)
        self.assertNotIn("createBootView(", resume)
        # New Portal starts from the launcher; switching apps is just resume.
        self.assertNotIn(".notePortalPaused(this)", PREP)
        self.assertNotIn(".noteUserLeaving(this)", PREP)

    def test_first_cold_launch_keeps_the_clean_crystal_sound(self):
        self.assertIn("COLD_ARRIVAL_SOUND_PENDING", BOOT)
        self.assertIn("playPendingColdArrivalIfReady", BOOT)
        self.assertIn("new android.media.AudioTrack.Builder()", BOOT)
        self.assertIn("android.media.AudioTrack.MODE_STATIC", BOOT)
        self.assertIn("MediaPlayer.create(activity", BOOT)
        self.assertIn("R.raw.charoite_crystal_startup", BOOT)
        self.assertIn("AudioAttributes.USAGE_MEDIA", BOOT)
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td)/"startup.wav"
            audio.generate(wav)
            with wave.open(str(wav),"rb") as tone:
                self.assertEqual(tone.getframerate(),44100)
                self.assertEqual(tone.getnframes(),185220)

    def test_no_access_to_saved_games(self):
        for forbidden in ("ProcessBuilder", "deleteRecursively", "finishAffinity()",
                          "finishAndRemoveTask()", "clearApplicationUserData", "WINEPREFIX"):
            self.assertNotIn(forbidden, BOOT)
        self.assertIn("applicationId 'com.charoitx'", PREP)


if __name__ == "__main__":
    unittest.main()

"""Charoite Next boot: exact user-supplied artwork, repeated launch, safe audio."""
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
spec = importlib.util.spec_from_file_location("startup_audio",ROOT / "generate_crystal_startup.py")
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)


class StartupExperienceTest(unittest.TestCase):
    def test_exact_user_supplied_full_resolution_artwork(self):
        from PIL import Image
        with Image.open(ART) as img:
            img.load()
            self.assertEqual(img.size, (1536,1536))
            self.assertEqual(img.format, "JPEG")
        self.assertEqual(hashlib.sha256(ART.read_bytes()).hexdigest(),ART_SHA)
        self.assertIn("boot_art.write_bytes(image_bytes)",PREP)
        self.assertIn("next_launcher_icon.write_bytes(image_bytes)",PREP)
        self.assertIn("charoite_next_boot_reference.jpg",PREP)
        self.assertIn("charoite_next_boot_scene.jpg",PREP)
        self.assertNotIn("render_crystal_portal(",PREP)
        self.assertIn("R.drawable.charoite_next_boot_scene",BOOT)
        self.assertIn("com.charoitx",PREP)
        self.assertIn("versionCode 45",PREP)
        self.assertIn("11.2-next.0.14",PREP)

    def test_five_seconds_on_initial_open_and_each_foreground_return(self):
        self.assertIn("BOOT_DURATION_MS = 5000L",BOOT)
        self.assertIn("handler.postDelayed(openMain, BOOT_DURATION_MS)",BOOT)
        self.assertIn("ObjectAnimator.ofInt(progress",BOOT)
        self.assertIn("animation.setDuration(BOOT_DURATION_MS)",BOOT)
        self.assertIn("new Intent(this, com.winlator.TouhouEntryActivity.class)",BOOT)
        self.assertIn("onPortalRestart(Activity portal)",BOOT)
        self.assertIn("onPortalResumed(Activity portal)",BOOT)
        self.assertIn(".onPortalResumed(this)",PREP)
        self.assertNotIn(".playArrivalChimeIfRequested(this)",PREP)
        self.assertIn("Last-resort onResume replay",BOOT)
        # onRestart is no longer permitted to cancel a later external resume.
        restart=BOOT.split("public static void onPortalRestart(Activity portal) {")[1].split("    /** Every actual Portal resume")[0]
        self.assertNotIn("REENTRY_NEEDED.set(false)",restart)
        self.assertNotIn("SUPPRESS_NEXT_RESTART.getAndSet(false)",restart)
        self.assertIn("onRestart()",PREP)
        self.assertIn(".onPortalRestart(this)",PREP)
        self.assertIn("onNewIntent(Intent intent)",PREP)
        self.assertIn("noteLauncherIntent(intent)",PREP)
        self.assertIn("onPause()",PREP)
        self.assertIn("notePortalPaused(this)",PREP)
        self.assertIn("onWindowFocusChanged(boolean hasFocus)",PREP)

    def test_no_dialog_token_race_and_reopen_without_focus_callback(self):
        self.assertIn("FrameLayout activeReentryOverlay",BOOT)
        self.assertIn("activity.findViewById(android.R.id.content)",BOOT)
        self.assertIn("content.addView(overlay",BOOT)
        self.assertIn("overlay.bringToFront()",BOOT)
        self.assertIn("OVERLAY_HANDLER.postDelayed(activeOverlayTimeout, BOOT_DURATION_MS)",BOOT)
        self.assertIn("removeWarmOverlay(activity, true)",BOOT)
        self.assertIn("removeWarmOverlay(portal, false)",BOOT)
        self.assertNotIn("new Dialog(activity",BOOT)
        self.assertNotIn("WindowManager.BadTokenException",BOOT)
        self.assertNotIn("|| !activity.hasWindowFocus()",BOOT)
        self.assertIn("SUPPRESS_NEXT_RESTART.set(true)",BOOT)
        self.assertIn("SUPPRESS_NEXT_RESTART.getAndSet(false)",BOOT)
        self.assertIn("REENTRY_NEEDED.set(true)",BOOT)
        self.assertIn("if (internalReturn && !explicitHomeOrLauncher)",BOOT)
        self.assertIn("portal.isChangingConfigurations()",BOOT)
        self.assertIn("noteDocumentPickerReturn(this)",PREP)
        self.assertIn("REENTRY_NEEDED.set(false)",BOOT)

    def test_no_games_prefixes_or_installed_data_touched(self):
        for forbidden in ("ProcessBuilder", "Runtime.getRuntime()", "deleteRecursively",
                          "finishAffinity()", "finishAndRemoveTask()", "clearApplicationUserData"):
            self.assertNotIn(forbidden,BOOT)
        self.assertIn('applicationId \'com.charoitx\'',PREP)
        self.assertNotIn("WINEPREFIX",BOOT)

    def test_original_slow_crystal_arrival_sound(self):
        self.assertIn("playCrystalChime(activity)",BOOT)
        self.assertIn("COLD_ARRIVAL_SOUND_PENDING", BOOT)
        self.assertIn("playPendingColdArrivalIfReady", BOOT)
        self.assertIn("postDelayed(", BOOT)
        self.assertIn("new android.media.AudioTrack.Builder()", BOOT)
        self.assertIn("android.media.AudioTrack.MODE_STATIC", BOOT)
        self.assertIn("activeCrystalAudioTrack = track", BOOT)
        self.assertIn("MediaPlayer.create(activity", BOOT)
        self.assertIn("STARTED: direct PCM crystal sound", BOOT)
        self.assertIn("QUEUED: cold arrival sound waiting", BOOT)
        self.assertIn("charoite_crystal_startup",BOOT)
        self.assertIn("AudioAttributes.USAGE_MEDIA",BOOT)
        self.assertIn("AudioManager.STREAM_MUSIC",BOOT)
        self.assertEqual(audio.DURATION_SECONDS,4.2)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"arrival.wav"
            audio.generate(path)
            with wave.open(str(path),"rb") as sound:
                self.assertEqual(sound.getframerate(),44100)
                self.assertEqual(sound.getnframes(),round(44100*4.2))


if __name__ == "__main__":
    unittest.main()

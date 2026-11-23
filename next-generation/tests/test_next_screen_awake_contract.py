"""Keep-screen-on only for visible Meteorite Alpha activities, never stable Portal."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "CharoiteNextAwakeApplication.java").read_text(encoding="utf-8")
PREP = (ROOT / "prepare_next.py").read_text(encoding="utf-8")


class ScreenAwakeContract(unittest.TestCase):
    def test_next_manifest_installs_application_for_all_activities(self):
        self.assertIn('assert application.get(ns + "name") is None', PREP)
        self.assertIn('application.set(ns + "name", "com.charoitegames.core.CharoiteNextAwakeApplication")', PREP)
        self.assertIn('shutil.copy2(source_dir / "CharoiteNextAwakeApplication.java", awake_java)', PREP)
        self.assertIn('ns + "process": ":wine29_display"', PREP)
        self.assertIn('source_dir / "WineActivity.java"', PREP)

    def test_awake_flag_is_released_when_app_goes_to_background(self):
        self.assertIn('extends Application', APP)
        self.assertIn('registerActivityLifecycleCallbacks(', APP)
        self.assertIn('void onActivityResumed(Activity activity)', APP)
        self.assertIn('window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);', APP)
        self.assertIn('void onActivityPaused(Activity activity)', APP)
        self.assertIn('window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);', APP)
        self.assertLess(APP.index('void onActivityResumed('), APP.index('void onActivityPaused('))

    def test_no_permanent_wake_lock_or_global_device_setting(self):
        for forbidden in (
            'PowerManager.WakeLock', 'acquire(', 'Settings.System',
            'WRITE_SETTINGS', 'KeyguardManager', 'setShowWhenLocked',
            'FLAG_TURN_SCREEN_ON', 'FLAG_DISMISS_KEYGUARD',
            'startForegroundService', 'PARTIAL_WAKE_LOCK)',
        ):
            self.assertNotIn(forbidden, APP)
        self.assertNotIn('android.permission.WAKE_LOCK', PREP)

if __name__ == "__main__":
    unittest.main()

"""Isolated v24 x64 graphics one-shot: consumed v1-v23 remain immutable."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROBE = (ROOT / "next-generation/CharoiteWine29V28FocusedInfProbe.java").read_text(encoding="utf-8")
HOST = (ROOT / "next-generation/WineActivity.java").read_text(encoding="utf-8")
FIXTURE = (ROOT / "next-generation/charoite-wine/fixtures/x64-window.c").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")


class V24DisplayScratch(unittest.TestCase):
    def test_no_consumed_directory_reused(self):
        selection = PROBE.split("String scratchName = prepareWindow ?", 1)[1].split(";", 1)[0]
        self.assertIn('"charoite-next-wine29-x64-window-v24"', selection)
        for version in range(1, 24):
            self.assertNotIn(f'"charoite-next-wine29-x64-window-v{version}"', selection)
        self.assertIn("if (!newScratch.mkdir())", PROBE)
        self.assertIn("One-shot scratch exists or cannot be created", PROBE)
        self.assertNotIn("clearApplicationUserData", PROBE)
        self.assertNotIn(".delete(", PROBE)

    def test_last_log_fallback_is_read_only_and_covers_history(self):
        self.assertIn("for (int version = 24; version >= 1; version--)", HOST)
        self.assertIn('"charoite-next-wine29-x64-window-v" + version + "/x64-window-native.log"', HOST)
        self.assertNotIn("for (int version = 24; version >= 1; version--)", HOST)

    def test_no_success_shortcuts_or_fake_android_pixels(self):
        self.assertIn("if (pixel != paint_color || client_pixel != paint_color || !IsWindowVisible(window))", FIXTURE)
        self.assertIn("ExitProcess(42)", FIXTURE)
        self.assertIn("ExitProcess(code)", FIXTURE)
        for pattern in ("ANativeWindow_lock", "androidSurfaceFill", "0x2003e", "GetPixel ="):
            self.assertNotIn(pattern, FIXTURE)
        self.assertIn("wine29-x64-window.zip", WORKFLOW)
        self.assertIn("x64-window.sha256", WORKFLOW)


if __name__ == "__main__":
    unittest.main()

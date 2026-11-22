"""Source-only guard for Android-side Wine29 frame presentation evidence.

The desktop Wine fixture checks GetPixel(screen DC), which does not by itself
prove an Android TextureView displayed pixels. These tests check the separate
bounded, UI-thread readback contract. They do NOT claim a phone result.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOST = (ROOT / "next-generation/WineActivity.java").read_text(encoding="utf-8")
FIXTURE = (ROOT / "next-generation/charoite-wine/fixtures/x64-window.c").read_text(
    encoding="utf-8"
)


class AndroidFrameProofContract(unittest.TestCase):
    def test_only_a_posted_sized_child_frame_can_pass(self):
        self.assertIn("onSurfaceTextureUpdated(SurfaceTexture texture)", HOST)
        self.assertIn("hwnd == desktopHwnd", HOST)
        self.assertIn("view.getWidth() < 16 || view.getHeight() < 16", HOST)
        self.assertIn("frame = view.getBitmap(64, 64);", HOST)
        self.assertIn("int pixel = frame.getPixel(8, 8) & 0x00ffffff;", HOST)
        for channel in ("- 124) <= 8", "- 64) <= 8", "- 192) <= 8"):
            self.assertIn(channel, HOST)
        self.assertIn("presentedPurpleWindow = true;", HOST)
        self.assertIn("if (frame != null) frame.recycle();", HOST)

    def test_screen_readback_remains_independently_required(self):
        self.assertIn("Win32 screen-DC readback is a separate gate.", HOST)
        self.assertIn("GetPixel(screen, sample.x, sample.y)", FIXTURE)
        self.assertIn("if (pixel != paint_color || !IsWindowVisible(window))", FIXTURE)
        self.assertIn("ExitProcess(15);", FIXTURE)
        self.assertIn("ExitProcess(42);", FIXTURE)

    def test_checkpoint_does_not_capture_frames_or_user_data(self):
        self.assertIn("recordWindowStage(", HOST)
        self.assertIn("if (!sampledWindowFrame)", HOST)
        self.assertIn("catch (RuntimeException failure)", HOST)
        for forbidden in ("bitmap.compress(", "MediaStore.", "getExternalStorageDirectory("):
            self.assertNotIn(forbidden, HOST)


if __name__ == "__main__":
    unittest.main()

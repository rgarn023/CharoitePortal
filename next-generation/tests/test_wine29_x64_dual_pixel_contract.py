"""No-bypass tests for the Wine29 x64 GUI fixture's two pixel readback paths."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "charoite-wine/fixtures/x64-window.c").read_text(encoding="utf-8")
WORKFLOW = (ROOT.parent / ".github/workflows/wine29-x64-window-fixture.yml").read_text(
    encoding="utf-8"
)


class Wine29DualReadback(unittest.TestCase):
    def test_client_and_screen_readback_are_both_required(self):
        self.assertIn("HDC client_dc = GetDC(window);", SOURCE)
        self.assertIn("client_pixel = GetPixel(client_dc, 16, 16);", SOURCE)
        self.assertIn("pixel = GetPixel(screen, sample.x, sample.y);", SOURCE)
        self.assertIn("if (pixel == paint_color && client_pixel == paint_color)", SOURCE)
        self.assertIn("pixel != paint_color || client_pixel != paint_color || !IsWindowVisible(window)", SOURCE)
        self.assertIn("ReleaseDC(window, client_dc);", SOURCE)
        self.assertIn("ReleaseDC(NULL, screen);", SOURCE)
        self.assertIn("ExitProcess(42);", SOURCE)

    def test_failure_codes_keep_client_and_screen_diagnostics_distinct(self):
        self.assertIn("client_pixel == paint_color ? 16", SOURCE)
        self.assertIn("pixel == paint_color ? 17 : 15", SOURCE)
        self.assertIn("ExitProcess(code);", SOURCE)
        self.assertNotIn("ExitProcess(42);\n        }", SOURCE)

    def test_desktop_wine_ci_retains_full_two_pixel_gate(self):
        self.assertIn("wine29-x64-window-fixture", WORKFLOW)
        self.assertIn('if [ "$rc" -ne 42 ]; then', WORKFLOW)
        self.assertIn("x86_64-w64-mingw32-gcc-posix", WORKFLOW)
        self.assertIn("-nostdlib -mwindows -Wl,--entry,fixture_entry", WORKFLOW)


if __name__ == "__main__":
    unittest.main()

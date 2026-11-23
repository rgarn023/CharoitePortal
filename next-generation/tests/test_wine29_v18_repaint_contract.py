"""Source-only contract: bounded direct GDI repaint without a fake graphics pass."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (ROOT / "charoite-wine/fixtures/x64-window.c").read_text(encoding="utf-8")
CI = (ROOT.parent / ".github/workflows/wine29-x64-window-fixture.yml").read_text(encoding="utf-8")


class DirectGdiPaintRecovery(unittest.TestCase):
    def test_bounded_repaint_stays_on_windows_gdi(self):
        self.assertIn("static void repaint_client_dc(HWND window)", FIXTURE)
        self.assertIn("HDC dc = GetDC(window);", FIXTURE)
        self.assertIn("GetClientRect(window, &client)", FIXTURE)
        self.assertIn("FillRect(dc, &client, brush);", FIXTURE)
        self.assertIn("ReleaseDC(window, dc);", FIXTURE)
        self.assertIn("if (attempt == 0 || attempt == 20 || attempt == 60)", FIXTURE)
        self.assertIn("repaint_client_dc(window);", FIXTURE)
        self.assertIn("InvalidateRect(window, NULL, FALSE);", FIXTURE)
        self.assertIn("UpdateWindow(window);", FIXTURE)

    def test_real_client_and_screen_pixel_proof_remains_required(self):
        self.assertIn("client_pixel = GetPixel(client_dc, 16, 16);", FIXTURE)
        self.assertIn("pixel = GetPixel(screen, sample.x, sample.y);", FIXTURE)
        self.assertIn("if (pixel == paint_color && client_pixel == paint_color)", FIXTURE)
        self.assertIn("pixel != paint_color || client_pixel != paint_color || !IsWindowVisible(window)", FIXTURE)
        self.assertIn("client_pixel == paint_color ? 16", FIXTURE)
        self.assertIn("pixel == paint_color ? 17 : 15", FIXTURE)
        self.assertIn("ExitProcess(42);", FIXTURE)
        self.assertIn('if [ "$rc" -ne 42 ]; then', CI)

    def test_no_android_surface_shortcut_or_unbounded_retry(self):
        self.assertIn("for (unsigned attempt = 0; attempt < 100; ++attempt)", FIXTURE)
        for prohibited in ("ANativeWindow", "android_surface", "ExitProcess(42);\n        }"):
            self.assertNotIn(prohibited, FIXTURE)


if __name__ == "__main__":
    unittest.main()

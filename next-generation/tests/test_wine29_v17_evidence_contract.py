"""Source-only contracts for bounded Android frame evidence and v19 native repaint integration."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOST = (ROOT / "WineActivity.java").read_text(encoding="utf-8")
PROBE = (ROOT / "CharoiteWine29V28FocusedInfProbe.java").read_text(encoding="utf-8")
FIXTURE = (ROOT / "charoite-wine/fixtures/x64-window.c").read_text(
    encoding="utf-8"
)
WORKFLOW = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(
    encoding="utf-8"
)


class V18DisplayEvidence(unittest.TestCase):
    def test_frame_checkpoint_persists_bounded_sequence_on_process_exit(self):
        self.assertIn("windowStageHistory = new java.util.ArrayDeque<>();", HOST)
        self.assertIn("if (windowStageHistory.size() == 20) windowStageHistory.removeFirst();", HOST)
        self.assertIn("for (String event : windowStageHistory)", HOST)
        self.assertIn("record(this, history.toString());", HOST)
        self.assertIn("Android texture available hwnd ", HOST)
        self.assertIn("Android child texture size ", HOST)
        self.assertIn("Android window drawable and visible, hwnd ", HOST)
        self.assertIn("onSurfaceTextureUpdated(SurfaceTexture texture)", HOST)
        self.assertIn("Android presentation VERIFIED:", HOST)

    def test_exit_codes_distinguish_readback_without_claiming_android(self):
        self.assertIn("case 15: return report", HOST)
        self.assertIn("case 16: return report", HOST)
        self.assertIn("case 17: return report", HOST)
        self.assertIn("case 42: return report", HOST)
        self.assertIn("Android visible frame still separate.", HOST)
        self.assertIn("client_pixel = GetPixel(client_dc, 16, 16)", FIXTURE)
        self.assertIn("pixel = GetPixel(screen, sample.x, sample.y)", FIXTURE)
        self.assertIn("if (pixel == paint_color && client_pixel == paint_color)", FIXTURE)

    def test_v19_private_one_shot_and_last_log_fallback(self):
        self.assertIn('prepareWindow ? "charoite-next-wine29-x64-window-v21"', PROBE)
        self.assertIn("if (!newScratch.mkdir())", PROBE)
        self.assertIn("for (int version = 21; version >= 1; version--)", HOST)
        self.assertIn("new java.io.RandomAccessFile(log, \"r\")", HOST)
        self.assertIn("Math.min(size, 16384L)", HOST)

    def test_desktop_verified_fixture_zip_and_inner_pe_are_pinned(self):
        # The artifact is from strict desktop Wine fixture run 45095286821 (SUCCESS).
        self.assertIn("actions/artifacts/14782543540/zip", WORKFLOW)
        self.assertIn("05f4d80c56312ef9fdd567cce61c3c939e21b047a5bf9a3ec469c6c6545e08c8", WORKFLOW)
        self.assertIn("80c1df49ed02b61aa4bf479b7fc6805a258a24e1559cf7e0408a19c1a72eb670", WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c x64-window.sha256)', WORKFLOW)
        self.assertNotIn("actions/artifacts/14756991971/zip", WORKFLOW)

    def test_no_screenshots_or_game_data_stored_in_checkpoint(self):
        segment = HOST.split("private synchronized void recordWindowStage(", 1)[1].split(
            "public void createWindow(", 1)[0]
        self.assertNotIn("getBitmap(", segment)
        self.assertNotIn("getExternalFilesDir(", segment)
        self.assertNotIn("compress(", segment)
        self.assertNotIn("PowerManager.WakeLock", HOST)


if __name__ == "__main__":
    unittest.main()

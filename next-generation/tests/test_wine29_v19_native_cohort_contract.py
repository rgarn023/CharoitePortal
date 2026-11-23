"""Source-only current v21 native WineAndroid provider provenance and isolation tests."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
PROBE = (ROOT / "next-generation/CharoiteWine29V28FocusedInfProbe.java").read_text(
    encoding="utf-8"
)
HOST = (ROOT / "next-generation/WineActivity.java").read_text(encoding="utf-8")

class NativeCohortV21(unittest.TestCase):
    def test_new_java_host_and_explorer_from_one_successful_provider(self):
        self.assertIn("actions/artifacts/14830427285/zip", WORKFLOW)
        self.assertIn("3a4ac7e4c397bbc227f7fd3fa3d83654c2a1f725aedb8fdb7288b9b79addded5", WORKFLOW)
        self.assertIn("actions/artifacts/14830162796/zip", WORKFLOW)
        self.assertIn("74f58c19fef20a8c2eddae8540751bcd82d2e376935e7efec9c5b8573406a087", WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c SHA256SUMS)', WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c explorer.sha256)', WORKFLOW)

    def test_native_driver_is_byte_identical_to_host_cohort(self):
        self.assertIn("actions/artifacts/14830207787/zip", WORKFLOW)
        self.assertIn("b41ea09ce24ce642305d2e59e9466955e21177b988017292c2ebee8c5afa9564", WORKFLOW)
        self.assertIn("for file in win32u.dll win32u.so wineandroid.drv wineandroid.so; do", WORKFLOW)
        self.assertIn('unzip -p "$display" "$file" | cmp - "$assets/$file"', WORKFLOW)
        self.assertIn("WINE29_V21_NATIVE_HOST_DISPLAY_COHORT=MATCH", WORKFLOW)
        for stale in (
            "actions/artifacts/14778917103/zip",
            "actions/artifacts/14779061741/zip",
        ):
            self.assertNotIn(stale, WORKFLOW)

    def test_one_shot_only_new_private_v21_and_strict_wine_gate(self):
        self.assertIn('prepareWindow ? "charoite-next-wine29-x64-window-v21"', PROBE)
        self.assertIn("if (!newScratch.mkdir())", PROBE)
        self.assertIn("for (int version = 21; version >= 1; version--)", HOST)
        self.assertIn("actions/artifacts/14782543540/zip", WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c x64-window.sha256)', WORKFLOW)
        self.assertNotIn('adb install', WORKFLOW)

if __name__ == "__main__":
    unittest.main()

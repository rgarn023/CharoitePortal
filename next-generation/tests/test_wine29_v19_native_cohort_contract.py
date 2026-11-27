"""Source-only current v26 native WineAndroid provider provenance and isolation tests."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
PROBE = (ROOT / "next-generation/CharoiteWine29V28FocusedInfProbe.java").read_text(
    encoding="utf-8"
)
HOST = (ROOT / "next-generation/WineActivity.java").read_text(encoding="utf-8")

class NativeCohortV26(unittest.TestCase):
    def test_new_java_host_and_explorer_from_one_successful_provider(self):
        self.assertIn("actions/artifacts/15169674395/zip", WORKFLOW)
        self.assertIn("583b8886046a3f2dc9abcc7e42a6ffe968f653122199bb5d9f566af310798f87", WORKFLOW)
        self.assertIn("actions/artifacts/15170283267/zip", WORKFLOW)
        self.assertIn("45f2fcb790cf629389540841e6bb49fbaf2349a8d88b29d09e56594129dd5ddf", WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c SHA256SUMS)', WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c explorer.sha256)', WORKFLOW)

    def test_native_driver_is_byte_identical_to_host_cohort(self):
        self.assertIn("actions/artifacts/15169729236/zip", WORKFLOW)
        self.assertIn("94ccf44a8d605c5c9139b4b694aed08f40d0155e6b53acc3ecdc90da9b73caaa", WORKFLOW)
        self.assertIn("for file in win32u.dll win32u.so wineandroid.drv wineandroid.so; do", WORKFLOW)
        self.assertIn('unzip -p "$display" "$file" | cmp - "$assets/$file"', WORKFLOW)
        self.assertIn("WINE29_V26_NATIVE_HOST_DISPLAY_COHORT=MATCH", WORKFLOW)
        for stale in (
            "actions/artifacts/14778917103/zip",
            "actions/artifacts/14779061741/zip",
        ):
            self.assertNotIn(stale, WORKFLOW)

    def test_one_shot_only_new_private_v26_and_strict_wine_gate(self):
        self.assertIn('prepareWindow ? "charoite-next-wine29-x64-window-v26"', PROBE)
        self.assertIn("if (!newScratch.mkdir())", PROBE)
        self.assertIn("for (int version = 26; version >= 1; version--)", HOST)
        self.assertIn("actions/artifacts/14782543540/zip", WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c x64-window.sha256)', WORKFLOW)
        self.assertNotIn('adb install', WORKFLOW)

if __name__ == "__main__":
    unittest.main()

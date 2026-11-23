"""Source-only current v22 native WineAndroid provider provenance and isolation tests."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
PROBE = (ROOT / "next-generation/CharoiteWine29V28FocusedInfProbe.java").read_text(
    encoding="utf-8"
)
HOST = (ROOT / "next-generation/WineActivity.java").read_text(encoding="utf-8")

class NativeCohortV22(unittest.TestCase):
    def test_new_java_host_and_explorer_from_one_successful_provider(self):
        self.assertIn("actions/artifacts/14838255023/zip", WORKFLOW)
        self.assertIn("7d871248c53a610ba27fbc9e252a3af25d5877febbc5d4878db798ba16f7ba00", WORKFLOW)
        self.assertIn("actions/artifacts/14836598137/zip", WORKFLOW)
        self.assertIn("e41ef0bb37b32f2b89c66f7ae0d8fe732fc0568b9c5b390a17e4c4883ff0bf57", WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c SHA256SUMS)', WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c explorer.sha256)', WORKFLOW)

    def test_native_driver_is_byte_identical_to_host_cohort(self):
        self.assertIn("actions/artifacts/14836507866/zip", WORKFLOW)
        self.assertIn("0912eaf81f3c6e574b5f5bb0a0d1c9783956dc7dab3b14c00dae563bca88717b", WORKFLOW)
        self.assertIn("for file in win32u.dll win32u.so wineandroid.drv wineandroid.so; do", WORKFLOW)
        self.assertIn('unzip -p "$display" "$file" | cmp - "$assets/$file"', WORKFLOW)
        self.assertIn("WINE29_V22_NATIVE_HOST_DISPLAY_COHORT=MATCH", WORKFLOW)
        for stale in (
            "actions/artifacts/14778917103/zip",
            "actions/artifacts/14779061741/zip",
        ):
            self.assertNotIn(stale, WORKFLOW)

    def test_one_shot_only_new_private_v22_and_strict_wine_gate(self):
        self.assertIn('prepareWindow ? "charoite-next-wine29-x64-window-v22"', PROBE)
        self.assertIn("if (!newScratch.mkdir())", PROBE)
        self.assertIn("for (int version = 22; version >= 1; version--)", HOST)
        self.assertIn("actions/artifacts/14782543540/zip", WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c x64-window.sha256)', WORKFLOW)
        self.assertNotIn('adb install', WORKFLOW)

if __name__ == "__main__":
    unittest.main()

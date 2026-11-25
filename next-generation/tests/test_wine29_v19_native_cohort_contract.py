"""Source-only current v24 native WineAndroid provider provenance and isolation tests."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
PROBE = (ROOT / "next-generation/CharoiteWine29V28FocusedInfProbe.java").read_text(
    encoding="utf-8"
)
HOST = (ROOT / "next-generation/WineActivity.java").read_text(encoding="utf-8")

class NativeCohortV24(unittest.TestCase):
    def test_new_java_host_and_explorer_from_one_successful_provider(self):
        self.assertIn("actions/artifacts/14965418391/zip", WORKFLOW)
        self.assertIn("8be85d8443655c1428f6003ef9c7cc73352cd1e89147d732cab3ce22bfa470f0", WORKFLOW)
        self.assertIn("actions/artifacts/14965827499/zip", WORKFLOW)
        self.assertIn("6bbf702751b55e09be20bce38a769e42539a2abf28c265e144eaaa0d683a5acb", WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c SHA256SUMS)', WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c explorer.sha256)', WORKFLOW)

    def test_native_driver_is_byte_identical_to_host_cohort(self):
        self.assertIn("actions/artifacts/14965018928/zip", WORKFLOW)
        self.assertIn("741f218746a17730d450761737a1eea625bfc400dae49ae7cebd6c7a3a2a870d", WORKFLOW)
        self.assertIn("for file in win32u.dll win32u.so wineandroid.drv wineandroid.so; do", WORKFLOW)
        self.assertIn('unzip -p "$display" "$file" | cmp - "$assets/$file"', WORKFLOW)
        self.assertIn("WINE29_V24_NATIVE_HOST_DISPLAY_COHORT=MATCH", WORKFLOW)
        for stale in (
            "actions/artifacts/14778917103/zip",
            "actions/artifacts/14779061741/zip",
        ):
            self.assertNotIn(stale, WORKFLOW)

    def test_one_shot_only_new_private_v24_and_strict_wine_gate(self):
        self.assertIn('prepareWindow ? "charoite-next-wine29-x64-window-v24"', PROBE)
        self.assertIn("if (!newScratch.mkdir())", PROBE)
        self.assertIn("for (int version = 24; version >= 1; version--)", HOST)
        self.assertIn("actions/artifacts/14782543540/zip", WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c x64-window.sha256)', WORKFLOW)
        self.assertNotIn('adb install', WORKFLOW)

if __name__ == "__main__":
    unittest.main()

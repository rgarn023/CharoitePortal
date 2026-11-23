"""Source-only current v20 native WineAndroid provider provenance and isolation tests."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
PROBE = (ROOT / "next-generation/CharoiteWine29V28FocusedInfProbe.java").read_text(
    encoding="utf-8"
)
HOST = (ROOT / "next-generation/WineActivity.java").read_text(encoding="utf-8")

class NativeCohortV20(unittest.TestCase):
    def test_new_java_host_and_explorer_from_one_successful_provider(self):
        self.assertIn("actions/artifacts/14789922623/zip", WORKFLOW)
        self.assertIn("b2d8efaad39038b253f349c22b23c4f243b299a313a77c1db79ca3f6fa1044c1", WORKFLOW)
        self.assertIn("actions/artifacts/14790167079/zip", WORKFLOW)
        self.assertIn("974df7a059a8945315f438c26795f69e7d600c79265dc7c8371477afb55fb02e", WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c SHA256SUMS)', WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c explorer.sha256)', WORKFLOW)

    def test_native_driver_is_byte_identical_to_host_cohort(self):
        self.assertIn("actions/artifacts/14789992572/zip", WORKFLOW)
        self.assertIn("b3af3ca1332569549001e5ad0a2bf5bfc21cb2c43175d8228ce73c76ab08f258", WORKFLOW)
        self.assertIn("for file in win32u.dll win32u.so wineandroid.drv wineandroid.so; do", WORKFLOW)
        self.assertIn('unzip -p "$display" "$file" | cmp - "$assets/$file"', WORKFLOW)
        self.assertIn("WINE29_V20_NATIVE_HOST_DISPLAY_COHORT=MATCH", WORKFLOW)
        for stale in (
            "actions/artifacts/14778917103/zip",
            "actions/artifacts/14779061741/zip",
        ):
            self.assertNotIn(stale, WORKFLOW)

    def test_one_shot_only_new_private_v20_and_strict_wine_gate(self):
        self.assertIn('prepareWindow ? "charoite-next-wine29-x64-window-v20"', PROBE)
        self.assertIn("if (!newScratch.mkdir())", PROBE)
        self.assertIn("for (int version = 20; version >= 1; version--)", HOST)
        self.assertIn("actions/artifacts/14782543540/zip", WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c x64-window.sha256)', WORKFLOW)
        self.assertNotIn('adb install', WORKFLOW)

if __name__ == "__main__":
    unittest.main()

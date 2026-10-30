"""Fail-closed Charoite Wine / Proton lineage and integration scope tests.

No checkout, Android private storage, prefix or Windows process is required.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FORK = ROOT / "charoite-wine"
PREP = (FORK / "prepare-source.sh").read_text(encoding="utf-8")
SERIES = (FORK / "patches/SERIES").read_text(encoding="utf-8")
DOC = (FORK / "PROTON_INTEGRATION_AUDIT.md").read_text(encoding="utf-8")
STAGER = (ROOT / "stage_native_wine_loader.py").read_text(encoding="utf-8")
SERVER = (ROOT / "CharoiteWineServerProbe.java").read_text(encoding="utf-8")


class ProtonIntegrationAuditTest(unittest.TestCase):
    def test_exact_pinned_proton_wine_lineage(self):
        self.assertIn("The412Banner/proton-wine.git", PREP)
        self.assertIn("c74acb09d51b447f5d5ac56c87608d3ec565a767", PREP)
        self.assertIn("git checkout --detach", PREP)
        self.assertIn("android/patches/$rel", PREP)
        self.assertIn("apply-ge-patches.sh", PREP)
        self.assertIn("GE-Proton", DOC)
        self.assertIn("ge-video-rework", DOC)
        self.assertIn("not Wine authored from scratch", DOC)

    def test_charoite_patch_count_and_source_guardrails(self):
        patches = [line.strip() for line in SERIES.splitlines()
                   if line.strip() and not line.lstrip().startswith("#")]
        self.assertEqual(len(patches), 9)
        self.assertEqual(len(set(patches)), 9)
        self.assertTrue(all((FORK / "patches" / name).is_file() for name in patches))
        for needle in ("0700-android-apk-native-ntdll-path.patch",
                       "0400-arm64ec-atomic-operations.patch",
                       "0200-android-machine-id-fallback.patch"):
            self.assertIn(needle, patches)
        self.assertIn('[[ "$count" -eq 9 ]]', PREP)
        self.assertIn("git apply --check", PREP)
        self.assertIn("git diff --check", PREP)

    def test_future_components_not_claimed_runnable(self):
        for name in ("FEX", "DXVK", "VKD3D-Proton", "Mesa/Turnip",
                     "wineserver", "wineboot", "22-component", "76-NLS"):
            self.assertIn(name, DOC)
        self.assertIn("launch_ready", STAGER)
        self.assertIn('"wineserver_device_tested":False', STAGER)
        self.assertIn('"prefix_created":False', STAGER)
        self.assertIn("Wineserver session: NOT STARTED", SERVER)
        self.assertIn("Wine prefix/wineboot: NOT ATTEMPTED", SERVER)
        self.assertNotIn("new File(context.getFilesDir()", SERVER)
        self.assertNotIn("clearApplicationUserData", SERVER)


if __name__ == "__main__":
    unittest.main()

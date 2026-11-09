"""Source-only V23 Wine29 prefix setup candidates; never execute Windows PE."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = (ROOT.parent / ".github/workflows/wine29-v23-prefix-setup-candidate.yml").read_text(encoding="utf-8")
DOC = (ROOT.parent / "docs/WINE29_V23_PREFIX_SETUP_SOURCE_CANDIDATE.md").read_text(encoding="utf-8")

class V23PrefixSetupSourceContract(unittest.TestCase):
    def test_pinned_source_and_isolated_build(self):
        for literal in (
            "c74acb09d51b447f5d5ac56c87608d3ec565a767",
            "41947164001",
            "ada8bd980722deba16e89231652a25a27a7e197a7638abc9d38a61e0614e412e",
            "next-generation/charoite-wine/prepare-source.sh",
            "analysis/wine29_bootstrap/patch_v6_child_loader.py",
            "programs/rundll32/aarch64-windows/rundll32.exe",
            "programs/rpcss/aarch64-windows/rpcss.exe",
            "loader/wine.inf",
            "DefaultInstall.ntarm64.Services",
            "AddService=RpcSs",
            "kernelbase.dll", "rpcrt4.dll",
            "wine_executed", "device_tested", "launch_ready",
        ):
            with self.subTest(literal=literal):
                self.assertIn(literal, WF)
    def test_no_phone_or_apk_steps(self):
        self.assertNotIn("assembleDebug", WF)
        self.assertNotIn("adb shell", WF)
        self.assertNotIn("wineboot -i", WF)
        self.assertNotIn("install APK", WF)
        self.assertIn("Wine29-V23-Pinned-Prefix-Setup-Source-Only-NOT-APK", WF)
        self.assertIn("rundll32.exe", DOC)
        self.assertIn("WINEDATADIR", DOC)
        self.assertIn("NOT an APK", DOC)
        self.assertIn("V22 permanently consumed", DOC)

if __name__ == "__main__":
    unittest.main()

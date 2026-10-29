"""Fail-closed Android diagnostic APK asset/staging contracts."""
import ast
import json
import tempfile
import unittest
from pathlib import Path
import sys
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
STAGER=ROOT/"stage_wine_probe.py"
SCRIPT=STAGER.read_text(encoding="utf-8")
JAVA=(ROOT/"CharoiteNextDiagnostics.java").read_text(encoding="utf-8")
PREP=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WORKFLOW=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class DeviceProbeContract(unittest.TestCase):
    def test_exact_verified_wine_provenance(self):
        self.assertIn("40791083178",SCRIPT)
        self.assertIn("c1658e2d20260ff413e6ba6c47f460e2d5e7cec1",SCRIPT)
        self.assertIn("1a795a07b9a803c66e8ccba47d20b70ab97e54741e24376cb863a9ba0fb3b33d",SCRIPT)
        self.assertIn("verify-pe-foundation.py",SCRIPT)
        self.assertIn("verify-pe-expansion.py",SCRIPT)

    def test_verifier_is_non_destructive(self):
        for bad in ("adb install","rm -rf","WINEPREFIX=","deleteRecursively","ProcessBuilder"):
            self.assertNotIn(bad,SCRIPT+JAVA+PREP)
        self.assertIn("Refusing to overwrite",SCRIPT)
        self.assertIn("launch_ready",SCRIPT)
        self.assertIn('"installable_as_runtime": False',SCRIPT)

    def test_android_probe_checks_real_os_and_asset_hashes(self):
        for phrase in ("Os.sysconf(OsConstants._SC_PAGESIZE)",
                       "android.hardware.vulkan.version","getUsableSpace()",
                       "MessageDigest.getInstance(\"SHA-256\")",
                       "PE_ARM64_CARRIER", "7", "MODERN ENGINE: NOT READY"):
            self.assertIn(phrase,JAVA)

    def test_diagnostic_is_user_initiated(self):
        self.assertIn("Run Core Next device diagnostics",PREP)
        self.assertIn("CharoiteNextDiagnostics.deviceReport(this)",PREP)
        self.assertIn("Copy report",PREP)
        self.assertNotIn("Runtime.getRuntime().exec",JAVA)
        self.assertNotIn("loadLibrary",JAVA)
        self.assertNotIn("startActivity",JAVA)

    def test_ci_fetches_pinned_artifacts_not_a_latest_mutable_run(self):
        self.assertIn("12861682823",WORKFLOW)
        self.assertIn("12861074729",WORKFLOW)
        self.assertIn("GH_TOKEN",WORKFLOW)
        self.assertIn("stage_wine_probe.py",WORKFLOW)
        self.assertIn("wine-ci-evidence.json",WORKFLOW)

if __name__=="__main__":unittest.main()

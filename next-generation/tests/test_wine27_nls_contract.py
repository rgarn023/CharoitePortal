"""New isolated patched native Wine cohort: static fail-closed regression contract."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT.parent / ".github/workflows/charoite-next.yml"
STAGE = (ROOT / "stage_wine27.py").read_text()
NATIVE = (ROOT / "stage_wine27_native.py").read_text()
DATA = (ROOT / "CharoiteWine27Stage.java").read_text()
GATE = (ROOT / "CharoiteWine27NativeGate.java").read_text()
PREFIX = (ROOT / "CharoiteWine27PrefixProbe.java").read_text()
PREP = (ROOT / "prepare_next.py").read_text()
CI = WORKFLOW.read_text()


class Wine27IsolatedNlsContract(unittest.TestCase):
    def test_pinned_verified_new_source_and_identity(self):
        for src in (STAGE, NATIVE, DATA, GATE):
            self.assertIn("41130899651", src)
            self.assertIn("13012239618", src)
            self.assertIn("c74acb09d51b447f5d5ac56c87608d3ec565a767", src)
        for src in (STAGE, NATIVE):
            self.assertIn("wine-bootstrap-27", src)
        self.assertIn("source/charoite-source-delta.patch", STAGE)
        self.assertIn("CHAROITE_WINE27_NATIVE_DIR", STAGE)
        self.assertIn("CHAROITE_WINE26_DATA_DIR", STAGE)
        self.assertIn("CHAROITE_WINE27_NATIVE_DIR", NATIVE)
        self.assertIn("CHAROITE_WINE26_DATA_DIR", NATIVE)
        self.assertIn("wine10-arm64ec-bootstrap-0.6-staged", DATA)
        self.assertIn("wine10-arm64ec-bootstrap-0.6-staged", GATE)

    def test_fresh_v3_scratch_and_no_legacy_data_modification(self):
        self.assertIn('charoite-next-wine27-first-prefix-v3', PREFIX)
        self.assertNotIn('charoite-next-wine26-first-prefix-v2"', PREFIX)
        self.assertIn('CharoiteWine27NativeGate.run(context)', PREFIX)
        self.assertIn('CharoiteWine27Stage.verifyOnly(context)', GATE)
        self.assertIn('CHAROITE_WINE27_NATIVE_DIR', PREFIX)
        self.assertIn('CHAROITE_WINE26_DATA_DIR', PREFIX)
        self.assertIn('nls/locale.nls', PREFIX)
        self.assertIn('nls/l_intl.nls', PREFIX)
        self.assertIn('WINELOADERNOEXEC', PREFIX)
        self.assertIn('scratch.exists() || !scratch.mkdir()', PREFIX)
        self.assertIn('TIMEOUT = 25L', PREFIX)
        self.assertIn('Existing Wine22', PREFIX)
        self.assertNotIn('env.put("CHAROITE_NTDLL_NATIVE_DIR"', PREFIX)
        self.assertNotIn("rm -rf", PREFIX)
        self.assertNotIn(".delete(", PREFIX)

    def test_next_package_and_source_only_gate(self):
        self.assertIn('versionName "11.2-next.0.56"', PREP)
        self.assertIn('versionCode 87', PREP)
        self.assertIn("CharoiteWine27Stage.java", PREP)
        self.assertIn("CharoiteWine27NativeGate.java", PREP)
        self.assertIn("CharoiteWine27PrefixProbe.java", PREP)
        self.assertIn('Run one-time v3 Wineboot probe', PREP)
        self.assertIn("41130899651", CI)
        self.assertIn("next-generation/stage_wine27.py", CI)
        self.assertIn("next-generation/stage_wine27_native.py", CI)
        self.assertIn("CHAROITE_NEXT_WINE27_PATCHED_SOURCE_APK_HASHES_VERIFIED", CI)
        self.assertIn("wine-bootstrap-26.bundle", CI)  # unchanged old slot
        self.assertIn("wine-bootstrap-27.bundle", CI)  # new source cohort

    def test_native_versions_are_not_game_claims(self):
        for src in (STAGE, NATIVE, GATE):
            self.assertIn("launch_ready", src)
        self.assertIn('"anti_cheat_supported":False', STAGE)
        self.assertIn('wine27-native-probe.json', NATIVE)


if __name__ == "__main__":
    unittest.main()

"""Pinned independent Wine28 0.7 APK cohort and one-shot v5 prefix contract."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
DATA=(ROOT/"stage_wine28.py").read_text()
NATIVE=(ROOT/"stage_wine28_native.py").read_text()
STAGE=(ROOT/"CharoiteWine28Stage.java").read_text()
GATE=(ROOT/"CharoiteWine28NativeGate.java").read_text()
V5=(ROOT/"CharoiteWine28V5Trace.java").read_text()
PREP=(ROOT/"prepare_next.py").read_text()
WORKFLOW=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()

class Wine28IsolatedV5(unittest.TestCase):
    def test_pinned_new_source_and_nonoverwriting_generation(self):
        for s in (DATA,NATIVE,STAGE,GATE):
            self.assertIn("41144679591",s)
            self.assertIn("13019349525",s)
            self.assertIn("c74acb09d51b447f5d5ac56c87608d3ec565a767",s)
        for s in (DATA,NATIVE):
            self.assertIn("wine-bootstrap-28",s)
        self.assertIn("wine-bootstrap-27.bundle",DATA)
        self.assertIn("CHAROITE_WINE28_PE_DIR",DATA)
        self.assertIn("CHAROITE_WINE28_NATIVE_DIR",DATA)
        self.assertIn("libcharoite_wine28_ntdll.so",NATIVE)
        self.assertIn("CHAROITE_WINE28_PE_DIR",NATIVE)
        self.assertIn("wine10-arm64ec-bootstrap-0.7-staged",STAGE)
        self.assertIn("wine10-arm64ec-bootstrap-0.7-staged",GATE)
        self.assertIn("CharoiteWine28Stage.verifyOnly(context)",GATE)
        self.assertIn("wine28-native-probe.json",NATIVE)

    def test_exact_fresh_v5_and_no_old_scratch_access(self):
        for needle in ("charoite-next-wine28-first-prefix-v5-ntdll-fix",
            "CharoiteWine28NativeGate.run(context)",
            "scratch.exists() || !scratch.mkdir()",
            "CHAROITE_WINE28_PE_DIR","CHAROITE_WINE28_NATIVE_DIR",
            "CHAROITE_WINE26_DATA_DIR","WINELOADERNOEXEC",
            "getNoBackupFilesDir()","MAX_LOG = 8L","TIMEOUT = 25L",
            "waitFor(200,TimeUnit.MILLISECONDS)","peNtdll.isFile()",
            "copyVerified(origin,destination","v1/v2/v3/v4 scratches: NOT ACCESSED"):
            self.assertIn(needle,V5)
        for bad in ('first-prefix-v4-trace"',".delete(","rm -rf",
                    "clearApplicationUserData","com.touhoudr"):
            self.assertNotIn(bad,V5)

    def test_user_consent_and_apk_source_hash_verification(self):
        for needle in ("Stage source-patched Wine28 modules",
             "Verify matched Wine28 native cohort",
             "Test new v5 Wine28 PE-NTDLL bootstrap",
             "Run ONE Wine28 v5 bootstrap",
             "CharoiteWine28V5Trace.run(this)",
             "versionCode 84","11.2-next.0.53"):
            self.assertIn(needle,PREP)
        for needle in ("41144679591","13019349525","stage_wine28.py",
             "stage_wine28_native.py",
             "WINE28_MATCHED_SOURCE_PE_NATIVE_APK_HASHES_VERIFIED",
             "libcharoite_wine28_ntdll.so","wine-bootstrap-27.bundle",
             "wine-bootstrap-28.bundle"):
            self.assertIn(needle,WORKFLOW)
        self.assertIn("versionCode='84' versionName='11.2-next.0.53'",WORKFLOW)

if __name__=="__main__":
    unittest.main()

"""Fresh v4 Wineboot explicitly consented and trace-bounded, never v3 reuse."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
V4=(ROOT/"CharoiteWine27V4Trace.java").read_text()
V3=(ROOT/"CharoiteWine27PrefixProbe.java").read_text()
PREP=(ROOT/"prepare_next.py").read_text()
WORKFLOW=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
class Wine27V4TraceContract(unittest.TestCase):
    def test_fresh_no_backup_scratch_fail_closed(self):
        for marker in ("charoite-next-wine27-first-prefix-v4-trace",
                       "CharoiteWine27NativeGate.run(context)",
                       "scratch.exists() || !scratch.mkdir()",
                       "copyVerified(origin,destination",
                       "getNoBackupFilesDir()",
                       "env.clear()", "WINEPREFIX",
                       "CHAROITE_WINE27_NATIVE_DIR",
                       "CHAROITE_WINE26_DATA_DIR",
                       "WINELOADERNOEXEC", "WINEDLLPATH",
                       "TIMEOUT = 25L", "MAX_LOG = 8L",
                       "log.length()>MAX_LOG","waitFor(200,TimeUnit.MILLISECONDS)",
                       "V4 trace channels:", "boundedLog(log)",
                       "Earlier failed Wine v1/v2/v3 scratches: NOT ACCESSED"):
            self.assertIn(marker,V4)
        self.assertNotIn('charoite-next-wine27-first-prefix-v3"',V4)
        self.assertIn('charoite-next-wine27-first-prefix-v3', V3)
        for bad in (".delete(", "clearApplicationUserData", "rm -rf",
                    "new File(context.getFilesDir()", "com.touhoudr"):
            self.assertNotIn(bad,V4)
    def test_explicit_opt_in_and_incremented_apk(self):
        self.assertIn('Test new v4 isolated traced Wineboot',PREP)
        self.assertIn('Run ONE v4 traced Wineboot',PREP)
        self.assertIn('CharoiteWine27V4Trace.run(this)',PREP)
        self.assertIn('CharoiteWine27V4Trace.java',PREP)
        self.assertIn('CharoiteWine27V4Trace.java',WORKFLOW)
        self.assertIn('versionCode 78',PREP)
        self.assertIn('11.2-next.0.47',PREP)
        self.assertIn("versionCode='78' versionName='11.2-next.0.47'",WORKFLOW)
if __name__=="__main__":
    unittest.main()

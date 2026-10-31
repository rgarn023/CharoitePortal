"""Read-only postmortem contract for already-used Wine28 v5 scratch."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
V5=(ROOT/"CharoiteWine28V5Trace.java").read_text()
F=(ROOT/"CharoiteWine28V5Forensics.java").read_text()
UI=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
class Wine28V5ReadOnlyForensics(unittest.TestCase):
    def test_exact_isolated_retained_v5(self):
        for s in ("getNoBackupFilesDir()",
                  "charoite-next-wine28-first-prefix-v5-ntdll-fix",
                  "prefix/system.reg","prefix/user.reg",
                  "prefix/.wineserver","prefix/drive_c",
                  "wineboot.log","wineserver-stop.log",
                  "nls/l_intl.nls","nls/locale.nls",
                  "CharoiteWine27PEAudit.inspect(",
                  "read-only v5 evidence collected"):
            self.assertIn(s,F)
        for forbidden in ("charoite-next-wine27-first-prefix-v4-trace",
                          "charoite-next-wine27-first-prefix-v3",
                          "charoite-next-wine26-first-prefix-v2"):
            self.assertNotIn(forbidden,F)
    def test_no_native_execution_or_mutation(self):
        for forbidden in ("ProcessBuilder","Runtime.getRuntime()","FileOutputStream",
                          ".delete(", ".mkdir(", ".mkdirs(",
                          "clearApplicationUserData","getFilesDir()","com.touhoudr"):
            self.assertNotIn(forbidden,F)
        self.assertIn('new RandomAccessFile(file, "r")',F)
        self.assertIn("getCanonicalFile().equals(scratch.getAbsoluteFile())",F)
        self.assertIn("LOG_LIMIT = 12288",F)
        self.assertIn("scratch.exists() || !scratch.mkdir()",V5)
    def test_ui_and_apk_bundle(self):
        for s in ("CharoiteWine28V5Forensics.java",
                  "Inspect failed Wine28 v5 bootstrap (read-only)",
                  "Inspect v5 without changing files",
                  "CharoiteWine28V5Forensics.run(this)",
                  "versionCode 82","11.2-next.0.51"):
            self.assertIn(s,UI)
        self.assertIn("CharoiteWine28V5Forensics.java CharoiteWine28V6ServerProbe.java CharoiteWine28V7PeHelpProbe.java; do",WF)
        self.assertIn("versionCode='82' versionName='11.2-next.0.51'",WF)
if __name__=="__main__":
    unittest.main()

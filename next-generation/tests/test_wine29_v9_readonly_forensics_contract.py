"""Read-only V9 SCM postmortem may inspect three fixed logs; never execute or touch older state."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V9ReadOnlyForensics.java").read_text()
UI=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()

class Wine29V9PreservedScReadOnly(unittest.TestCase):
    def test_exact_evidence_bounds(self):
        for token in ("charoite-next-wine29-scm-v9","v9-wine-direct-init.log",
            "v9-foreground-wineserver.log","v9-sc-query.log",
            "MAX_SC_LOG = 8L * 1024L * 1024L","MAX_REPORT_CHARS = 9000",
            "MAX_LINES = 100000","MAX_LINE = 16384",
            "getNoBackupFilesDir()","prefix/system.reg","prefix/user.reg",
            "prefix/userdef.reg","runtime/lib/wine/aarch64-windows/sc.exe",
            "native loader/exec failure","DLL load failure","sc.exe PE mapped",
            "First 12 relevant SC event TYPES","END OF SHORT V9 REPORT"):
            with self.subTest(token=token):self.assertIn(token,JAVA)
    def test_never_executes_or_mutates_and_no_raw_log_leak(self):
        for denied in ("new ProcessBuilder(","Runtime.getRuntime(","FileOutputStream",
            "mkdir(","mkdirs(","delete(","renameTo(","createNewFile(","System.load(",
            "clearApplicationUserData(","charoite-next-wine29-userenv-v8",
            "charoite-next-wine29-services-v7","out.append(line)",
            "out.append(peText)","readAllBytes()"):
            with self.subTest(denied=denied):self.assertNotIn(denied,JAVA)
        self.assertIn("no raw log text/paths",JAVA)
        self.assertIn("contents NOT read",JAVA)
    def test_single_current_button_and_ci(self):
        for token in ('"CharoiteWine29V9ReadOnlyForensics.java"',
            "final boolean showArchivedWine29V9Execution = false;",
            "Inspect Wine29 v9 SCM failure (read-only)",
            "CharoiteWine29V9ReadOnlyForensics.run(this)",
            "nextCoreCard.addView(wine29V9Audit);"):
            with self.subTest(token=token):self.assertIn(token,UI)
        self.assertIn("test_wine29_v9_readonly_forensics_contract.py",WF)
        self.assertIn("WINE29_V9_PRESERVED_SC_READONLY_POSTMORTEM=PASS",WF)

if __name__=="__main__":unittest.main()

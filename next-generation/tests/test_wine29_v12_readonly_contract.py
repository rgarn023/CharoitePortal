"""Preserved V12 PE-entry postmortem: strictly read-only with V12 execution retired."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V12ReadOnlyForensics.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")


class V12ReadOnlyContract(unittest.TestCase):
    def test_preserved_three_logs_and_boundaries(self):
        for token in (
            "charoite-next-wine29-entry-v12",
            "v12-wine-direct-init.log", "v12-foreground-wineserver.log",
            "v12-sc-entry.log", "Only THREE V12 logs",
            "getNoBackupFilesDir()", "MAX_PE_LOG", "MAX_SERVER_LOG", "MAX_SC_LOG",
            "MAX_LINES", "MAX_LINE", "MAX_REPORT_CHARS",
            "END OF SHORT V12 READ-ONLY REPORT",
            "Os.lstat(", "Os.readlink(", "contents NOT opened",
            "sc.exe mappings=", "sc.exe mentions=", "PE mapping NOT VERIFIED",
            "READ-ONLY V12 AUDIT COMPLETE",
            "No Windows PE or games executed by this read-only audit.",
        ):
            with self.subTest(token=token):
                self.assertIn(token,JAVA)
        for forbidden in (
            "charoite-next-wine29-entry-v11",
            "charoite-next-wine29-entry-v10", "charoite-next-wine29-scm-v9",
            "new ProcessBuilder(", "Runtime.getRuntime(", "FileOutputStream",
            "FileWriter", ".delete(", ".mkdir(", ".mkdirs(", "renameTo(",
            "clearApplicationUserData(", "System.exit(", "nativeAudit(",
            "NATIVE_SET_LOG", "NATIVE_UNSET_LOG",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,JAVA)

    def test_exit_127_does_not_implicitly_prove_pe_or_scm(self):
        self.assertIn("exit 127",JAVA)
        self.assertIn("No-argument",JAVA) if "No-argument" in JAVA else self.assertIn("Usage or exit status alone",JAVA)
        self.assertIn("SCM/gaming readiness",JAVA)
        self.assertNotIn("RESULT: PASS — sc.exe",JAVA)

    def test_archive_execution_and_wire_only_readonly_audit(self):
        for token in (
            "final boolean showArchivedWine29V11Execution = false;",
            "final boolean showArchivedWine29V11ReadOnly = false;",
            "final boolean showArchivedWine29V12Execution = false;",
            "Inspect Wine29 v12 sc.exe exit (read-only)",
            "CharoiteWine29V12ReadOnlyForensics.run(this)",
            "nextCoreCard.addView(wine29V12Audit);",
            '"CharoiteWine29V12ReadOnlyForensics.java"',
            "versionCode 135", "11.2-next.0.104",
        ):
            self.assertIn(token,UI)
        self.assertIn("test_wine29_v12_readonly_contract.py",WF)
        self.assertIn("WINE29_V12_PRESERVED_SC_ENTRY_READONLY_POSTMORTEM=PASS",WF)
        self.assertIn("cp next-generation/CharoiteWine29V12ReadOnlyForensics.java legal-bundle/CharoiteWine29V12ReadOnlyForensics.java",WF)
        self.assertIn("versionCode='135' versionName='11.2-next.0.104'",WF)


if __name__ == "__main__":
    unittest.main()

"""V13 was executed once. Its next on-phone step must be read-only."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V13ReadOnlyForensics.java").read_text(encoding="utf-8")
UI=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class V13ReadOnlyContract(unittest.TestCase):
    def test_allowlisted_three_v13_logs_bounded_readonly(self):
        for s in (
            "charoite-next-wine29-entry-v13", "v13-wine-direct-init.log",
            "v13-sc-entry.log", "v13-foreground-wineserver.log",
            "Only THREE V13 logs", "no V1–V12",
            "getNoBackupFilesDir()", "MAX_PE_LOG", "MAX_SERVER_LOG",
            "MAX_SC_LOG", "MAX_LINES", "MAX_LINE", "MAX_REPORT_CHARS",
            "END OF SHORT V13 READ-ONLY REPORT", "Os.lstat(", "Os.readlink(",
            "contents NOT opened", "sc.exe mappings=", "sc.exe mentions=",
            "PE mapping NOT VERIFIED", "READ-ONLY V13 AUDIT COMPLETE",
            "No Windows PE or games executed by this read-only audit.",
        ):
            with self.subTest(s=s): self.assertIn(s,JAVA)
        for s in (
            "charoite-next-wine29-entry-v12", "charoite-next-wine29-entry-v11",
            "charoite-next-wine29-entry-v10", "charoite-next-wine29-scm-v9",
            "new ProcessBuilder(", "Runtime.getRuntime(", "FileOutputStream",
            "FileWriter", ".delete(", ".mkdir(", ".mkdirs(", "renameTo(",
            "clearApplicationUserData(", "System.exit(", "nativeAudit(",
            "NATIVE_SET_LOG", "NATIVE_UNSET_LOG",
        ):
            with self.subTest(s=s): self.assertNotIn(s,JAVA)

    def test_exit127_noexec_is_observation_not_scm_proof(self):
        for s in ("exit 127", "NOEXEC unset", "NOEXEC-unset",
                  "SCM/gaming readiness", "Usage or exit status alone"):
            self.assertIn(s,JAVA)
        self.assertNotIn("RESULT: PASS — sc.exe",JAVA)

    def test_previous_execution_archived_only_v13_readonly_visible(self):
        for s in (
            "final boolean showArchivedWine29V12Execution = false;",
            "final boolean showArchivedWine29V12ReadOnly = false;",
            "final boolean showArchivedWine29V13Execution = false;",
            "Inspect Wine29 v13 sc.exe exit (read-only)",
            "CharoiteWine29V13ReadOnlyForensics.run(this)",
            "nextCoreCard.addView(wine29V13Audit);",
            '"CharoiteWine29V13ReadOnlyForensics.java"',
            "versionCode 136","11.2-next.0.105",
        ):
            self.assertIn(s,UI)
        for s in (
            "test_wine29_v13_readonly_contract.py",
            "WINE29_V13_PRESERVED_SC_EXIT127_READONLY_POSTMORTEM=PASS",
            "cp next-generation/CharoiteWine29V13ReadOnlyForensics.java legal-bundle/CharoiteWine29V13ReadOnlyForensics.java",
            "versionCode='136' versionName='11.2-next.0.105'",
        ):
            self.assertIn(s,WF)

if __name__=="__main__":
    unittest.main()

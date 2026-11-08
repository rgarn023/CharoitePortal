"""Preserved V14 sc.exe PE-entry evidence: strictly bounded read-only audit."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V14ReadOnlyForensics.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class V14ReadOnlyContract(unittest.TestCase):
    def test_only_fixed_v14_logs_and_metadata(self):
        for good in (
            "charoite-next-wine29-entry-v14", "v14-wine-direct-init.log",
            "v14-sc-entry.log", "v14-foreground-wineserver.log",
            "Only THREE V14 logs", "no V1–V13",
            "MAX_SC_LOG", "MAX_PE_LOG", "MAX_SERVER_LOG", "MAX_LINES",
            "MAX_LINE", "MAX_REPORT_CHARS", "Os.lstat(", "Os.readlink(",
            "prefix/drive_c/windows/system32/sc.exe", "contents NOT opened",
            "END OF SHORT V14 READ-ONLY REPORT", "PE mapping NOT VERIFIED",
            "READ-ONLY V14 AUDIT COMPLETE",
            "No Windows PE or games executed by this read-only audit.",
        ):
            with self.subTest(good=good): self.assertIn(good, JAVA)
        for bad in (
            "charoite-next-wine29-entry-v13",
            "charoite-next-wine29-entry-v12",
            "charoite-next-wine29-scm-v9",
            "new ProcessBuilder(", "Runtime.getRuntime(", "FileOutputStream",
            "FileWriter", ".delete(", ".mkdir(", ".mkdirs(", "renameTo(",
            "clearApplicationUserData(", "System.exit(",
            "NATIVE_SET_LOG", "NATIVE_UNSET_LOG",
        ):
            with self.subTest(bad=bad): self.assertNotIn(bad, JAVA)

    def test_sc_127_not_claimed_resolved(self):
        for good in ("exit 127", "Windows C: path also did not resolve exit 127",
                     "SCM/gaming readiness", "Usage or exit status alone",
                     "three", "sc.exe mentions="):
            self.assertIn(good,JAVA)
        self.assertNotIn("RESULT: PASS — sc.exe", JAVA)

    def test_old_one_shot_hidden_and_only_v14_audit_active(self):
        for good in (
            'final boolean showArchivedWine29V14Execution = false;',
            'final boolean showArchivedWine29V13ReadOnly = false;',
            'Inspect Wine29 v14 sc.exe exit (read-only)',
            'CharoiteWine29V14ReadOnlyForensics.run(this)',
            'nextCoreCard.addView(wine29V14Audit);',
            '"CharoiteWine29V14ReadOnlyForensics.java"',
            'versionCode 133', '11.2-next.0.102',
        ):
            self.assertIn(good, UI)
        for good in (
            'test_wine29_v14_readonly_contract.py',
            'WINE29_V14_PRESERVED_SC_ENTRY_READONLY_POSTMORTEM=PASS',
            'cp next-generation/CharoiteWine29V14ReadOnlyForensics.java legal-bundle/CharoiteWine29V14ReadOnlyForensics.java',
            "versionCode='133' versionName='11.2-next.0.102'",
        ):
            self.assertIn(good, WF)

if __name__ == "__main__":
    unittest.main()

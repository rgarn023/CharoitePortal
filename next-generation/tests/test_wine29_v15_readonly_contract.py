"""Consumed V15 evidence only: read-only bounded PE-entry/server postmortem."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V15ReadOnlyForensics.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class V15ReadOnlyContract(unittest.TestCase):
    def test_fixed_v15_scope_no_mutation_or_execution(self):
        for good in (
            "charoite-next-wine29-entry-v15", "v15-wine-direct-init.log",
            "v15-sc-entry.log", "v15-foreground-wineserver.log",
            "Only THREE V15 logs", "no V1–V14",
            "MAX_SC_LOG", "MAX_PE_LOG", "MAX_SERVER_LOG",
            "MAX_LINES", "MAX_LINE", "MAX_REPORT_CHARS",
            "Os.lstat(", "Os.readlink(", "prefix/drive_c/windows/system32/sc.exe",
            "contents NOT opened", "END OF SHORT V15 READ-ONLY REPORT",
            "READ-ONLY V15 AUDIT COMPLETE", "PE mapping NOT VERIFIED",
            "Server trace shutdown markers are counts, NOT causal proof",
            "Handoff: https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md",
        ):
            with self.subTest(good=good): self.assertIn(good, JAVA)
        for forbidden in (
            "charoite-next-wine29-entry-v14", "charoite-next-wine29-entry-v13",
            "new ProcessBuilder(", "Runtime.getRuntime(", "FileOutputStream",
            "FileWriter", ".delete(", ".mkdir(", ".mkdirs(", "renameTo(",
            "clearApplicationUserData(", "System.exit(",
        ):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden, JAVA)

    def test_no_unproven_sc_or_scm_success(self):
        self.assertIn("exit 127", JAVA)
        self.assertIn("NOT alive immediately after", JAVA)
        self.assertIn("NOT proof of a sc.exe crash or root cause", JAVA)
        self.assertIn("Usage or exit status alone", JAVA)
        self.assertIn("sc.exe mentions=", JAVA)
        self.assertNotIn("RESULT: PASS — sc.exe", JAVA)

    def test_handoff_is_first_and_short_report_remains_bounded(self):
        self.assertIn('String head = "Handoff: ', JAVA)
        self.assertIn('int limit = MAX_REPORT_CHARS - head.length() - tail.length();', JAVA)
        self.assertIn('return head + b.append(tail).toString();', JAVA)
        self.assertIn('END OF SHORT V15 READ-ONLY REPORT', JAVA)

    def test_consumed_v15_hidden_only_new_readonly_active(self):
        for good in (
            "final boolean showArchivedWine29V15Execution = false;",
            "final boolean showArchivedWine29V14ReadOnly = false;",
            "Inspect Wine29 v15 sc.exe + server (read-only)",
            "CharoiteWine29V15ReadOnlyForensics.run(this)",
            "wine29CurrentAction.addView(wine29V15Audit);",
            "wine29CurrentAction.addView(handoffButton);",
            "nextCoreCard.addView(wine29CurrentAction);",
            "Open current project handoff",
            "The handoff link is the ",
            '"CharoiteWine29V15ReadOnlyForensics.java"',
            "versionCode 146", "11.2-next.0.115",
        ):
            with self.subTest(good=good): self.assertIn(good, UI)
        for good in (
            "test_wine29_v15_readonly_contract.py",
            "WINE29_V15_PRESERVED_SERVER_EXIT_READONLY_POSTMORTEM=PASS",
            "cp next-generation/CharoiteWine29V15ReadOnlyForensics.java legal-bundle/CharoiteWine29V15ReadOnlyForensics.java",
            "versionCode='146' versionName='11.2-next.0.115'",
        ):
            with self.subTest(good=good): self.assertIn(good, WF)

if __name__ == "__main__":
    unittest.main()

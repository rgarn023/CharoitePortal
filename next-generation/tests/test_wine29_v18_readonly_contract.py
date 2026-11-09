"""V18 consumed idle server evidence: precisely two fixed V18 logs, strict read-only."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V18ReadOnlyForensics.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class V18PreservedIdleReadOnlyContract(unittest.TestCase):
    def test_exact_bounded_preserved_scope(self):
        for needle in (
            "charoite-next-wine29-entry-v18", "v18-wine-direct-init.log",
            "v18-foreground-wineserver.log", "Only TWO V18 logs",
            "MAX_PE_LOG", "MAX_SERVER_LOG", "MAX_LINES", "MAX_LINE",
            "MAX_REPORT_CHARS", "peAudit(scratch, out)", "serverAudit(scratch, out)",
            "registryBytes(scratch,", "Os.lstat(", "Os.readlink(",
            "END OF SHORT V18 READ-ONLY REPORT",
            "Handoff: https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md",
        ):
            with self.subTest(required=needle):
                self.assertIn(needle, JAVA)
        for forbidden in (
            "charoite-next-wine29-entry-v17", "charoite-next-wine29-entry-v16",
            "v17-wine-direct-init.log", "v18-sc-entry.log",
            "v18-independent-wineboot-help.log", "new ProcessBuilder(",
            "Runtime.getRuntime(", "FileOutputStream", "FileWriter",
            ".delete(", ".mkdir(", ".mkdirs(", "renameTo(",
            "controlAudit(", "entryAudit(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, JAVA)

    def test_system_action_adjacent_and_execution_archived(self):
        for needle in (
            "final boolean showArchivedWine29V18Execution = false;",
            "CURRENT WINE29 ACTION — V18 PRESERVED READ-ONLY",
            "Inspect Wine29 v18 idle server (read-only)",
            "CharoiteWine29V18ReadOnlyForensics.run(this)",
            "wine29V18ReadOnlyAction.addView(wine29V18Inspect);",
            "wine29V18ReadOnlyAction.addView(v18ReadOnlyHandoff);",
            "nextCoreCard.addView(wine29V18ReadOnlyAction);",
            '"CharoiteWine29V18ReadOnlyForensics.java"',
            "versionCode 144", "11.2-next.0.113",
        ):
            with self.subTest(required=needle):
                self.assertIn(needle, UI)

    def test_ci_source_only_and_license(self):
        for needle in (
            "test_wine29_v18_readonly_contract.py",
            "WINE29_V18_PRESERVED_IDLE_SERVER_READONLY=PASS",
            "WINE29_V18_PHONE_INSPECTION=NOT_ATTEMPTED_IN_CI",
            "cp next-generation/CharoiteWine29V18ReadOnlyForensics.java legal-bundle/CharoiteWine29V18ReadOnlyForensics.java",
            "versionCode='144' versionName='11.2-next.0.113'",
        ):
            with self.subTest(required=needle):
                self.assertIn(needle, WF)

if __name__ == "__main__":
    unittest.main()

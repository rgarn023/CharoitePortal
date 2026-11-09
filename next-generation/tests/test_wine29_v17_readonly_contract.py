"""V17 consumed evidence: four fixed private logs, STRICT READ ONLY."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V17ReadOnlyForensics.java").read_text(encoding="utf-8")
UI=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class V17PreservedReadOnlyContract(unittest.TestCase):
    def test_fixed_scope_and_no_execution(self):
        for needle in ("charoite-next-wine29-entry-v17",
            "v17-wine-direct-init.log","v17-independent-wineboot-help.log",
            "v17-sc-entry.log","v17-foreground-wineserver.log",
            "Only FOUR V17 logs","no V1–V16","MAX_CONTROL_LOG","MAX_PE_LOG",
            "MAX_SC_LOG","MAX_SERVER_LOG","MAX_LINES","MAX_LINE","MAX_REPORT_CHARS",
            "controlAudit(scratch,out)","peAudit(scratch,out)","entryAudit(scratch,out)",
            "serverAudit(scratch,out)","IllegalStateException","sc.exe launch",
            "END OF SHORT V17 READ-ONLY REPORT",
            "Handoff: https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md"):
            with self.subTest(needle=needle):self.assertIn(needle,JAVA)
        for forbidden in ("charoite-next-wine29-entry-v16","charoite-next-wine29-entry-v15",
            "new ProcessBuilder(","Runtime.getRuntime(","FileOutputStream",
            "FileWriter",".delete(",".mkdir(",".mkdirs(","renameTo("):
            with self.subTest(forbidden=forbidden):self.assertNotIn(forbidden,JAVA)
    def test_ui_actions_archived_and_adjacent(self):
        for needle in ('final boolean showArchivedWine29V17Execution = false;',
            "CURRENT WINE29 ACTION — V17 PRESERVED READ-ONLY",
            "Inspect Wine29 v17 control + server (read-only)",
            "CharoiteWine29V17ReadOnlyForensics.run(this)",
            "wine29V17ReadOnlyAction.addView(wine29V17ReadOnly);",
            "wine29V17ReadOnlyAction.addView(v17ReadOnlyHandoff);",
            "nextCoreCard.addView(wine29V17ReadOnlyAction);",
            '"CharoiteWine29V17ReadOnlyForensics.java"',
            "versionCode 144","11.2-next.0.113"):
            self.assertIn(needle,UI)
        for needle in ("test_wine29_v17_readonly_contract.py",
            "WINE29_V17_PRESERVED_CONTROL_READONLY_POSTMORTEM=PASS",
            "cp next-generation/CharoiteWine29V17ReadOnlyForensics.java legal-bundle/CharoiteWine29V17ReadOnlyForensics.java",
            "versionCode='144' versionName='11.2-next.0.113'"):
            self.assertIn(needle,WF)
if __name__=="__main__":unittest.main()

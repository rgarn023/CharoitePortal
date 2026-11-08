"""Read-only audit of exactly three preserved Wine29 V16 logs and metadata."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT/"CharoiteWine29V16ReadOnlyForensics.java").read_text(encoding="utf-8")
UI = (ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
class V16ReadOnlyContract(unittest.TestCase):
    def test_scope(self):
        for token in ("charoite-next-wine29-entry-v16","v16-wine-direct-init.log",
                      "v16-sc-entry.log","v16-foreground-wineserver.log",
                      "Only THREE V16 logs","no V1–V15","MAX_PE_LOG","MAX_SC_LOG",
                      "MAX_SERVER_LOG","MAX_LINES","MAX_LINE","MAX_REPORT_CHARS",
                      "END OF SHORT V16 READ-ONLY REPORT","READ-ONLY V16 AUDIT COMPLETE",
                      "Server trace shutdown markers are counts, NOT causal proof",
                      "Handoff: https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md"):
            with self.subTest(token=token): self.assertIn(token,JAVA)
        for forbidden in ("charoite-next-wine29-entry-v15","charoite-next-wine29-entry-v14",
                          "new ProcessBuilder(","Runtime.getRuntime(","FileOutputStream",
                          "FileWriter",".delete(",".mkdir(",".mkdirs(","renameTo(","System.exit("):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden,JAVA)
    def test_unverified_sc(self):
        for token in ("native ProcessBuilder accepted it","exit 127",
                      "NOT alive at sc.exe completion","NOT proof of a sc.exe crash or root cause",
                      "PE mapping NOT VERIFIED","Usage or exit status alone"):
            self.assertIn(token,JAVA)
    def test_current_system_action(self):
        for token in ("final boolean showArchivedWine29V16Execution = false;",
                      "CURRENT WINE29 ACTION — V16 PRESERVED READ-ONLY",
                      "Inspect Wine29 v16 sc.exe + server (read-only)",
                      "CharoiteWine29V16ReadOnlyForensics.run(this)",
                      "wine29V16ReadOnlyAction.addView(wine29V16ReadOnly);",
                      "wine29V16ReadOnlyAction.addView(v16ReadOnlyHandoff);",
                      "nextCoreCard.addView(wine29V16ReadOnlyAction);",
                      '"CharoiteWine29V16ReadOnlyForensics.java"',
                      "versionCode 141","11.2-next.0.110"):
            self.assertIn(token,UI)
        for token in ("test_wine29_v16_readonly_contract.py",
                      "WINE29_V16_PRESERVED_EXEC_BOUNDARY_READONLY_POSTMORTEM=PASS",
                      "cp next-generation/CharoiteWine29V16ReadOnlyForensics.java legal-bundle/CharoiteWine29V16ReadOnlyForensics.java",
                      "versionCode='141' versionName='11.2-next.0.110'"):
            self.assertIn(token,WF)
if __name__=="__main__": unittest.main()

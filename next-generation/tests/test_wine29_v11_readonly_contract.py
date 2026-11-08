"""V11 one-shot is archived; only bounded five-log V11 audit is live."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V11ReadOnlyForensics.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine29V11ReadOnlyContract(unittest.TestCase):
    def test_only_v11_preserved_evidence(self):
        for token in (
            "charoite-next-wine29-entry-v11",
            "v11-wine-direct-init.log", "v11-foreground-wineserver.log",
            "v11-native-version-noexec-set.log",
            "v11-native-version-noexec-unset.log", "v11-sc-entry.log",
            "getNoBackupFilesDir()", "END OF SHORT V11 READ-ONLY REPORT",
            "prefix/system.reg", "prefix/user.reg", "prefix/userdef.reg",
            "contents NOT opened", "Os.lstat(", "Os.readlink(",
            "MAX_PE_LOG", "MAX_SERVER_LOG", "MAX_SC_LOG", "MAX_LINES", "MAX_LINE",
            "Only FIVE V11 logs",
        ):
            with self.subTest(token=token): self.assertIn(token, JAVA)
        for forbidden in (
            "charoite-next-wine29-entry-v10",
            "charoite-next-wine29-scm-v9", "charoite-next-wine29-userenv-v8",
            "charoite-next-wine29-services-v7", "new ProcessBuilder(",
            "Runtime.getRuntime(", "FileOutputStream", ".delete(", ".mkdir(",
            ".mkdirs(", "renameTo(", "clearApplicationUserData(", "System.exit(",
        ):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden, JAVA)

    def test_both_version_logs_and_retained_pe_server(self):
        self.assertIn('NATIVE_SET_LOG.equals(name) ? "NOEXEC=1" : "NOEXEC unset"', JAVA)
        self.assertIn("server became unavailable", JAVA)
        self.assertIn("do NOT establish a server-exit cause", JAVA)
        self.assertIn("No Windows PE or games executed by this audit", JAVA)

    def test_wiring_and_release(self):
        for t in (
            'final boolean showArchivedWine29V11Execution = false;',
            "Inspect Wine29 v11 server exit (read-only)",
            "CharoiteWine29V11ReadOnlyForensics.run(this)",
            "nextCoreCard.addView(wine29V11Audit);",
            '"CharoiteWine29V11ReadOnlyForensics.java"',
            "versionCode 133", "11.2-next.0.102",
        ): self.assertIn(t, UI)
        self.assertIn("test_wine29_v11_readonly_contract.py", WF)
        self.assertIn("WINE29_V11_PRESERVED_READONLY_POSTMORTEM=PASS", WF)
        self.assertIn("cp next-generation/CharoiteWine29V11ReadOnlyForensics.java legal-bundle/CharoiteWine29V11ReadOnlyForensics.java", WF)
        self.assertIn("versionCode='133' versionName='11.2-next.0.102'", WF)

if __name__ == "__main__":
    unittest.main()

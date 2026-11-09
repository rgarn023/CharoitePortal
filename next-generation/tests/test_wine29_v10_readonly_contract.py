"""Preserved V10 native-loader postmortem must remain read-only and archive execution."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V10ReadOnlyForensics.java").read_text(encoding="utf-8")
UI=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WORKFLOW=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine29V10ReadOnly(unittest.TestCase):
    def test_only_preserved_v10_evidence(self):
        for token in (
            'charoite-next-wine29-entry-v10',
            'v10-wine-direct-init.log', 'v10-foreground-wineserver.log',
            'v10-native-version.log', 'v10-sc-entry.log',
            'getNoBackupFilesDir()', 'END OF SHORT V10 READ-ONLY REPORT',
            'prefix/system.reg', 'prefix/user.reg', 'prefix/userdef.reg',
            'contents NOT opened', 'Os.lstat(', 'Os.readlink(',
            'MAX_PE_LOG', 'MAX_SERVER_LOG', 'MAX_SC_LOG',
            'MAX_LINES', 'MAX_LINE',
        ):
            with self.subTest(token=token):
                self.assertIn(token,JAVA)
        for forbidden in (
            'charoite-next-wine29-scm-v9', 'charoite-next-wine29-userenv-v8',
            'charoite-next-wine29-services-v7', 'new ProcessBuilder(',
            'Runtime.getRuntime(', 'FileOutputStream', '.delete(', '.mkdir(',
            '.mkdirs(', 'renameTo(', 'clearApplicationUserData(', 'System.exit(',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,JAVA)
    def test_version_failure_not_scm_evidence(self):
        self.assertIn('native version and SCM',JAVA)
        self.assertIn('sc.exe NOT attempted',JAVA)
        self.assertIn('Exit 127 alone is not a root cause',JAVA)
        self.assertIn('No Windows PE or games executed by this audit',JAVA)
    def test_only_current_button(self):
        for token in (
            'final boolean showArchivedWine29V10Execution = false;',
            'Inspect Wine29 v10 native loader failure (read-only)',
            'CharoiteWine29V10ReadOnlyForensics.run(this)',
            'nextCoreCard.addView(wine29V10Audit);',
            '"CharoiteWine29V10ReadOnlyForensics.java"',
            'versionCode 144', '11.2-next.0.113',
        ):
            with self.subTest(token=token):
                self.assertIn(token,UI)
        self.assertIn('test_wine29_v10_readonly_contract.py',WORKFLOW)
        self.assertIn('WINE29_V10_PRESERVED_READONLY_POSTMORTEM=PASS',WORKFLOW)

if __name__=="__main__":
    unittest.main()

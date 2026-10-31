"""Regression requirements for read-only postmortem of already-used v3 scratch."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FORENSICS = (ROOT / "CharoiteWine27V3Forensics.java").read_text()
PREP = (ROOT / "prepare_next.py").read_text()
CI = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text()

class ReadOnlyV3ForensicsContract(unittest.TestCase):
    def test_only_exact_used_v3_scratch_is_read(self):
        self.assertIn('getNoBackupFilesDir()', FORENSICS)
        self.assertIn('charoite-next-wine27-first-prefix-v3', FORENSICS)
        self.assertNotIn('charoite-next-wine26-first-prefix-v2"', FORENSICS)
        self.assertIn('wineboot.log', FORENSICS)
        self.assertIn('wineserver-stop.log', FORENSICS)
        self.assertIn('prefix/system.reg', FORENSICS)
        self.assertIn('prefix/user.reg', FORENSICS)
        self.assertIn('nls/l_intl.nls', FORENSICS)
        self.assertIn('nls/locale.nls', FORENSICS)
        self.assertIn('read-only v3 evidence collected; boot failure unresolved', FORENSICS)

    def test_no_execution_mutation_or_following_symlinks(self):
        for forbidden in ('new ProcessBuilder(', '.start()', 'FileOutputStream',
                          '.delete(', '.mkdir(', '.mkdirs(', 'Runtime.getRuntime()',
                          'ProcessBuilder', 'exec(', 'clearApplicationUserData',
                          'com.touhoudr', 'getFilesDir()', 'new File("/storage/'):
            self.assertNotIn(forbidden, FORENSICS)
        self.assertIn('getCanonicalFile().equals(direct.getAbsoluteFile())', FORENSICS)
        self.assertIn('getCanonicalFile().equals(scratch.getAbsoluteFile())', FORENSICS)
        self.assertIn('new RandomAccessFile(file, "r")', FORENSICS)
        self.assertIn('LOG_LIMIT = 12288', FORENSICS)

    def test_new_apk_includes_source_and_explicit_user_button(self):
        self.assertIn('versionCode 79', PREP)
        self.assertIn('11.2-next.0.48', PREP)
        self.assertIn('CharoiteWine27V3Forensics.java', PREP)
        self.assertIn('Inspect failed Wine27 v3 PE imports and logs (read-only)', PREP)
        self.assertIn('Inspect v3 without changing files', PREP)
        self.assertIn('CharoiteWine27V3Forensics.run(this)', PREP)
        self.assertIn('CharoiteWine27V3Forensics.java', CI)
        self.assertIn('CharoiteWine27PEAudit.java', CI)
        self.assertIn('CharoiteWine27PEAudit.inspect(', FORENSICS)
        self.assertIn("versionCode='79' versionName='11.2-next.0.48'", CI)

if __name__ == "__main__":
    unittest.main()

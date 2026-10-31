"""Wine28 v6 foreground wineserver-only one-shot contract."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"CharoiteWine28V6ServerProbe.java").read_text()
PREP=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
V5=(ROOT/"CharoiteWine28V5Trace.java").read_text()
class Wine28V6ServerOnlyContract(unittest.TestCase):
    def test_new_private_scratch_and_verified_native(self):
        for item in ('charoite-next-wine28-server-only-v6',
                     'getNoBackupFilesDir()', 'scratch.exists() || !scratch.mkdir()',
                     'CharoiteWine28NativeGate.run(context)',
                     'libcharoite_wine28_wineserver.so',
                     '"-f", "-d"', 'CHAROITE_WINE26_DATA_DIR',
                     'nls/locale.nls', 'nls/l_intl.nls',
                     'MessageDigest.getInstance("SHA-256")',
                     'OsConstants.S_ISSOCK', 'OsConstants.S_ISREG',
                     'DEADLINE_SECONDS = 8L', 'LOG_CAP = 256L'):
            self.assertIn(item, SOURCE)
    def test_server_only_and_no_old_data(self):
        for forbidden in ('new ProcessBuilder(loader',
                          'wineboot.exe', 'WINELOADERNOEXEC',
                          '.delete(', 'clearApplicationUserData',
                          'com.touhoudr', 'getFilesDir()',
                          'charoite-next-wine28-first-prefix-v5-ntdll-fix'):
            self.assertNotIn(forbidden,SOURCE)
        self.assertIn('process.destroyForcibly()',SOURCE)
        self.assertIn('Wineboot or PE capability established',SOURCE)
        self.assertIn('charoite-next-wine28-first-prefix-v5-ntdll-fix',V5)
        self.assertIn('scratch.exists() || !scratch.mkdir()',V5)
    def test_user_consent_and_apk_attribution(self):
        for needle in ('CharoiteWine28V6ServerProbe.java',
                       'Test isolated Wine28 wineserver only (one-shot v6)',
                       'Run ONE v6 server-only test',
                       'CharoiteWine28V6ServerProbe.run(this)',
                       'versionCode 80', '11.2-next.0.49'):
            self.assertIn(needle,PREP)
        self.assertIn('CharoiteWine28V6ServerProbe.java; do',WF)
        self.assertIn("versionCode='80' versionName='11.2-next.0.49'",WF)
if __name__=="__main__":
    unittest.main()

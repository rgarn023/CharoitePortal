"""Wine28 v7 matched Wine + isolated live server to Windows PE --help handshake."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
V7=(ROOT/"CharoiteWine28V7PeHelpProbe.java").read_text()
V5=(ROOT/"CharoiteWine28V5Trace.java").read_text()
PREP=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
class Wine28V7PeHelpContract(unittest.TestCase):
    def test_exact_private_v7_one_shot_cohort(self):
        for x in ("charoite-next-wine28-pe-help-v7",
                  "scratch.exists() || !scratch.mkdir()",
                  "CharoiteWine28NativeGate.run(context)",
                  "copyVerified(child(staged,name),dst",
                  "dll!=22 || exe!=1 || nls!=76",
                  'new ProcessBuilder(server.getAbsolutePath(),"-f","-d")',
                  'boot.getAbsolutePath(),"--help"',
                  "socketAndLock(prefix)",
                  "OsConstants.S_ISSOCK","OsConstants.S_ISREG",
                  'WINELOADERNOEXEC', "CHAROITE_WINE28_PE_DIR",
                  "RESULT: PASS — isolated Wine28 PE help reached",
                  "V7 one-shot scratch retained; NEVER rerun"):
            self.assertIn(x,V7)
        for forbidden in ('.delete(', 'clearApplicationUserData',
                          'com.touhoudr', 'getFilesDir()',
                          'charoite-next-wine28-first-prefix-v5-ntdll-fix',
                          'charoite-next-wine28-server-only-v6',
                          'new File("/storage/'):
            self.assertNotIn(forbidden,V7)
        self.assertIn('charoite-next-wine28-first-prefix-v5-ntdll-fix',V5)
    def test_user_consent_and_apk(self):
        for x in ("CharoiteWine28V7PeHelpProbe.java",
                  "Test isolated Wine28 PE help handshake (one-shot v7)",
                  "Run ONE v7 PE help test",
                  "CharoiteWine28V7PeHelpProbe.run(this)",
                  "versionCode 84", "11.2-next.0.53"):
            self.assertIn(x,PREP)
        self.assertIn("CharoiteWine28V7PeHelpProbe.java CharoiteWine28V8LayoutProbe.java CharoiteWine28V9BuiltinBootstrapProbe.java; do",WF)
        self.assertIn("versionCode='84' versionName='11.2-next.0.53'",WF)
if __name__=="__main__":
    unittest.main()

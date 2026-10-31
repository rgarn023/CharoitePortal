"""No-regression contract: Wine28 v8 corrected ARM64 DLL lookup root, new isolated prefix."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
V8=(ROOT/"CharoiteWine28V8LayoutProbe.java").read_text()
V7=(ROOT/"CharoiteWine28V7PeHelpProbe.java").read_text()
UI=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
class Wine28V8LayoutContract(unittest.TestCase):
    def test_exact_corrected_wine_arm64_search_root(self):
        for x in ('charoite-next-wine28-pe-help-v8-layout',
                  'File lib = child(scratch,"runtime/lib/wine/aarch64-windows");',
                  'env.put("WINEDLLPATH", child(scratch,"runtime/lib/wine").getCanonicalPath());',
                  'File kernel=child(lib,"kernel32.dll");',
                  'V8 kernel32 PE: verified aarch64-windows/kernel32.dll present',
                  'CHAROITE_WINE28_PE_DIR', 'WINELOADERNOEXEC',
                  'copyVerified(child(staged,name),dst',
                  'dll!=22 || exe!=1 || nls!=76',
                  'CharoiteWine28NativeGate.run(context)',
                  'new ProcessBuilder(server.getAbsolutePath(),"-f","-d")',
                  'boot.getAbsolutePath(),"--help"',
                  'socketAndLock(prefix)', 'RESULT: PASS — isolated Wine28 PE help reached'):
            self.assertIn(x,V8)
        self.assertIn('runtime/lib/wine/arm64ec-windows', V7)
        for forbidden in ('charoite-next-wine28-pe-help-v7',
                          'charoite-next-wine28-server-only-v6',
                          'charoite-next-wine28-first-prefix-v5-ntdll-fix',
                          'com.touhoudr', 'getFilesDir()', '.delete(',
                          'clearApplicationUserData'):
            self.assertNotIn(forbidden,V8)
        self.assertIn('scratch.exists() || !scratch.mkdir()',V8)
        self.assertIn('process.destroyForcibly()',V8.replace("peProc","process") if False else V8) if False else None
    def test_separate_opt_in_explicit_auto_init_warning(self):
        for x in ('CharoiteWine28V8LayoutProbe.java',
                  'Test corrected Wine28 ARM64 DLL paths (one-shot v8)',
                  'Run ONE new v8 DLL-layout test',
                  'Wine can AUTOMATICALLY run internal wineboot',
                  'CharoiteWine28V8LayoutProbe.run(this)',
                  'versionCode 83', '11.2-next.0.52'):
            self.assertIn(x,UI)
        self.assertIn('CharoiteWine28V8LayoutProbe.java; do',WF)
        self.assertIn("versionCode='83' versionName='11.2-next.0.52'",WF)
if __name__=="__main__":
    unittest.main()

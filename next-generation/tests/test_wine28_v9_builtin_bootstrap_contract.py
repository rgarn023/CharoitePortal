"""Source contract: new isolated v9 ARM64 auto-init built-in Wineboot lookup."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
V9=(ROOT/"CharoiteWine28V9BuiltinBootstrapProbe.java").read_text()
V8=(ROOT/"CharoiteWine28V8LayoutProbe.java").read_text()
PREP=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
class Wine28V9BuiltinBootstrapContract(unittest.TestCase):
    def test_source_verified_auto_init_alias(self):
        for marker in (
            'charoite-next-wine28-pe-help-v9-builtin-boot',
            'File lib = child(scratch,"runtime/lib/wine/aarch64-windows");',
            'File boot = child(scratch,"runtime/lib/wine/arm64-windows/wineboot.exe");',
            'if (name.equals("pe/arm64/wineboot.exe"))',
            'copyVerified(child(staged,name),child(lib,"wineboot.exe"),',
            'File bootBuiltin=child(lib,"wineboot.exe");',
            'V9 built-in auto-init Wineboot copy:',
            'WINEDLLPATH", child(scratch,"runtime/lib/wine").getCanonicalPath()',
            'CHAROITE_WINE28_PE_DIR',
            'CharoiteWine28NativeGate.run(context)',
            'new ProcessBuilder(server.getAbsolutePath(),"-f","-d")',
            'boot.getAbsolutePath(),"--help"',
            'socketAndLock(prefix)',
            'scratch.exists() || !scratch.mkdir()',
            'peProc.destroyForcibly()', 'serverProc.destroyForcibly()'):
            self.assertIn(marker,V9)
        self.assertIn('runtime/lib/wine/arm64-windows/wineboot.exe',V8)
        for forbidden in ('charoite-next-wine28-pe-help-v8-layout',
                          'charoite-next-wine28-pe-help-v7',
                          'charoite-next-wine28-first-prefix-v5-ntdll-fix',
                          'com.touhoudr','getFilesDir()', '.delete(',
                          'clearApplicationUserData'):
            self.assertNotIn(forbidden,V9)
    def test_opt_in_auto_init_warning_and_apk_attribution(self):
        for marker in ('CharoiteWine28V9BuiltinBootstrapProbe.java',
                       'Test Wine28 built-in Wineboot lookup (one-shot v9)',
                       'Run ONE new v9 Wineboot lookup test',
                       'Wine WILL automatically attempt wineboot --init',
                       'CharoiteWine28V9BuiltinBootstrapProbe.run(this)',
                       'versionCode 84', '11.2-next.0.53'):
            self.assertIn(marker,PREP)
        self.assertIn('CharoiteWine28V9BuiltinBootstrapProbe.java; do',WF)
        self.assertIn("versionCode='84' versionName='11.2-next.0.53'",WF)
if __name__=="__main__": unittest.main()

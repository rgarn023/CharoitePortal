"""Safety contracts for the separate, explicitly authorized Wine29 v2 trace."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V2BootstrapProbe.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine29V2BootstrapContracts(unittest.TestCase):
    def test_isolated_exactly_once_and_sealed_source(self):
        for token in (
            "charoite-next-wine29-bootstrap-v2",
            'private static final String PACKAGE = "com.charoitx"',
            'private static final int COUNT = 111',
            'CharoiteWine29Sealed012PePreflight.run(context)',
            'CharoiteWine29Sealed012Stage.verifyOnly(context)',
            'getNoBackupFilesDir()',
            'if (scratch.exists() || !scratch.mkdir())',
            'src.length() != size',
            'md.update(block, 0, n)',
            'index.getInt("module_count") != 111',
            'env.clear()',
            'env.put("WINEPREFIX", prefix.getCanonicalPath())',
            'env.put("WINEDLLPATH"',
            'env.put("CHAROITE_WINE29_NATIVE_DIR"',
            'env.put("CHAROITE_WINE29_PE_DIR"',
            'env.put("CHAROITE_WINE29_DATA_DIR"',
            'WINELOADERNOEXEC',
            'WINEBOOTSTRAPMODE',
            'new ProcessBuilder(server.getAbsolutePath(),"-f","-d")',
            'new ProcessBuilder(loader.getAbsolutePath()',
            'boot.getAbsolutePath(),"--help"',
            'peProc.destroyForcibly()',
            'serverProc.destroyForcibly()',
            'TimeUnit.SECONDS.toNanos(12)',
            'TimeUnit.SECONDS.toNanos(5)',
            'sanitizeLog(',
            'lower.contains("env=")',
            'NEVER rerun/delete v2',
        ):
            with self.subTest(token=token): self.assertIn(token, JAVA)
        self.assertLess(JAVA.index('CharoiteWine29Sealed012Stage.verifyOnly(context)'), JAVA.index('scratch.mkdir()'))
        self.assertNotIn('env.put("WINEBOOTSTRAPMODE"', JAVA)
        for forbidden in (
            "charoite-next-wine29-pe-help-v1",
            'new ProcessBuilder("/system/bin/sh"',
            'sh -c', '.delete(', 'deleteOnExit(', 'Runtime.getRuntime(',
            'clearApplicationUserData', 'getFilesDir(', 'new File("/sdcard"',
            'CharoiteWine29V1PeHelpProbe.run(',
        ):
            self.assertNotIn(forbidden, JAVA)

    def test_current_system_button_requires_explicit_authorization(self):
        self.assertIn('"CharoiteWine29V2BootstrapProbe.java"', UI)
        self.assertIn('wine29V2Bootstrap.setText("Wine29 v2 bootstrap and kernel32 trace (one-shot)")', UI)
        self.assertIn('setPositiveButton("Authorize ONE new v2 diagnostic"', UI)
        self.assertIn('setNegativeButton("Cancel — do not execute", null)', UI)
        self.assertIn('CharoiteWine29V2BootstrapProbe.run(this)', UI)
        self.assertIn('nextCoreCard.addView(wine29V2Bootstrap);', UI)
        self.assertIn('versionCode 139', UI)
        self.assertIn('11.2-next.0.108', UI)
        self.assertGreater(UI.index('wine29V2Bootstrap.setText('), UI.index('} // Archived test controls'))
        before = UI.split('wine29V2Bootstrap.setOnClickListener(v ->',1)[0]
        self.assertNotIn('CharoiteWine29V2BootstrapProbe.run(this)', before)
        self.assertIn('wine29V1Forensics.setText(', UI)

    def test_ci_signing_and_source_publication(self):
        self.assertIn("test_wine29_v2_bootstrap_contract.py", WF)
        self.assertIn("WINE29_V2_ONE_SHOT_CONSENT_ISOLATION=PASS", WF)
        self.assertIn("cp next-generation/CharoiteWine29V2BootstrapProbe.java legal-bundle/CharoiteWine29V2BootstrapProbe.java", WF)
        self.assertIn("versionCode='139' versionName='11.2-next.0.108'", WF)

if __name__ == "__main__":
    unittest.main()

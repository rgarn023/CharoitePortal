"""Source-level contracts for one-shot, opt-in Wine29 v1 PE-help bootstrap."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "CharoiteWine29V1PeHelpProbe.java"
PREP = ROOT / "prepare_next.py"
WORKFLOW = ROOT.parent / ".github/workflows/charoite-next.yml"

class Wine29V1PeHelpContracts(unittest.TestCase):
    def test_strict_explicit_ui_authorization_and_versions(self):
        ui = PREP.read_text(encoding="utf-8")
        self.assertIn('"CharoiteWine29V1PeHelpProbe.java"', ui)
        self.assertIn('wine29PeHelpV1.setText("Wine29 v1 isolated Wineboot PE-help test (one-shot)")', ui)
        self.assertIn('setPositiveButton("Authorize ONE new v1 test"', ui)
        self.assertIn('setNegativeButton("Cancel — do not execute", null)', ui)
        self.assertIn('Wine MAY automatically initialize', ui)
        self.assertIn('CharoiteWine29V1PeHelpProbe.run(this)', ui)
        self.assertIn('versionCode 143', ui)
        self.assertIn('11.2-next.0.112', ui)
        # Source invocation must be under its explicit consent button only.
        before = ui.split('wine29PeHelpV1.setOnClickListener(v ->', 1)[0]
        self.assertNotIn('CharoiteWine29V1PeHelpProbe.run(this)', before)

    def test_one_shot_private_111_hashes_and_no_legacy_fallback(self):
        source = PROBE.read_text(encoding="utf-8")
        must = (
          'charoite-next-wine29-012-sealed-pe-nls/wine10-arm64ec-dependencies-0.12-sealed-pe-nls',
          'charoite-next-wine29-pe-help-v1',
          'charoite-next/wine29-sealed012/wine29-sealed012-index.json',
          'private static final int COUNT = 111',
          'index.getInt("pe_count") != 35',
          'index.getInt("nls_count") != 76',
          'index.getInt("module_count") != 111',
          'dll!=34 || exe!=1 || nls!=76',
          'CharoiteWine29Sealed012PePreflight.run(context)',
          'CharoiteWine29Sealed012Stage.verifyOnly(context)',
          'if (scratch.exists() || !scratch.mkdir())',
          'src.length() != size',
          'md.update(block, 0, n)',
          'env.clear()',
          'env.put("CHAROITE_WINE29_NATIVE_DIR"',
          'env.put("CHAROITE_WINE29_PE_DIR"',
          'env.put("CHAROITE_WINE29_DATA_DIR"',
          'env.put("WINEPREFIX", prefix.getCanonicalPath())',
          'env.put("WINESERVER", server.getCanonicalPath())',
          'env.put("WINEDLLPATH"',
          'env.put("WINELOADERNOEXEC", "1")',
          'new ProcessBuilder(server.getAbsolutePath(),"-f","-d")',
          'new ProcessBuilder(loader.getAbsolutePath()',
          'boot.getAbsolutePath(),"--help"',
          'peProc.destroyForcibly()',
          'serverProc.destroyForcibly()',
          'TimeUnit.SECONDS.toNanos(12)',
          'TimeUnit.SECONDS.toNanos(5)',
          'NEVER rerun/delete v1'
        )
        for token in must:
            with self.subTest(token=token):
                self.assertIn(token, source)
        for forbidden in ('CHAROITE_WINE26_DATA_DIR',
                          'env.put("CHAROITE_WINE28_', 'ProcessBuilder("/system/bin/sh"',
                          'sh -c', 'System.loadLibrary', '.delete(', '.deleteOnExit(',
                          'runtime.exec', '.renameTo(', 'exec("'):
            self.assertNotIn(forbidden, source)
        self.assertLess(source.index('CharoiteWine29Sealed012Stage.verifyOnly(context)'),
                        source.index('scratch.mkdir()'))
        self.assertLess(source.index('CharoiteWine29Sealed012PePreflight.run(context)'),
                        source.index('scratch.mkdir()'))

    def test_ci_signing_and_non_game_label(self):
        wf = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("test_wine29_v1_pe_help_contract.py", wf)
        self.assertIn("WINE29_V1_ONE_SHOT_EXPLICIT_CONSENT_GUARD=PASS", wf)
        self.assertIn("versionCode='143' versionName='11.2-next.0.112'", wf)
        text = PROBE.read_text(encoding="utf-8")
        self.assertIn('NOT Wineboot -i or Windows gaming', text)
        self.assertIn('Wine WILL attempt internal auto --init', text)

if __name__=="__main__":
    unittest.main()

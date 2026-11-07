"""Wine29 .0.12 read-only phone PE/ARM64EC and direct/delay import preflight."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / "CharoiteWine29Sealed012PePreflight.java"
PREP = ROOT / "prepare_next.py"
STAGE = ROOT / "CharoiteWine29Sealed012Stage.java"
WORKFLOW = ROOT.parent / ".github/workflows/charoite-next.yml"

class Wine29Sealed012Preflight(unittest.TestCase):
    def test_explicit_read_only_button_no_auto_run(self):
        ui = PREP.read_text(encoding="utf-8")
        self.assertIn('"CharoiteWine29Sealed012PePreflight.java"', ui)
        self.assertIn('wine29SealedPe.setText("Preflight Wine29 0.12 PE imports (read-only)")', ui)
        self.assertIn('CharoiteWine29Sealed012PePreflight.run(this)', ui)
        self.assertIn('nextCoreCard.addView(wine29SealedPe);', ui)
        self.assertIn('versionCode 107', ui)
        self.assertIn('11.2-next.0.76', ui)
        self.assertNotIn('CharoiteWine29Sealed012PePreflight.run(this)', ui.split('        nextCoreCard.addView(wine29SealedVerify);')[0])

    def test_no_execution_no_mutation_strict_sealed_source_gate(self):
        code = JAVA.read_text(encoding="utf-8")
        for phrase in ('CharoiteWine29Sealed012Stage.verifyOnly(context)',
                       'charoite-next-wine29-012-sealed-pe-nls',
                       'wine10-arm64ec-dependencies-0.12-sealed-pe-nls',
                       'dlls.length != 34', 'inspect(dll, ARM64EC',
                       'inspect(wineboot, ARM64', 'inspectDelayed(wineboot, delayed)',
                       'opt + 112 + 13 * 8', 'u32(data, opt + 108) <= 13',
                       'directImports != 186', 'delayedImports != 68',
                       'deferredOutside.size() != 15',
                       'external.isEmpty()', 'Raw COFF machines among 34 DLLs',
                       'Selectors proposed ONLY; environment variables NOT set or executed'):
            self.assertIn(phrase, code)
        for forbidden in ('ProcessBuilder', 'Runtime.getRuntime', 'exec(', 'mkdir(',
                          'mkdirs(', 'FileOutputStream', '.delete(', 'renameTo(',
                          'WINEPREFIX', 'System.load', 'getSharedPreferences'):
            self.assertNotIn(forbidden, code)
        self.assertNotIn('CharoiteWine29Sealed012PePreflight', STAGE.read_text())

    def test_ci_repeats_read_only_source_guard(self):
        wf=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('test_wine29_012_pe_preflight.py', wf)
        self.assertIn('WINE29_012_PE_IMPORT_PREFLIGHT_NO_EXECUTION=PASS', wf)
        self.assertIn('versionCode=\'107\' versionName=\'11.2-next.0.76\'', wf)

if __name__=="__main__":
    unittest.main()

"""Wine29 v3 is a distinct one-shot PE directory correction, not a v2 retry."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V3LayoutProbe.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine29V3LayoutContracts(unittest.TestCase):
    def test_unique_scratch_exact_hashes_and_directory_alignment(self):
        for token in (
            'private static final String PACKAGE = "com.charoitx"',
            'charoite-next-wine29-pe-dir-v3',
            'private static final int COUNT = 111',
            'CharoiteWine29Sealed012PePreflight.run(context)',
            'CharoiteWine29Sealed012Stage.verifyOnly(context)',
            'getNoBackupFilesDir()',
            'if (scratch.exists() || !scratch.mkdir())',
            'md.update(block, 0, n)',
            'copyVerified(child(staged,name),child(lib,"wineboot.exe")',
            'bootBuiltin.getAbsolutePath(),"--help"',
            'bootBuiltin.getCanonicalFile().getParentFile()',
            'kernel.getCanonicalFile().getParentFile()',
            'env.clear()',
            'env.put("WINEPREFIX", prefix.getCanonicalPath())',
            'env.put("WINEDLLPATH"',
            'env.put("CHAROITE_WINE29_NATIVE_DIR"',
            'env.put("CHAROITE_WINE29_PE_DIR"',
            'env.put("CHAROITE_WINE29_DATA_DIR"',
            'TimeUnit.SECONDS.toNanos(12)',
            'peProc.destroyForcibly()',
            'serverProc.destroyForcibly()',
            'sanitizeLog(',
            'NEVER rerun/delete v3',
        ):
            with self.subTest(token=token): self.assertIn(token, JAVA)
        self.assertLess(JAVA.index('CharoiteWine29Sealed012Stage.verifyOnly(context)'), JAVA.index('scratch.mkdir()'))
        self.assertNotIn('boot.getAbsolutePath(),"--help"', JAVA, "Do not reintroduce v2 launch directory")
        for forbidden in (
            'charoite-next-wine29-bootstrap-v2',
            'charoite-next-wine29-pe-help-v1',
            'env.put("WINEBOOTSTRAPMODE"',
            'Runtime.getRuntime(',
            '.delete(', '.renameTo(', 'deleteOnExit(',
            'clearApplicationUserData', 'getFilesDir(',
        ):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden, JAVA)

    def test_ui_one_shot_opt_in_and_archived_v2(self):
        self.assertIn('"CharoiteWine29V3LayoutProbe.java"', UI)
        self.assertIn('wine29V3Layout.setText("Wine29 v3 matched-directory Wineboot test (one-shot)")', UI)
        self.assertIn('setPositiveButton("Authorize ONE new v3 test"', UI)
        self.assertIn('setNegativeButton("Cancel — do not execute", null)', UI)
        self.assertIn('CharoiteWine29V3LayoutProbe.run(this)', UI)
        self.assertIn('nextCoreCard.addView(wine29V3Layout);', UI)
        self.assertIn('final boolean showArchivedWine29V2Execution = false;', UI)
        self.assertIn('final boolean showArchivedWine29V3Execution = false;', UI)
        self.assertIn('wine29V1Forensics.setText(', UI)
        self.assertIn('versionCode 125', UI)
        self.assertIn('11.2-next.0.94', UI)
        before = UI.split('wine29V3Layout.setOnClickListener(v ->', 1)[0]
        self.assertNotIn('CharoiteWine29V3LayoutProbe.run(this)', before)

    def test_ci_integration(self):
        self.assertIn("test_wine29_v3_layout_contract.py", WF)
        self.assertIn("WINE29_V3_MATCHED_PE_DIRECTORY_CONSENT=PASS", WF)
        self.assertIn("cp next-generation/CharoiteWine29V3LayoutProbe.java legal-bundle/CharoiteWine29V3LayoutProbe.java", WF)
        self.assertIn("versionCode='125' versionName='11.2-next.0.94'", WF)

if __name__ == "__main__":
    unittest.main()

"""Wine29 V14 only: a NEW private Windows-path sc.exe launch, explicit one-shot."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V14ScWindowsPathProbe.java").read_text(encoding="utf-8")
UI=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")


class Wine29V14WindowsPathContract(unittest.TestCase):
    def test_new_v14_scratch_and_source_pinned_sc(self):
        for s in (
            'charoite-next-wine29-entry-v14',
            'sc.exe source SHA-256/import/PE gate: PASS',
            'V14 private Windows system32/sc.exe SHA-256: PASS',
            'V14 sc.exe launch form: WINDOWS',
            'drive_c/windows/system32/sc.exe',
            '"C:\\\\windows\\\\system32\\\\sc.exe"',
            'cSc.getCanonicalFile().getParentFile().equals(privateSystem32)',
            'cSc.length()!=scImage.length',
            'expectedSc.equals(hex(v14Digest.digest()))',
            'V14 sc.exe Windows-path PE-entry attempted: true',
            'V14 sc.exe WINELOADERNOEXEC: UNSET',
            'scEnv.remove("WINELOADERNOEXEC")',
            'V14 SCM query / service operation: NOT ATTEMPTED',
            'V14 prior Wine29 v1-v13 scratch directories: NOT ACCESSED',
            'END OF SHORT V14 ENTRY REPORT',
        ):
            with self.subTest(s=s): self.assertIn(s,JAVA)
        for bad in (
            'charoite-next-wine29-entry-v13',
            'charoite-next-wine29-scm-v9',
            'scBuiltin.getAbsolutePath());',
            'scBuiltin.getAbsolutePath(),"query"',
            'clearApplicationUserData(',
            '.delete(', 'renameTo(',
        ):
            with self.subTest(bad=bad): self.assertNotIn(bad,JAVA)
        self.assertIn('if (scratch.exists() || !scratch.mkdir())', JAVA)
        self.assertIn('scProc=entry.start();', JAVA)
        self.assertIn('TimeUnit.SECONDS.toNanos(12)', JAVA)

    def test_ui_only_v14_active_and_consent_required(self):
        for s in (
            'final boolean showArchivedWine29V12Execution = false;',
            'final boolean showArchivedWine29V13Execution = false;',
            'final boolean showArchivedWine29V13ReadOnly = false;',
            'final boolean showArchivedWine29V14Execution = false;',
            'Test Wine29 v14 sc.exe Windows C: path (one-shot)',
            'Authorize ONE fresh v14 test',
            'Cancel — do not execute',
            'CharoiteWine29V14ScWindowsPathProbe.run(this)',
            'nextCoreCard.addView(wine29V14WindowsPath);',
            '"CharoiteWine29V14ScWindowsPathProbe.java"',
            'versionCode 142','11.2-next.0.111',
        ):
            with self.subTest(s=s): self.assertIn(s,UI)

    def test_build_ci_remains_source_only(self):
        for s in (
            'test_wine29_v14_windows_path_contract.py',
            'WINE29_V14_FRESH_WINDOWS_SC_PATH_ONE_SHOT=PASS',
            'WINE29_V14_PHONE_EXECUTION=NOT_ATTEMPTED_IN_CI',
            'cp next-generation/CharoiteWine29V14ScWindowsPathProbe.java legal-bundle/CharoiteWine29V14ScWindowsPathProbe.java',
            "versionCode='142' versionName='11.2-next.0.111'",
        ):
            with self.subTest(s=s): self.assertIn(s,WF)

if __name__=="__main__":
    unittest.main()

"""V15: private C: sc.exe path with WINELOADERNOEXEC=1, source-only safety gate."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V15ScWindowsNoexecProbe.java").read_text(encoding="utf-8")
UI=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
class V15WindowsNoexecContract(unittest.TestCase):
    def test_new_private_prefix_and_c_path_only(self):
        for s in (
            "charoite-next-wine29-entry-v15",
            "V15 private Windows system32/sc.exe SHA-256: PASS",
            "drive_c/windows/system32/sc.exe",
            'scEnv.get("WINELOADERNOEXEC")',
            "V15 scoped Windows-path NOEXEC=1 gate failed",
            "V15 sc.exe WINELOADERNOEXEC: 1 (verified)",
            "V15 SCM query / service operation: NOT ATTEMPTED",
            "V15 prior Wine29 v1-v14 scratch directories: NOT ACCESSED",
            "END OF SHORT V15 ENTRY REPORT",
        ):
            with self.subTest(s=s): self.assertIn(s,JAVA)
        for forbidden in (
            "charoite-next-wine29-entry-v14",
            'scEnv.remove("WINELOADERNOEXEC")',
            "clearApplicationUserData(", ".delete(", "renameTo(",
            'scBuiltin.getAbsolutePath(),"query"',
        ):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden,JAVA)
        self.assertIn("if (scratch.exists() || !scratch.mkdir())",JAVA)
        self.assertIn("scProc=entry.start();",JAVA)
        self.assertIn("TimeUnit.SECONDS.toNanos(12)",JAVA)
    def test_only_v15_active_with_explicit_owner_consent(self):
        for s in (
            "final boolean showArchivedWine29V14Execution = false;",
            "final boolean showArchivedWine29V14ReadOnly = false;",
            "Test Wine29 v15 Windows sc.exe + NOEXEC=1 (one-shot)",
            "Authorize ONE fresh v15 test",
            "Cancel — do not execute",
            "CharoiteWine29V15ScWindowsNoexecProbe.run(this)",
            "nextCoreCard.addView(wine29V15Entry);",
            '"CharoiteWine29V15ScWindowsNoexecProbe.java"',
            "versionCode 138","11.2-next.0.107",
        ):
            with self.subTest(s=s):self.assertIn(s,UI)
    def test_ci_is_not_phone_execution(self):
        for s in (
            "test_wine29_v15_windows_noexec_contract.py",
            "WINE29_V15_WINDOWS_PATH_NOEXEC_ONE_SHOT=PASS",
            "WINE29_V15_PHONE_EXECUTION=NOT_ATTEMPTED_IN_CI",
            "cp next-generation/CharoiteWine29V15ScWindowsNoexecProbe.java legal-bundle/CharoiteWine29V15ScWindowsNoexecProbe.java",
            "versionCode='138' versionName='11.2-next.0.107'",
        ):
            with self.subTest(s=s):self.assertIn(s,WF)
if __name__=="__main__":
    unittest.main()

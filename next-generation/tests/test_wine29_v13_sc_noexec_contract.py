"""V13 one-shot sc.exe native loader handoff. Tests only; never run Wine on CI."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V13ScNoexecProbe.java").read_text(encoding="utf-8")
UI=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine29V13ScNoexecContract(unittest.TestCase):
    def test_new_private_scratch_and_preflight_before_writes(self):
        for marker in (
            "charoite-next-wine29-entry-v13","getNoBackupFilesDir()",
            "verifyV6Native(context);","verifyV7Services(context);",
            "verifyV8Userenv(context);","verifyV13Sc(context);",
            "if (scratch.exists() || !scratch.mkdir())",
            "END OF SHORT V13 ENTRY REPORT",
            "V13 scratch retained; NEVER retry or delete V13",
        ):
            with self.subTest(marker=marker): self.assertIn(marker,JAVA)
        self.assertLess(JAVA.index("verifyV13Sc(context);"),
                        JAVA.index("scratch = child(privateBase, SCRATCH);"))
        for forbidden in (
            "charoite-next-wine29-entry-v12","charoite-next-wine29-entry-v11",
            "charoite-next-wine29-entry-v10","charoite-next-wine29-scm-v9",
            "clearApplicationUserData(", ".delete(", "renameTo(",
            "Runtime.getRuntime("):
            self.assertNotIn(forbidden,JAVA)

    def test_one_no_argument_sc_launch_only_with_unset_noexec(self):
        for token in (
            'env.put("WINELOADERNOEXEC", "1");',
            'String removedNoexec=scEnv.remove("WINELOADERNOEXEC");',
            'scEnv.containsKey("WINELOADERNOEXEC")',
            "V13 sc.exe WINELOADERNOEXEC: UNSET (verified)",
            'scEnv.containsKey("WINEBOOTSTRAPMODE")',
            'scBuiltin.getAbsolutePath());',
            'TimeUnit.SECONDS.toNanos(12)',
            'V13 SCM query / service operation: NOT ATTEMPTED',
            'V13 native --version probes: NOT ATTEMPTED',
        ):
            self.assertIn(token,JAVA)
        self.assertEqual(JAVA.count("scProc=entry.start();"),1)
        self.assertEqual(JAVA.count('scBuiltin.getAbsolutePath());'),1)
        for forbidden in (
            'scBuiltin.getAbsolutePath(),"query"',
            'scBuiltin.getAbsolutePath(),"start"',
            'scBuiltin.getAbsolutePath(),"stop"',
            'new ProcessBuilder(loader.getAbsolutePath(),"--version")',
        ):
            self.assertNotIn(forbidden,JAVA)

    def test_ui_explicit_consent_archives_v12_and_bumps_version(self):
        for token in (
            '"CharoiteWine29V13ScNoexecProbe.java"',
            'final boolean showArchivedWine29V12Execution = false;',
            'final boolean showArchivedWine29V12ReadOnly = false;',
            'CharoiteWine29V13ScNoexecProbe.run(this)',
            'Authorize ONE fresh v13 test',
            'Cancel — do not execute',
            'nextCoreCard.addView(wine29V13Entry);',
            'versionCode 135', '11.2-next.0.104',
        ):
            self.assertIn(token,UI)
        for token in (
            "test_wine29_v13_sc_noexec_contract.py",
            "WINE29_V13_SC_NOEXEC_UNSET_ONLY=PASS",
            "versionCode='135' versionName='11.2-next.0.104'",
            "cp next-generation/CharoiteWine29V13ScNoexecProbe.java legal-bundle/CharoiteWine29V13ScNoexecProbe.java",
        ):
            self.assertIn(token,WF)

if __name__=="__main__":
    unittest.main()

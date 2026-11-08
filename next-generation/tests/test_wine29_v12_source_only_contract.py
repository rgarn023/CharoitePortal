"""One-shot Wine29 V12 first-sc.exe probe: opt-in APK wiring, no CI phone execution."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V12ScEntryProbe.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")


class Wine29V12SourceOnlyContract(unittest.TestCase):
    def test_fresh_prefix_and_pinned_sources_only(self):
        for marker in (
            "public final class CharoiteWine29V12ScEntryProbe",
            'charoite-next-wine29-entry-v12',
            'if (scratch.exists() || !scratch.mkdir())',
            'getNoBackupFilesDir()',
            'verifyV6Native(context);',
            'verifyV7Services(context);',
            'verifyV8Userenv(context);',
            'verifyV12Sc(context);',
            'END OF SHORT V12 ENTRY REPORT',
            'V12 scratch retained; NEVER retry or delete V12',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, JAVA)
        self.assertLess(JAVA.index("verifyV12Sc(context);"),
                        JAVA.index("scratch = child(privateBase, SCRATCH);"))
        for old_scratch in (
            'charoite-next-wine29-entry-v11',
            'charoite-next-wine29-entry-v10',
            'charoite-next-wine29-scm-v9',
            'charoite-next-wine29-userenv-v8',
            'charoite-next-wine29-services-v7',
        ):
            self.assertNotIn(old_scratch, JAVA)
        for forbidden in ("clearApplicationUserData(", ".delete(", "renameTo(",
                          "Runtime.getRuntime(", "getExternalStorageDirectory("):
            self.assertNotIn(forbidden, JAVA)

    def test_one_sc_entry_before_version_without_scm_query(self):
        for marker in (
            'V12 native --version probes: NOT ATTEMPTED',
            'v12-sc-entry.log',
            'boolean serverBeforeSc = serverProc.isAlive();',
            'scBuiltin.getAbsolutePath());',
            'scEnv.get("WINELOADERNOEXEC")',
            'TimeUnit.SECONDS.toNanos(12)',
            'scLog.length()>512L*1024L',
            'V12 sc.exe PE mapping: UNVERIFIED',
            'V12 SCM query / service operation: NOT ATTEMPTED',
        ):
            self.assertIn(marker, JAVA)
        self.assertEqual(JAVA.count('scProc=entry.start();'), 1)
        self.assertNotIn('new ProcessBuilder(loader.getAbsolutePath(),"--version")', JAVA)
        self.assertNotIn('v12-native-version-noexec', JAVA)
        self.assertNotIn('scBuiltin.getAbsolutePath(),"query"', JAVA)
        self.assertNotIn('scBuiltin.getAbsolutePath(),"start"', JAVA)
        self.assertNotIn('scBuiltin.getAbsolutePath(),"stop"', JAVA)

    def test_explicit_consent_wired_not_auto_executed(self):
        self.assertIn('"CharoiteWine29V12ScEntryProbe.java"', UI)
        self.assertIn('CharoiteWine29V12ScEntryProbe.run(this)', UI)
        self.assertIn('final boolean showArchivedWine29V11Execution = false;', UI)
        self.assertIn('final boolean showArchivedWine29V11ReadOnly = false;', UI)
        self.assertIn('final boolean showArchivedWine29V12Execution = false;', UI)
        self.assertIn('Authorize ONE fresh v12 test', UI)
        self.assertIn('Cancel — do not execute', UI)
        self.assertIn('nextCoreCard.addView(wine29V12Entry);', UI)
        self.assertIn('Inspect Wine29 v11 server exit (read-only)', UI)
        self.assertIn('versionCode 142', UI)
        self.assertIn('11.2-next.0.111', UI)


if __name__ == "__main__":
    unittest.main()

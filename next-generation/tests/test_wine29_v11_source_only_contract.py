"""V11 source candidate must remain entirely unwired until a distinct signed/consented release."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V11EntryProbe.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")

class Wine29V11SourceOnlyContract(unittest.TestCase):
    def test_fresh_v11_scratch_and_pinned_preflight(self):
        for marker in (
            "charoite-next-wine29-entry-v11",
            "if (scratch.exists() || !scratch.mkdir())",
            "getNoBackupFilesDir()",
            "verifyV6Native(context);",
            "verifyV7Services(context);",
            "verifyV8Userenv(context);",
            "verifyV11Sc(context);",
            "END OF SHORT V11 ENTRY REPORT",
            "V11 scratch retained; NEVER retry or delete V11",
        ):
            with self.subTest(marker=marker): self.assertIn(marker, JAVA)
        self.assertLess(JAVA.index("verifyV11Sc(context);"),
                        JAVA.index("scratch = child(privateBase, SCRATCH);"))
        for forbidden in (
            "charoite-next-wine29-entry-v10",
            "charoite-next-wine29-scm-v9",
            "charoite-next-wine29-userenv-v8",
            "charoite-next-wine29-services-v7",
            "clearApplicationUserData(",
            ".delete(", "renameTo(", "Runtime.getRuntime(",
        ):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden, JAVA)

    def test_comparative_native_version_probe(self):
        for marker in (
            'v11-native-version-noexec-set.log',
            'v11-native-version-noexec-unset.log',
            'v11-sc-entry.log',
            'controlEnv.get("WINELOADERNOEXEC")',
            'fixedEnv.remove("WINELOADERNOEXEC")',
            'fixedEnv.containsKey("WINELOADERNOEXEC")',
            'scEnv.get("WINELOADERNOEXEC")',
            'nativeFixedProc.waitFor(5,TimeUnit.SECONDS)',
            'V11 version-only gate independent of sc.exe PE entry: true',
            'V11 SCM query: NOT ATTEMPTED (PE entry only)',
            'scLog.length()>512L*1024L',
            'TimeUnit.SECONDS.toNanos(12)',
        ):
            with self.subTest(marker=marker): self.assertIn(marker, JAVA)
        self.assertNotIn('scBuiltin.getAbsolutePath(),"query"',JAVA)
        self.assertNotIn('scBuiltin.getAbsolutePath(),"start"',JAVA)
        self.assertNotIn('scBuiltin.getAbsolutePath(),"stop"',JAVA)

    def test_wired_only_behind_fresh_one_shot_consent(self):
        self.assertIn('"CharoiteWine29V11EntryProbe.java"',UI)
        self.assertIn('CharoiteWine29V11EntryProbe.run(this)',UI)
        self.assertIn('final boolean showArchivedWine29V10Execution = false;',UI)
        self.assertIn('final boolean showArchivedWine29V10ReadOnly = false;',UI)
        self.assertIn('Authorize ONE fresh v11 test',UI)
        self.assertIn('Cancel — do not execute',UI)
        self.assertIn('nextCoreCard.addView(wine29V11Entry);',UI)
        self.assertIn('"11.2-next.0.104"',UI)
        self.assertIn('versionCode 135',UI)
        self.assertNotIn('showArchivedWine29V10ReadOnly = true',UI)

if __name__ == "__main__":
    unittest.main()

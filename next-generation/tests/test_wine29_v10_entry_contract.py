"""V10 must use fresh one-shot isolated scratch and test SC PE entry, never query SCM."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT/"CharoiteWine29V10EntryProbe.java").read_text(encoding="utf-8")
UI = (ROOT/"prepare_next.py").read_text(encoding="utf-8")
WORKFLOW = (ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
V9 = (ROOT/"CharoiteWine29V9ScmProbe.java").read_text(encoding="utf-8")

class Wine29V10Entry(unittest.TestCase):
    def test_new_scratch_without_old_path_access(self):
        for token in ("charoite-next-wine29-entry-v10","v10-native-version.log",
                      "v10-sc-entry.log","v10-wine-direct-init.log",
                      "v10-foreground-wineserver.log","getNoBackupFilesDir()",
                      "if (scratch.exists() || !scratch.mkdir())",
                      "V10 scratch retained; NEVER retry or delete V10",
                      "END OF SHORT V10 ENTRY REPORT"):
            with self.subTest(token=token): self.assertIn(token, JAVA)
        for forbidden in ("charoite-next-wine29-scm-v9", "charoite-next-wine29-userenv-v8",
                          "charoite-next-wine29-services-v7", "clearApplicationUserData(",
                          ".delete(", "renameTo(", "Runtime.getRuntime("):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden,JAVA)
    def test_source_closure_before_new_scratch(self):
        for token in ("verifyV6Native(context);", "verifyV7Services(context);",
                      "verifyV8Userenv(context);", "verifyV10Sc(context);",
                      "scBuiltin=child(lib,\"sc.exe\")",
                      'charoite-next/wine29-v9-sc/sc-arm64.exe.bin'):
            with self.subTest(token=token): self.assertIn(token,JAVA)
        self.assertLess(JAVA.index("verifyV10Sc(context);"),
                        JAVA.index("scratch = child(privateBase, SCRATCH);"))
        self.assertIn("v9-sc-query.log", V9)
    def test_no_scm_query_and_bounded_native_sc(self):
        for token in ('new ProcessBuilder(loader.getAbsolutePath(),"--version")',
                      "nativeProc.waitFor(5,TimeUnit.SECONDS)",
                      "scProc.waitFor(200,TimeUnit.MILLISECONDS)",
                      "TimeUnit.SECONDS.toNanos(12)",
                      "scLog.length()>512L*1024L",
                      "new ProcessBuilder(loader.getAbsolutePath(),",
                      "scBuiltin.getAbsolutePath());",
                      "V10 SCM query: NOT ATTEMPTED (PE entry only)"):
            with self.subTest(token=token): self.assertIn(token,JAVA)
        self.assertNotIn('scBuiltin.getAbsolutePath(),"query"', JAVA)
        self.assertNotIn('scBuiltin.getAbsolutePath(),"-i"', JAVA)
    def test_live_button_archives_old_v9_controls_and_ci(self):
        for token in ("final boolean showArchivedWine29V9Execution = false;",
                      "final boolean showArchivedWine29V9ReadOnly = false;",
                      "Test Wine29 v10 sc.exe PE entry (one-shot)",
                      "Authorize ONE fresh v10 test", "Cancel — do not execute",
                      "CharoiteWine29V10EntryProbe.run(this)",
                      "nextCoreCard.addView(wine29V10Entry);",
                      '"CharoiteWine29V10EntryProbe.java"',
                      "versionCode 126", "11.2-next.0.95"):
            with self.subTest(token=token): self.assertIn(token,UI)
        self.assertIn("final boolean showArchivedWine29V10Execution = false;", UI)
        self.assertIn("Inspect Wine29 v10 native loader failure (read-only)", UI)
        for token in ("test_wine29_v10_entry_contract.py",
                      "WINE29_V10_NEW_PREFIX_PE_ENTRY_CONSENT=PASS",
                      "versionCode='126' versionName='11.2-next.0.95'"):
            with self.subTest(token=token): self.assertIn(token,WORKFLOW)

if __name__ == "__main__":
    unittest.main()

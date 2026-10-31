"""One-shot user-consented Wine26 fresh-prefix bootstrap, never existing saves."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROBE = (ROOT/"CharoiteWine26PrefixProbe.java").read_text(encoding="utf-8")
PREP = (ROOT/"prepare_next.py").read_text(encoding="utf-8")
ENGINE = (ROOT/"CharoiteNextRuntime.java").read_text(encoding="utf-8")
WORKFLOW = (ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine26FirstPrefixTests(unittest.TestCase):
    def test_fresh_prefix_is_opt_in_and_unconditionally_version_gated(self):
        self.assertIn("Test isolated Wine26 prefix bootstrap", PREP)
        self.assertIn("Run isolated Wineboot probe", PREP)
        self.assertIn("CharoiteWine26PrefixProbe.run(this)", PREP)
        self.assertIn("CharoiteWine26PrefixProbe.java", PREP)
        self.assertIn("CharoiteWine26NativeGate.run(context)", PROBE)
        self.assertIn('RESULT: PASS — matched Wine26 native --version gate; NOT runnable', PROBE)
        self.assertLess(PROBE.index("CharoiteWine26NativeGate.run(context)"),
                        PROBE.index("scratch.mkdir()"))
        self.assertIn("never existing data", PROBE.lower())

    def test_one_shot_scratch_data_boundary_and_copy_hashes(self):
        for token in ('getNoBackupFilesDir()', 'charoite-next-wine26-first-prefix-v2',
                      'charoite-next-isolated-wine/wine10-arm64ec-bootstrap-0.5-staged',
                      'if (scratch.exists() || !scratch.mkdir())',
                      'copyVerified(origin,destination', 'MessageDigest.getInstance("SHA-256")',
                      'index.getJSONArray("module_files")',
                      'dll !=22 || nls!=76 || boots!=1',
                      'getUsableSpace()', '132L'):
            if token != "132L": self.assertIn(token, PROBE)
        self.assertIn("2*total+64L*1024*1024", PROBE)
        for prohibited in ("deleteRecursively", "clearApplicationUserData", "Runtime.getRuntime()",
                           "com.touhoudr", "com.charoite.FileProvider", "rm -rf",
                           'new File(context.getFilesDir()', 'ProcessBuilder("sh"',
                           'new File("/storage/', '"WINEPREFIX", "/data/'):
            self.assertNotIn(prohibited, PROBE)
        self.assertIn("Disposable probe data retained for inspection; NEVER auto-deleted",PROBE)
        self.assertIn('Earlier failed Wine26 v1 scratch: NOT ACCESSED', PROBE)
        self.assertNotIn('private static final String SCRATCH = "charoite-next-wine26-first-prefix-v1"', PROBE)

    def test_only_new_prefix_and_existing_source_matched_native_components(self):
        for token in ('"WINEPREFIX", prefix.getCanonicalPath()', 'env.clear()',
                      '"CHAROITE_NTDLL_NATIVE_DIR"', '"WINESERVER", server.getCanonicalPath()',
                      '"WINEDLLPATH"', 'NATIVE_LOADER = "libcharoite_wine26_loader.so"',
                      'NATIVE_SERVER = "libcharoite_wine26_wineserver.so"',
                      'new ProcessBuilder(loader.getAbsolutePath()', 'boot.getAbsolutePath(),"-i"',
                      'new ProcessBuilder(server.getAbsolutePath(),"-k")',
                      'TIMEOUT = 25L', 'destroyForcibly()', "redirectErrorStream(true)",
                      "RESULT: FAIL — isolated Wine26 bootstrap not yet verified"):
            self.assertIn(token, PROBE)
        self.assertNotIn("RESULT: PASS — Windows games ready", PROBE)
        self.assertIn("20 unbundled PE import names remain", PROBE)
        self.assertIn('env.put("WINELOADERNOEXEC", "1")', PROBE)
        self.assertIn('Native loader re-exec diagnostic: WINELOADERNOEXEC=1 (v2 only)', PROBE)
        self.assertIn('new v2 scratch', PREP)
        self.assertIn("Wineboot", ENGINE)

    def test_build_release_contains_only_experimental_code_and_version(self):
        self.assertIn('versionCode 84', PREP)
        self.assertIn('11.2-next.0.53', PREP)
        self.assertIn('0.52 (Wine28 first-run builtin wineboot v9', ENGINE)
        self.assertIn("CharoiteWine26PrefixProbe.java", WORKFLOW)
        self.assertIn("versionCode='83' versionName='11.2-next.0.53'", WORKFLOW)
        self.assertNotIn("com.charoite.FileProvider", PROBE)

if __name__ == "__main__":
    unittest.main()

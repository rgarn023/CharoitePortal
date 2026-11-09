"""V26 fresh-prefix source contract. CI never launches Wine or modifies phone data."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V26DefaultInstallProbe.java").read_text()
PREP = (ROOT / "prepare_next.py").read_text()
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text()

class V26DefaultInstallContract(unittest.TestCase):
    def test_java_class_name_matches_public_file_and_ui(self):
        self.assertIn("public final class CharoiteWine29V26DefaultInstallProbe {", JAVA)
        self.assertIn("private CharoiteWine29V26DefaultInstallProbe() {}", JAVA)
        self.assertNotIn("CharoiteWine29V26InfTraceProbe", JAVA)

    def test_strict_fresh_one_shot_and_no_older_scratch(self):
        for token in (
            "charoite-next-wine29-entry-v26",
            "if (scratch.exists() || !scratch.mkdir())",
            'bootBuiltin.getAbsolutePath(),"-i"',
            "END OF SHORT V26 PREFIX SETUP SCM REPORT",
            "V26 scratch retained; NEVER retry or delete V26",
            'scBuiltin.getAbsolutePath(),"query","RpcSs"',
        ):
            self.assertIn(token, JAVA)
        self.assertEqual(JAVA.count("new ProcessBuilder("), 4)
        for banned in (
            "charoite-next-wine29-entry-v25",
            ".delete(", ".renameTo(", "clearApplicationUserData(",
            '"start","RpcSs"', '"create","RpcSs"', '"delete","RpcSs"',
            'new ProcessBuilder("/system/bin/sh"',
        ):
            self.assertNotIn(banned, JAVA)

    def test_gated_only_one_independent_source_pinned_inf_install(self):
        for token in (
            "return data.contains(\"installhinfsection defaultinstall\");",
            "boolean defaultInstallObserved = appendV26InfTraceMarkers(out, peLog);",
            "boolean setupGate = finished && exit == 0 && !expired && !overflow",
            "if (defaultInstallObserved) {",
            'File rundllBuiltin=child(lib,"rundll32.exe");',
            '"setupapi,InstallHinfSection", "DefaultInstall", "128",',
            "verifiedInf.getCanonicalPath());",
            'setupLog=child(scratch,"v26-independent-defaultinstall.log");',
            'setupExpired=System.nanoTime()-setupStart>=TimeUnit.SECONDS.toNanos(35);',
            "&& !internalCreationFail && serverBeforeControl && setupPassed) {",
            "appendV26RegistryMarkers(out, scratch);",
            "V26 helper log retained privately; no raw values or paths copied",
            'env.put("WINEDATADIR",dataDir.getCanonicalPath());',
        ):
            self.assertIn(token, JAVA)
        self.assertLess(JAVA.index("boolean setupGate"), JAVA.index("setupProc=install.start();"))
        self.assertLess(JAVA.index("setupProc=install.start();"), JAVA.index('scBuiltin.getAbsolutePath(),"query","RpcSs"'))
        self.assertLess(JAVA.index("serverProc.destroyForcibly(); serverProc.waitFor"),
                        JAVA.index("appendV26RegistryMarkers(out, scratch);"))

    def test_current_ui_identity_source_and_archival(self):
        for token in (
            'final boolean showArchivedWine29V25Execution = false;',
            "CURRENT WINE29 ACTION — V26 GATED DEFAULTINSTALL + RPCSS QUERY",
            "Test Wine29 v26 DefaultInstall + RpcSs (one-shot)",
            "Authorize ONE fresh v26 test",
            "CharoiteWine29V26DefaultInstallProbe.run(this)",
            "wine29V26Action.addView(v26HandoffButton)",
            "nextCoreCard.addView(wine29V26Action);",
            '"CharoiteWine29V26DefaultInstallProbe.java"',
            "versionCode 149",
            "11.2-next.0.118",
        ):
            self.assertIn(token, PREP)
        self.assertIn("versionCode='149' versionName='11.2-next.0.118'", WF)
        self.assertIn("WINE29_V26_EXPLICIT_DEFAULTINSTALL_SOURCE_GATE=PASS", WF)
        self.assertIn("CharoiteWine29V26DefaultInstallProbe.java legal-bundle/", WF)

if __name__ == "__main__":
    unittest.main()

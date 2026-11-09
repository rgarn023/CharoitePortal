"""V25 one-shot fresh prefix source contract. Never executes Wine in CI."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V25InfTraceProbe.java").read_text()
UI=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
class V25InfTraceContract(unittest.TestCase):
    def test_new_scratch_only_and_no_new_scm_commands(self):
        for token in ("charoite-next-wine29-entry-v25",
                      "if (scratch.exists() || !scratch.mkdir())",
                      'bootBuiltin.getAbsolutePath(),"-i"',
                      'scBuiltin.getAbsolutePath(),"query","RpcSs"',
                      "END OF SHORT V25 PREFIX SETUP SCM REPORT",
                      "V25 scratch retained; NEVER retry or delete V25",
                      "prior Wine29 v1-v24 scratch"):
            self.assertIn(token,JAVA)
        self.assertEqual(JAVA.count("new ProcessBuilder("),3)
        for banned in ("charoite-next-wine29-entry-v24",".delete(", ".renameTo(",
                       "clearApplicationUserData(", '"start","RpcSs"', '"create","RpcSs"'):
            self.assertNotIn(banned,JAVA)
    def test_trace_bounded_and_postfinal_registry_isolated(self):
        for token in ("+wineboot", "appendV25InfTraceMarkers(out, peLog);",
                      "Os.lstat(log.getAbsolutePath())","OsConstants.S_ISREG(st.st_mode)",
                      "2L*1024L*1024L", "V25 Wineboot trace channel observed:",
                      "V25 internal PreInstall command marker observed:",
                      "V25 internal DefaultInstall command marker observed:",
                      "V25 private Wineboot trace bounded scan: PASS; raw lines/paths NOT copied",
                      "appendV25RegistryMarkers(out, scratch);",
                      'env.put("WINEDATADIR",dataDir.getCanonicalPath());'):
            self.assertIn(token,JAVA)
        self.assertLess(JAVA.index("serverProc.destroyForcibly(); serverProc.waitFor"),
                        JAVA.index("appendV25RegistryMarkers(out, scratch);"))
    def test_system_opt_in_archives_v24_and_new_apk_identity(self):
        for token in ('final boolean showArchivedWine29V24Execution = false;',
                      "CURRENT WINE29 ACTION — V25 WINEBOOT INF TRACE + RPCSS QUERY",
                      "Test Wine29 v25 Wineboot INF trace + RpcSs (one-shot)",
                      "Authorize ONE fresh v25 test",
                      "CharoiteWine29V25InfTraceProbe.run(this)",
                      "wine29V25Action.addView(v25HandoffButton)",
                      "nextCoreCard.addView(wine29V25Action);",
                      "versionCode 148", "11.2-next.0.117",
                      '"CharoiteWine29V25InfTraceProbe.java"'):
            self.assertIn(token,UI)
        self.assertIn("versionCode='148' versionName='11.2-next.0.117'",WF)
        self.assertIn("WINE29_V25_WINEBOOT_INF_TRACE_SOURCE_GATE=PASS",WF)
        self.assertIn("CharoiteWine29V25InfTraceProbe.java legal-bundle/",WF)
if __name__=="__main__": unittest.main()

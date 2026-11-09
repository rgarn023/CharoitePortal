"""V27 fresh-prefix source contract; GitHub CI never runs phone Wine."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V27MappedInfProbe.java").read_text()
PREP=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
class V27MappedInfContract(unittest.TestCase):
    def test_isolated_one_shot_and_no_other_scm(self):
        for x in (
            "public final class CharoiteWine29V27MappedInfProbe {",
            "charoite-next-wine29-entry-v27",
            "if (scratch.exists() || !scratch.mkdir())",
            "V27 scratch retained; NEVER retry or delete V27",
            'bootBuiltin.getAbsolutePath(),"-i"',
            'scBuiltin.getAbsolutePath(),"query","RpcSs"',
        ): self.assertIn(x,JAVA)
        self.assertEqual(JAVA.count("new ProcessBuilder("),4)
        for x in ("charoite-next-wine29-entry-v26",".delete(", ".renameTo(",
                  "clearApplicationUserData(", '"start","RpcSs"',
                  '"create","RpcSs"', '"delete","RpcSs"'):
            self.assertNotIn(x,JAVA)
    def test_dos_mapped_verified_inf_not_unverified_unix_path(self):
        for x in (
            'File mappedInfDir=child(prefix,"drive_c/windows/inf");',
            'mkdir(mappedInfDir);',
            'File mappedInf=child(mappedInfDir,"charoite-v27.inf");',
            'stageV27SetupModule(setupImages[2],mappedInf,PINNED_WINE_INF_SHA);',
            r'"C:\\windows\\inf\\charoite-v27.inf"',
            'V27 fresh private mapped C: INF SHA-256 and containment: PASS',
            'appendV27HelperTraceMarkers(out, setupLog);',
            'V27 helper trace ARM64 DefaultInstall selection mention:',
            'V27 helper trace RpcSs service creation attempt mention:',
            'appendV27RegistryMarkers(out, scratch);',
            'env.put("WINEDATADIR",dataDir.getCanonicalPath());',
        ): self.assertIn(x,JAVA)
        self.assertLess(JAVA.index("stageV27SetupModule(setupImages[2],mappedInf"),
                        JAVA.index("setupProc=install.start();"))
        self.assertLess(JAVA.index("setupProc=install.start();"),
                        JAVA.index('scBuiltin.getAbsolutePath(),"query","RpcSs"'))
    def test_phone_action_archives_v26_and_uses_v27(self):
        for x in (
            'final boolean showArchivedWine29V26Execution = false;',
            'Test Wine29 v27 C: INF + RpcSs (one-shot)',
            'Authorize ONE fresh v27 test',
            'CharoiteWine29V27MappedInfProbe.run(this)',
            'wine29V27Action.addView(v27HandoffButton)',
            'nextCoreCard.addView(wine29V27Action);',
            '"CharoiteWine29V27MappedInfProbe.java"',
            'versionCode 150','11.2-next.0.119'
        ): self.assertIn(x,PREP)
        self.assertIn("versionCode='150' versionName='11.2-next.0.119'",WF)
        self.assertIn("WINE29_V27_MAPPED_C_INF_SOURCE_GATE=PASS",WF)
        self.assertIn("CharoiteWine29V27MappedInfProbe.java legal-bundle/",WF)
if __name__=="__main__": unittest.main()

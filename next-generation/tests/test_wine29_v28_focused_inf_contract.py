"""V28 focused SetupAPI one-shot source contract: CI never executes Wine on a phone."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V28FocusedInfProbe.java").read_text()
PREP=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
class V28FocusedInfContract(unittest.TestCase):
    def test_fresh_private_only_and_single_authorized_query(self):
        for text in (
            "public final class CharoiteWine29V28FocusedInfProbe {",
            "charoite-next-wine29-entry-v28",
            "if (scratch.exists() || !scratch.mkdir())",
            "V28 scratch retained; NEVER retry or delete V28",
            'bootBuiltin.getAbsolutePath(),"-i"',
            'scBuiltin.getAbsolutePath(),"query","RpcSs"',
            "appendV28RegistryMarkers(out, scratch);",
        ): self.assertIn(text, JAVA)
        self.assertEqual(JAVA.count("new ProcessBuilder("),4)
        for forbidden in (
            "charoite-next-wine29-entry-v27", ".delete(", ".renameTo(",
            "clearApplicationUserData(", '"create","RpcSs"', '"start","RpcSs"',
            '"delete","RpcSs"', "network.connect",
        ): self.assertNotIn(forbidden, JAVA)
    def test_bounded_targeted_setupapi_logging_and_dos_inf(self):
        for text in (
            'installEnv.put("WINEDEBUG", "-all,err+all,+setupapi");',
            'setupOverflow=setupLog.length()>4L*1024L*1024L;',
            "size<=0 || size>4L*1024L*1024L",
            "buf.size()+n>4L*1024L*1024L",
            "V28 helper trace INF open failure marker:",
            'File mappedInfDir=child(prefix,"drive_c/windows/inf");',
            'File mappedInf=child(mappedInfDir,"charoite-v28.inf");',
            'stageV28SetupModule(setupImages[2],mappedInf,PINNED_WINE_INF_SHA);',
            r'"C:\\windows\\inf\\charoite-v28.inf"',
            "V28 helper bound: 35 seconds / 4 MiB output",
        ): self.assertIn(text, JAVA)
        self.assertLess(JAVA.index("stageV28SetupModule(setupImages[2],mappedInf"),
                        JAVA.index("setupProc=install.start();"))
        self.assertLess(JAVA.index("setupProc=install.start();"),
                        JAVA.index('scBuiltin.getAbsolutePath(),"query","RpcSs"'))
    def test_ui_manifest_and_attribution(self):
        for text in (
            "final boolean showArchivedWine29V27Execution = false;",
            "Test Wine29 v28 C: INF + RpcSs (one-shot)",
            "Authorize ONE fresh v28 test",
            "CharoiteWine29V28FocusedInfProbe.run(this)",
            "wine29V28Action.addView(v28HandoffButton)",
            "nextCoreCard.addView(wine29V28Action);",
            '"CharoiteWine29V28FocusedInfProbe.java"',
            "versionCode 151", "11.2-next.0.120",
        ): self.assertIn(text, PREP)
        for text in (
            "versionCode='151' versionName='11.2-next.0.120'",
            "WINE29_V28_FOCUSED_SETUPAPI_SOURCE_GATE=PASS",
            "CharoiteWine29V28FocusedInfProbe.java legal-bundle/",
        ): self.assertIn(text, WF)
if __name__ == "__main__": unittest.main()

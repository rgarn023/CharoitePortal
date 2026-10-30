"""Next v0.38: verify 95 staged Windows data files before native Wine --version only."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
GATE=(ROOT/"CharoiteWineBootstrapGate.java").read_text(encoding="utf-8")
STAGE=(ROOT/"CharoiteWineIsolatedStage.java").read_text(encoding="utf-8")
LOADER=(ROOT/"CharoiteWineNativeProbe.java").read_text(encoding="utf-8")
SERVER=(ROOT/"CharoiteWineServerProbe.java").read_text(encoding="utf-8")
PREP=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WORKFLOW=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
ENGINE=(ROOT/"CharoiteNextRuntime.java").read_text(encoding="utf-8")

class NativeGateContract(unittest.TestCase):
    def test_gate_checks_staged_data_then_loader_then_server(self):
        verify=GATE.index("CharoiteWineIsolatedStage.verifyOnly(context)")
        loader=GATE.index("CharoiteWineNativeProbe.run(context)")
        server=GATE.index("CharoiteWineServerProbe.run(context)")
        self.assertLess(verify,loader)
        self.assertLess(loader,server)
        for s in ("RESULT: BLOCKED — staged PE/NLS prerequisites failed",
                  "RESULT: BLOCKED — native Wine loader did not pass",
                  "RESULT: BLOCKED — native wineserver did not pass",
                  "RESULT: PASS — version-only prerequisites, NOT a runnable Wine environment",
                  "Native ELF startup version gate: PASS",
                  "wineboot / FEX / graphics: NOT ATTEMPTED"):
            # The last assertion is matched as part of the scope line.
            if s=="wineboot / FEX / graphics: NOT ATTEMPTED":
                self.assertIn("wineboot / FEX / graphics: NOT ATTEMPTED",GATE)
            else:
                self.assertIn(s,GATE)

    def test_reverify_is_read_only_fail_closed_and_reuses_v037_stage(self):
        a=STAGE.index("public static String verifyOnly(Context context)")
        b=STAGE.index("public static String run(Context context)",a)
        read=STAGE[a:b]
        for s in ('validatedInventory(context)', 'if (pending.exists())',
                  'verifyFiles(complete, index.getJSONArray("files"))',
                  "RESULT: PASS — staged module data verified; NOT runnable"):
            self.assertIn(s,read)
        for s in (".mkdir(", ".mkdirs(", ".renameTo(", "FileOutputStream",
                  "ProcessBuilder", "delete(", "setExecutable("):
            self.assertNotIn(s,read)
        for source in (GATE,LOADER,SERVER):
            self.assertNotIn("wineboot.exe",source)
            self.assertNotIn("clearApplicationUserData",source)
            self.assertNotIn("deleteRecursively",source)
        self.assertIn('new ProcessBuilder(loader.getAbsolutePath(), "--version")',LOADER)
        self.assertIn('new ProcessBuilder(server.getAbsolutePath(), "--version")',SERVER)
        self.assertIn("env.clear()",LOADER)
        self.assertIn("env.clear()",SERVER)

    def test_v038_ui_has_explicit_consent_and_never_autostarts(self):
        for s in ("CharoiteWineBootstrapGate.java",
                  "Test native Wine startup prerequisites",
                  "Run version tests",
                  "CharoiteWineBootstrapGate.run(this)",
                  "versionCode 71","11.2-next.0.40"):
            self.assertIn(s,PREP)
        self.assertIn('0.40 (matched Wine26 native --version gate',ENGINE)
        self.assertIn("versionCode='71' versionName='11.2-next.0.40'",WORKFLOW)
        self.assertIn("CharoiteWineBootstrapGate.java legal-bundle",WORKFLOW)

if __name__=="__main__":
    unittest.main()

"""V17 source-only contract: one new control + sc.exe, no old-prefix reads."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROBE=(ROOT/"CharoiteWine29V17ControlCompareProbe.java").read_text(encoding="utf-8")
UI=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class V17ControlCompareContract(unittest.TestCase):
    def test_fresh_slot_isolation(self):
        for required in ("charoite-next-wine29-entry-v17",
                         "if (scratch.exists() || !scratch.mkdir())",
                         "verifyV6Native(context);", "verifyV7Services(context)",
                         "verifyV8Userenv(context)", "verifyV17Sc(context)",
                         "v17-wine-direct-init.log","v17-foreground-wineserver.log",
                         "v17-independent-wineboot-help.log","v17-sc-entry.log",
                         "END OF SHORT V17 ENTRY REPORT",
                         "Handoff: https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md"):
            with self.subTest(required=required):
                self.assertIn(required,PROBE)
        for forbidden in ("charoite-next-wine29-entry-v16",
                          "charoite-next-wine29-entry-v15",
                          'clearApplicationUserData(','.delete(','renameTo('):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,PROBE)
    def test_one_control_before_sc_and_fail_closed(self):
        for required in ("controlProc=control.start();","controlProc.waitFor(",
                         "V17 control native exit:","V17 control output bytes:",
                         "V17 foreground server alive after control:",
                         "server exited after control; sc.exe intentionally NOT attempted",
                         "scProc=entry.start();","V17 sc.exe subprocess exit:",
                         "sc.exe PE mapping: UNVERIFIED",
                         'controlEnv.get("WINELOADERNOEXEC")',
                         'scEnv.get("WINELOADERNOEXEC")'):
            with self.subTest(required=required): self.assertIn(required,PROBE)
        self.assertLess(PROBE.index("controlProc=control.start();"),
                        PROBE.index("scProc=entry.start();"))
        self.assertNotIn('"query"',' '.join(x for x in PROBE.splitlines() if "new ProcessBuilder" in x))
        self.assertNotIn("RESULT: PASS — sc.exe",PROBE)
    def test_system_consent_and_archive(self):
        for required in ("final boolean showArchivedWine29V16Execution = false;",
                         "final boolean showArchivedWine29V16ReadOnly = false;",
                         "CURRENT WINE29 ACTION — V17 CONTROL COMPARISON",
                         "Test Wine29 v17 control vs sc.exe (one-shot)",
                         "Authorize ONE fresh v17 test",
                         "Cancel — do not execute",
                         "CharoiteWine29V17ControlCompareProbe.run(this)",
                         "wine29V17Action.addView(v17HandoffButton);",
                         "nextCoreCard.addView(wine29V17Action);",
                         '"CharoiteWine29V17ControlCompareProbe.java"',
                         "versionCode 139","11.2-next.0.108"):
            with self.subTest(required=required):self.assertIn(required,UI)
    def test_ci_contract_no_device_execution(self):
        for required in ("test_wine29_v17_control_compare_contract.py",
                         "WINE29_V17_ISOLATED_CONTROL_COMPARISON_SOURCE_GATE=PASS",
                         "WINE29_V17_PHONE_EXECUTION=NOT_ATTEMPTED_IN_CI",
                         "cp next-generation/CharoiteWine29V17ControlCompareProbe.java legal-bundle/CharoiteWine29V17ControlCompareProbe.java",
                         "versionCode='139' versionName='11.2-next.0.108'"):
            with self.subTest(required=required):self.assertIn(required,WF)

if __name__=="__main__":unittest.main()

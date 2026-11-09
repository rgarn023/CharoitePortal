"""Source-only V18 server lifecycle: one new private prefix; no second PE or SCM."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = (ROOT / "CharoiteWine29V18ServerIdleProbe.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class V18IdleLifecycleContract(unittest.TestCase):
    def test_only_fresh_private_scratch_and_exact_sources(self):
        for required in (
            "charoite-next-wine29-entry-v18", "if (scratch.exists() || !scratch.mkdir())",
            "verifyV6Native(context);", "verifyV7Services(context)",
            "verifyV8Userenv(context)", "verifyV17Sc(context)",
            "v18-wine-direct-init.log", "v18-foreground-wineserver.log",
            "END OF SHORT V18 IDLE REPORT",
            "Handoff: https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md",
            "copyVerified(", "V18 private foreground server intentionally terminated",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PROBE)
        for forbidden in (
            "charoite-next-wine29-entry-v17", "charoite-next-wine29-entry-v16",
            "clearApplicationUserData(", ".delete(", "renameTo(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, PROBE)

    def test_only_server_and_one_direct_wineboot(self):
        self.assertEqual(PROBE.count("new ProcessBuilder("), 2)
        for required in (
            'new ProcessBuilder(server.getAbsolutePath(),"-f","-d")',
            'new ProcessBuilder(loader.getAbsolutePath(),',
            'bootBuiltin.getAbsolutePath(),"-i"',
            "WINELOADERNOEXEC",
            "idleCheckpointsMs = {0L,1000L,3000L,8000L,12000L}",
            "serverProc.waitFor(remaining,TimeUnit.MILLISECONDS)",
            "V18 server alive BEFORE intentional probe finalization:",
            "V18 observed foreground server native exit:",
            "V18 independent Wineboot --help: NOT ATTEMPTED",
            "V18 independent sc.exe / SCM: NOT ATTEMPTED",
        ):
            with self.subTest(required=required):
                self.assertIn(required, PROBE)
        for forbidden in ("controlProc", "scProc", "control.start();", "entry.start();",
                          'new ProcessBuilder(loader.getAbsolutePath(), "C:',
                          "RESULT: PASS — SCM"):
            self.assertNotIn(forbidden, PROBE)

    def test_system_consent_and_retired_v17(self):
        for required in (
            'final boolean showArchivedWine29V17Execution = false;',
            'final boolean showArchivedWine29V17ReadOnly = false;',
            'CURRENT WINE29 ACTION — V18 SERVER IDLE LIFECYCLE',
            'Test Wine29 v18 server lifecycle (one-shot)',
            'Authorize ONE fresh v18 test', 'Cancel — do not execute',
            'CharoiteWine29V18ServerIdleProbe.run(this)',
            'wine29V18Action.addView(v18HandoffButton);',
            'nextCoreCard.addView(wine29V18Action);',
            '"CharoiteWine29V18ServerIdleProbe.java"',
            'versionCode 146', '11.2-next.0.115',
        ):
            with self.subTest(required=required):
                self.assertIn(required, UI)

    def test_ci_does_not_run_phone_wine(self):
        for required in (
            'test_wine29_v18_server_idle_contract.py',
            'WINE29_V18_IDLE_LIFECYCLE_SOURCE_GATE=PASS',
            'WINE29_V18_PHONE_EXECUTION=NOT_ATTEMPTED_IN_CI',
            'cp next-generation/CharoiteWine29V18ServerIdleProbe.java legal-bundle/CharoiteWine29V18ServerIdleProbe.java',
            "versionCode='146' versionName='11.2-next.0.115'",
        ):
            with self.subTest(required=required):
                self.assertIn(required, WF)

if __name__ == "__main__":
    unittest.main()

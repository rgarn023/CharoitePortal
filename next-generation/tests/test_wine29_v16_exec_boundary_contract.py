"""V16 source-only contract: isolated Android sc.exe exec boundary, explicit consent."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V16ExecBoundaryProbe.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class V16ExecBoundaryContract(unittest.TestCase):
    def test_fresh_single_use_experiment_and_prior_scratch_isolation(self):
        for good in (
            "charoite-next-wine29-entry-v16",
            "if (scratch.exists() || !scratch.mkdir())",
            "V16 prior Wine29 v1-v15 scratch directories: NOT ACCESSED",
            "V16 private Windows system32/sc.exe SHA-256: PASS",
            "C:\\windows\\system32\\sc.exe",
            'scEnv.get("WINELOADERNOEXEC")',
            'scProc=entry.start();',
            "TimeUnit.SECONDS.toNanos(12)",
            "V16 SCM query / service operation: NOT ATTEMPTED",
            "END OF SHORT V16 ENTRY REPORT",
        ):
            with self.subTest(good=good):
                self.assertIn(good, JAVA)
        for forbidden in (
            "charoite-next-wine29-entry-v15",
            "charoite-next-wine29-entry-v14",
            "clearApplicationUserData(", ".delete(", "renameTo(",
            'scBuiltin.getAbsolutePath(),"query"',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, JAVA)

    def test_independent_native_boundary_without_unproven_mapping_claim(self):
        for good in (
            "V16 Android ProcessBuilder.start: RETURNED PROCESS",
            "V16 Android ProcessBuilder.start: THREW",
            "V16 Android exec errno:",
            "V16 Android native launch acceptance latency ms:",
            "V16 native process elapsed ms (start to bounded exit/stop):",
            "V16 foreground server alive after native process accepted:",
            "V16 foreground server alive at native process completion:",
            "ProcessBuilder success/exit 127 cannot establish Windows PE entry",
            "Handoff: https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md",
        ):
            with self.subTest(good=good):
                self.assertIn(good, JAVA)
        self.assertNotIn("RESULT: PASS — sc.exe", JAVA)

    def test_system_instructions_beside_only_active_one_shot(self):
        for good in (
            "final boolean showArchivedWine29V15Execution = false;",
            "final boolean showArchivedWine29V15ReadOnly = false;",
            "CURRENT WINE29 ACTION — V16 NATIVE EXEC BOUNDARY",
            "Test Wine29 v16 sc.exe native boundary (one-shot)",
            "Authorize ONE fresh v16 test",
            "Cancel — do not execute",
            "CharoiteWine29V16ExecBoundaryProbe.run(this)",
            "wine29V16Action.addView(wine29V16Exec);",
            "wine29V16Action.addView(v16HandoffButton);",
            "nextCoreCard.addView(wine29V16Action);",
            "The handoff URL ",
            '"CharoiteWine29V16ExecBoundaryProbe.java"',
            "versionCode 137", "11.2-next.0.106",
        ):
            with self.subTest(good=good):
                self.assertIn(good, UI)

    def test_ci_gate_not_phone_execution(self):
        for good in (
            "test_wine29_v16_exec_boundary_contract.py",
            "WINE29_V16_ISOLATED_EXEC_BOUNDARY_SOURCE_GATE=PASS",
            "WINE29_V16_PHONE_EXECUTION=NOT_ATTEMPTED_IN_CI",
            "cp next-generation/CharoiteWine29V16ExecBoundaryProbe.java legal-bundle/CharoiteWine29V16ExecBoundaryProbe.java",
            "versionCode='137' versionName='11.2-next.0.106'",
        ):
            with self.subTest(good=good):
                self.assertIn(good, WF)

if __name__ == "__main__":
    unittest.main()

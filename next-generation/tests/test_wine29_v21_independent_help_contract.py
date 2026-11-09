"""Source-only V21: isolated init + one independent Wineboot help with persistent server."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V21IndependentHelpProbe.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine29V21IndependentHelpContract(unittest.TestCase):
    def test_fresh_isolation_and_exact_process_count(self):
        self.assertIn('public final class CharoiteWine29V21IndependentHelpProbe', JAVA)
        self.assertIn('charoite-next-wine29-entry-v21', JAVA)
        self.assertNotIn('charoite-next-wine29-entry-v20', JAVA)
        self.assertIn('if (scratch.exists() || !scratch.mkdir())', JAVA)
        self.assertIn('new ProcessBuilder(server.getAbsolutePath(),"-f","-d","-p")', JAVA)
        self.assertIn('bootBuiltin.getAbsolutePath(),"-i"', JAVA)
        self.assertIn('bootBuiltin.getAbsolutePath(),"--help"', JAVA)
        self.assertEqual(JAVA.count('new ProcessBuilder('), 3)
        for forbidden in ('scProc', 'clearApplicationUserData(', '.delete(', '.renameTo(',
                          'new ProcessBuilder(scBuiltin', 'Runtime.getRuntime('):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, JAVA)

    def test_strict_gating_bounded_control_and_preserved_logs(self):
        for expected in (
            'finished && exit==0 && !expired && !overflow',
            '&& !internalCreationFail && serverBeforeControl',
            'controlProc=h.start();',
            'TimeUnit.SECONDS.toNanos(20)',
            'v21-independent-wineboot-help.log',
            'controlLog.length()>2L*1024L*1024L',
            'if (controlProc!=null&&controlProc.isAlive())',
            'V21 independent sc.exe / SCM: NOT ATTEMPTED',
            'V21 POST-FINALIZATION retained ',
            'contents NOT read',
            'END OF SHORT V21 INDEPENDENT HELP REPORT',
            'V21 scratch retained; NEVER retry or delete V21'):
            with self.subTest(expected=expected):
                self.assertIn(expected, JAVA)

    def test_owner_consent_ui_and_packaging(self):
        for expected in ('final boolean showArchivedWine29V20Execution = false;',
                         'CURRENT WINE29 ACTION — V21 INDEPENDENT WINEBOOT HELP',
                         'Test Wine29 v21 independent help (one-shot)',
                         'Authorize ONE fresh v21 test',
                         'Cancel — do not execute',
                         'CharoiteWine29V21IndependentHelpProbe.run(this)',
                         'nextCoreCard.addView(wine29V21Action);',
                         'wine29V21Action.addView(v21HandoffButton);',
                         '"CharoiteWine29V21IndependentHelpProbe.java"',
                         'versionCode 144', '11.2-next.0.113'):
            with self.subTest(expected=expected):
                self.assertIn(expected, UI)

    def test_workflow_and_attribution(self):
        for expected in ('test_wine29_v21_independent_help_contract.py',
                         'WINE29_V21_INDEPENDENT_HELP_SOURCE_GATE=PASS',
                         'WINE29_V21_PHONE_EXECUTION=NOT_ATTEMPTED_IN_CI',
                         'cp next-generation/CharoiteWine29V21IndependentHelpProbe.java legal-bundle/CharoiteWine29V21IndependentHelpProbe.java',
                         "versionCode='144' versionName='11.2-next.0.113'"):
            with self.subTest(expected=expected):
                self.assertIn(expected, WF)

if __name__ == "__main__":
    unittest.main()

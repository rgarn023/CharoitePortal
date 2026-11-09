"""Source-only V22: one fresh private server, Wineboot init, independent SCM query."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V22ScmQueryProbe.java").read_text(encoding="utf-8")
UI = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine29V22ScmQueryContract(unittest.TestCase):
    def test_private_one_shot_and_exact_process_allowlist(self):
        self.assertIn('charoite-next-wine29-entry-v22', JAVA)
        self.assertNotIn('charoite-next-wine29-entry-v21', JAVA)
        self.assertIn('if (scratch.exists() || !scratch.mkdir())', JAVA)
        self.assertIn('new ProcessBuilder(server.getAbsolutePath(),"-f","-d","-p")', JAVA)
        self.assertIn('bootBuiltin.getAbsolutePath(),"-i"', JAVA)
        self.assertIn('scBuiltin.getAbsolutePath(),"query","RpcSs"', JAVA)
        self.assertEqual(JAVA.count('new ProcessBuilder('), 3)
        for forbidden in ('"create"', '"start"', '"stop"', '"delete"', 'clearApplicationUserData(',
                          '.delete(', '.renameTo(', 'Runtime.getRuntime(', '"--help");'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, JAVA)

    def test_gated_query_status_markers_and_preserved_evidence(self):
        for required in ('finished && exit==0 && !expired && !overflow',
                         '&& !internalCreationFail && serverBeforeControl',
                         'controlProc=h.start();', 'TimeUnit.SECONDS.toNanos(20)',
                         'v22-independent-sc-rpcss-query.log',
                         'V22 SCM output identifies RpcSs',
                         'V22 SCM output includes service state',
                         'V22 SCM error 1060 marker observed',
                         'V22 SCM error 1722 marker observed',
                         'helpExit==0 && helpOutput && scmState',
                         'serverProc.isAlive()', 'V22 POST-FINALIZATION retained ',
                         'contents NOT read', 'V22 scratch retained; NEVER retry or delete V22',
                         'END OF SHORT V22 SCM QUERY REPORT'):
            with self.subTest(required=required):
                self.assertIn(required, JAVA)

    def test_archived_v21_and_new_system_consent(self):
        for required in ('final boolean showArchivedWine29V21Execution = false;',
                         'CURRENT WINE29 ACTION — V22 INDEPENDENT SC.EXE RPCSS QUERY',
                         'Test Wine29 v22 SCM query (one-shot)',
                         'Authorize ONE fresh v22 test',
                         'Cancel — do not execute',
                         'CharoiteWine29V22ScmQueryProbe.run(this)',
                         'nextCoreCard.addView(wine29V22Action);',
                         '"CharoiteWine29V22ScmQueryProbe.java"',
                         'versionCode 146','11.2-next.0.115'):
            with self.subTest(required=required):
                self.assertIn(required, UI)

    def test_ci_and_attribution(self):
        for required in ('test_wine29_v22_scm_query_contract.py',
                         'WINE29_V22_SCM_QUERY_SOURCE_GATE=PASS',
                         'WINE29_V22_PHONE_EXECUTION=NOT_ATTEMPTED_IN_CI',
                         'cp next-generation/CharoiteWine29V22ScmQueryProbe.java legal-bundle/CharoiteWine29V22ScmQueryProbe.java',
                         "versionCode='146' versionName='11.2-next.0.115'"):
            with self.subTest(required=required):
                self.assertIn(required, WF)

if __name__ == "__main__":
    unittest.main()

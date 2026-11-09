"""V23: verified Wine INF and ARM64 setup tools, independent RpcSs query, NEW one-shot prefix."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V23SetupProbe.java").read_text(encoding="utf-8")
STAGE=(ROOT/"stage_wine29_v23_setup.py").read_text(encoding="utf-8")
UI=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine29V23SetupContract(unittest.TestCase):
    def test_one_fresh_private_prefix_and_no_old_prefix(self):
        for required in ('public final class CharoiteWine29V23SetupProbe',
                         'charoite-next-wine29-entry-v23',
                         'if (scratch.exists() || !scratch.mkdir())',
                         'new ProcessBuilder(server.getAbsolutePath(),"-f","-d","-p")',
                         'bootBuiltin.getAbsolutePath(),"-i"',
                         'scBuiltin.getAbsolutePath(),"query","RpcSs"',
                         'finished && exit==0 && !expired && !overflow',
                         '&& !internalCreationFail && serverBeforeControl',
                         'END OF SHORT V23 PREFIX SETUP SCM REPORT',
                         'V23 scratch retained; NEVER retry or delete V23'):
            with self.subTest(required=required):
                self.assertIn(required,JAVA)
        self.assertEqual(JAVA.count('new ProcessBuilder('),3)
        self.assertNotIn('charoite-next-wine29-entry-v22',JAVA)
        for disallowed in ('clearApplicationUserData(','.delete(','.renameTo(',
                           'Runtime.getRuntime(', 'new ProcessBuilder("sc.exe"',
                           '"create","RpcSs"', '"start","RpcSs"'):
            with self.subTest(disallowed=disallowed):
                self.assertNotIn(disallowed,JAVA)

    def test_setup_provenance_hashes_inf_and_sandbox_env(self):
        for required in (
            'verifyV23Setup(context)',
            '42552476223L','13645473200L',
            'b6d180240adf2e8c354e9a5a016c828ca04a9911',
            '6d86ac6848e81af2190074c0e93f2ecf4aa6fc41cb7a72d15a55dc79d55b8581',
            '8dce8c98e0c6e443987ae810efbc3e15c23e9947583c5a00e713cf58124316ee',
            '5af9d9557d6a12cb9a91c2fb3cb2cd33119e9c3c30bad66c7b1b122ef30694ff',
            '5c7a7041399370937bdaaec11bac8ab64b910d6a1877b6afb582ad1d6a2f894a',
            'AddService=RpcSs', 'DefaultInstall.ntarm64.Services',
            'stageV23SetupModule(setupImages[0],child(lib,"rundll32.exe")',
            'stageV23SetupModule(setupImages[1],child(lib,"rpcss.exe")',
            'stageV23SetupModule(setupImages[2],verifiedInf',
            'env.put("WINEDATADIR",dataDir.getCanonicalPath());',
            'V23 PE trace rundll32.exe mention',
            'V23 PE trace rpcss.exe mention',
            'V23 PE trace wine.inf missing warning'):
            with self.subTest(required=required):
                self.assertIn(required,JAVA)

    def test_source_only_stage_is_additive_and_pinned(self):
        for required in ('RUN=42552476223','ARTIFACT=13645473200',
                         'prior_v9_sc_unchanged','wine_inf','rundll32','rpcss',
                         'dest.exists()','source_candidate_only',
                         'wine_executed":False','device_tested":False',
                         'ROOT="charoite-next/wine29-v23-setup"'):
            with self.subTest(required=required):
                self.assertIn(required,STAGE)
        self.assertNotIn('charoite-next-wine29-entry-v22',STAGE)
        self.assertNotIn('subprocess',STAGE)

    def test_system_ui_consent_and_build_checks(self):
        for required in ('final boolean showArchivedWine29V22Execution = false;',
                         'CURRENT WINE29 ACTION — V23 PREFIX SETUP AND RPCSS QUERY',
                         'Test Wine29 v23 prefix setup + RpcSs (one-shot)',
                         'Authorize ONE fresh v23 test','Cancel — do not execute',
                         'CharoiteWine29V23SetupProbe.run(this)',
                         'nextCoreCard.addView(wine29V23Action);',
                         'wine29V23Action.addView(v23HandoffButton)',
                         '"CharoiteWine29V23SetupProbe.java"',
                         'versionCode 146','11.2-next.0.115'):
            with self.subTest(required=required): self.assertIn(required,UI)
        for required in ('stage_wine29_v23_setup.py',
                         'Wine29-V23-Pinned-Prefix-Setup-Source-Only-NOT-APK',
                         'test_wine29_v23_setup_contract.py',
                         'WINE29_V23_PREFIX_SETUP_SOURCE_GATE=PASS',
                         'WINE29_V23_SIGNED_APK_PINNED_SETUP_AND_INF_SHA256=PASS',
                         'WINE29_V23_PHONE_EXECUTION=NOT_ATTEMPTED_IN_CI',
                         "versionCode='146' versionName='11.2-next.0.115'",
                         'cp next-generation/CharoiteWine29V23SetupProbe.java legal-bundle/CharoiteWine29V23SetupProbe.java'):
            with self.subTest(required=required): self.assertIn(required,WF)

if __name__=="__main__":
    unittest.main()

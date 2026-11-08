"""Source-only: V20 runs one fresh persistent server + Wineboot under explicit consent."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V20PersistentIdleProbe.java").read_text(encoding="utf-8")
OLD=(ROOT/"CharoiteWine29V18ServerIdleProbe.java").read_text(encoding="utf-8")
UI=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
class V20PersistentIdleContract(unittest.TestCase):
    def test_server_persistence_and_isolation(self):
        self.assertIn('new ProcessBuilder(server.getAbsolutePath(),"-f","-d")',OLD)
        self.assertIn('new ProcessBuilder(server.getAbsolutePath(),"-f","-d","-p")',JAVA)
        self.assertEqual(JAVA.count('new ProcessBuilder('),2)
        for x in ('public final class CharoiteWine29V20PersistentIdleProbe',
                  'charoite-next-wine29-entry-v20','v20-foreground-wineserver.log',
                  'v20-wine-direct-init.log','bootBuiltin.getAbsolutePath(),"-i"',
                  'idleCheckpointsMs = {0L,1000L,3000L,8000L,12000L}',
                  'serverProc.waitFor(remaining,TimeUnit.MILLISECONDS)',
                  'actual elapsed ','WINELOADERNOEXEC',
                  'V20 independent sc.exe / SCM: NOT ATTEMPTED',
                  'END OF SHORT V20 PERSISTENCE REPORT'):
            with self.subTest(x=x):self.assertIn(x,JAVA)
        for x in ('charoite-next-wine29-entry-v18','charoite-next-wine29-entry-v17',
                  'controlProc','scProc','clearApplicationUserData(','.delete(','renameTo('):
            with self.subTest(x=x):self.assertNotIn(x,JAVA)
    def test_ui_consent_and_archived_history(self):
        for x in ('final boolean showArchivedWine29V18Execution = false;',
                  'final boolean showArchivedWine29V18ReadOnly = false;',
                  'CURRENT WINE29 ACTION — V20 PERSISTENT SERVER IDLE',
                  'Test Wine29 v20 persistent idle (one-shot)',
                  'Authorize ONE fresh v20 test','Cancel — do not execute',
                  'wine29V20Exec.setEnabled(false); // one-shot remains disabled in this Activity',
                  'CharoiteWine29V20PersistentIdleProbe.run(this)',
                  'nextCoreCard.addView(wine29V20Action);',
                  'wine29V20Action.addView(v20HandoffButton);',
                  '"CharoiteWine29V20PersistentIdleProbe.java"',
                  'versionCode 143','11.2-next.0.112'):
            with self.subTest(x=x):self.assertIn(x,UI)
    def test_ci_and_license(self):
        for x in ('test_wine29_v20_persistent_idle_contract.py',
                  'WINE29_V20_PERSISTENT_IDLE_SOURCE_GATE=PASS',
                  'WINE29_V20_PHONE_EXECUTION=NOT_ATTEMPTED_IN_CI',
                  'cp next-generation/CharoiteWine29V20PersistentIdleProbe.java legal-bundle/CharoiteWine29V20PersistentIdleProbe.java',
                  "versionCode='143' versionName='11.2-next.0.112'"):
            with self.subTest(x=x):self.assertIn(x,WF)
if __name__=="__main__":unittest.main()

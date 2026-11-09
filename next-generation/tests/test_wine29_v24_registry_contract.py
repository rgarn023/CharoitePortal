"""V24 new private prefix, one SCM query, bounded post-finalized registry markers."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V24RegistryProbe.java").read_text()
UI=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
class V24Contract(unittest.TestCase):
    def test_isolation_and_no_writes_to_old_prefix(self):
        for token in ('charoite-next-wine29-entry-v24','if (scratch.exists() || !scratch.mkdir())',
                      'bootBuiltin.getAbsolutePath(),"-i"','scBuiltin.getAbsolutePath(),"query","RpcSs"',
                      'END OF SHORT V24 PREFIX SETUP SCM REPORT','V24 scratch retained; NEVER retry or delete V24'):
            self.assertIn(token,JAVA)
        self.assertEqual(3,JAVA.count('new ProcessBuilder('))
        for token in ('charoite-next-wine29-entry-v23','.delete(','.renameTo(',
                      'clearApplicationUserData(','"start","RpcSs"','"create","RpcSs"'):
            self.assertNotIn(token,JAVA)
    def test_postfinal_registry_bounded(self):
        for token in ('appendV24RegistryMarkers(StringBuilder out, File scratch)',
                      'File file = child(prefix, "system.reg");',
                      'Os.lstat(file.getAbsolutePath())','OsConstants.S_ISREG(st.st_mode)',
                      '1024L*1024L','appendV24RegistryMarkers(out, scratch);',
                      'V24 POST-FINALIZATION exact RpcSs service-root section:',
                      'V24 registry raw values, keys, identities, paths NOT copied to report'):
            self.assertIn(token,JAVA)
        self.assertLess(JAVA.index('serverProc.destroyForcibly(); serverProc.waitFor'),
                        JAVA.index('appendV24RegistryMarkers(out, scratch);'))
    def test_pinned_assets_system_button_and_ci(self):
        for token in ('wine29-v23-setup/setup-index.json',
                      'env.put("WINEDATADIR",dataDir.getCanonicalPath());','+setupapi,+service'):
            self.assertIn(token,JAVA)
        for token in ('showArchivedWine29V23Execution = false;',
                      'Test Wine29 v24 RpcSs registry diagnostic (one-shot)',
                      'Authorize ONE fresh v24 test','CharoiteWine29V24RegistryProbe.run(this)',
                      'wine29V24Action.addView(v24HandoffButton)',
                      'nextCoreCard.addView(wine29V24Action);',
                      '"CharoiteWine29V24RegistryProbe.java"',
                      'versionCode 147','11.2-next.0.116'):
            self.assertIn(token,UI)
        self.assertIn('WINE29_V24_RPCSS_REGISTRY_SOURCE_GATE=PASS',WF)
        self.assertIn('CharoiteWine29V24RegistryProbe.java legal-bundle/',WF)
if __name__=="__main__": unittest.main()

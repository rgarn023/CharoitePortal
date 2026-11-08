"""V4 explicit, fresh-scratch, one-shot Wine29 direct -i contract."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V4DirectInitProbe.java").read_text(encoding="utf-8")
UI=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine29V4DirectInitContract(unittest.TestCase):
 def test_one_shot_source_verification_and_prefix_isolation(self):
  for token in (
   'charoite-next-wine29-direct-init-v4','private static final String PACKAGE = "com.charoitx"',
   'CharoiteWine29Sealed012PePreflight.run(context)','CharoiteWine29Sealed012Stage.verifyOnly(context)',
   'getNoBackupFilesDir()', 'if (scratch.exists() || !scratch.mkdir())',
   'bootBuiltin.getAbsolutePath(),"-i"', 'bootBuiltin.getCanonicalFile().getParentFile()',
   'kernel.getCanonicalFile().getParentFile()', 'copyVerified(child(staged,name)',
   'WINELOADERNOEXEC', 'WINEDLLPATH','CHAROITE_WINE29_NATIVE_DIR',
   'CHAROITE_WINE29_PE_DIR','CHAROITE_WINE29_DATA_DIR',
   'WINEPREFIX','TimeUnit.SECONDS.toNanos(45)',
   'prefix,"drive_c"','prefix,"system.reg"','prefix,"user.reg"',
   'serverProc.destroyForcibly()','peProc.destroyForcibly()',
   'source-verified wineboot.exe -i ONLY','sanitizeLog','NEVER rerun/delete v4',
  ):
   with self.subTest(token=token):self.assertIn(token,JAVA)
  self.assertLess(JAVA.index('CharoiteWine29Sealed012Stage.verifyOnly(context)'),JAVA.index('scratch.mkdir()'))
  for forbidden in (
   'charoite-next-wine29-pe-dir-v3','charoite-next-wine29-bootstrap-v2',
   'charoite-next-wine29-pe-help-v1','env.put("WINEBOOTSTRAPMODE"',
   'bootBuiltin.getAbsolutePath(),"--help"','Runtime.getRuntime(',
   '.delete(','.renameTo(', 'deleteOnExit(','clearApplicationUserData'
  ):
   with self.subTest(forbidden=forbidden):self.assertNotIn(forbidden,JAVA)

 def test_explicit_user_consent_and_archiving(self):
  for tok in (
    '"CharoiteWine29V4DirectInitProbe.java"',
    'wine29V4DirectInit.setText("Wine29 v4 direct prefix initialization (one-shot)")',
    'setPositiveButton("Authorize ONE new v4 -i test"',
    'setNegativeButton("Cancel — do not execute", null)',
    'CharoiteWine29V4DirectInitProbe.run(this)',
    'nextCoreCard.addView(wine29V4DirectInit);',
    'final boolean showArchivedWine29V3Execution = false;',
    '11.2-next.0.95','versionCode 126',
  ):
   with self.subTest(tok=tok):self.assertIn(tok,UI)
  self.assertNotIn('CharoiteWine29V4DirectInitProbe.run(this)',UI.split('wine29V4DirectInit.setOnClickListener(v ->')[0])

 def test_ci_and_licenses(self):
  self.assertIn("test_wine29_v4_direct_init_contract.py",WF)
  self.assertIn("WINE29_V4_ONE_SHOT_DIRECT_INIT_CONSENT=PASS",WF)
  self.assertIn("cp next-generation/CharoiteWine29V4DirectInitProbe.java legal-bundle/CharoiteWine29V4DirectInitProbe.java",WF)
  self.assertIn("versionCode='126' versionName='11.2-next.0.95'",WF)
if __name__=="__main__":
 unittest.main()

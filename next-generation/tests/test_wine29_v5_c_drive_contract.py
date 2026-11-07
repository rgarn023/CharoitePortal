"""Wine29 v5 C: mapping must be new scratch, explicitly consented, never an old-prefix mutation."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"CharoiteWine29V5DriveCProbe.java").read_text(encoding="utf-8")
UI=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine29V5CDriveContracts(unittest.TestCase):
 def test_safe_one_shot_c_mapping_and_sealed_cohort(self):
  for token in (
   'private static final String PACKAGE = "com.charoitx"',
   'charoite-next-wine29-c-drive-v5',
   'CharoiteWine29Sealed012PePreflight.run(context)',
   'CharoiteWine29Sealed012Stage.verifyOnly(context)',
   'getNoBackupFilesDir()', 'if (scratch.exists() || !scratch.mkdir())',
   'prepareFreshDriveC(prefix)', 'if (disk.exists() || dos.exists())',
   'mkdir(disk);', 'mkdir(dos);', 'Os.symlink("../drive_c",link.getAbsolutePath())',
   'OsConstants.S_ISLNK(stat.st_mode)', 'Os.readlink(link.getAbsolutePath())',
   'V5 PRESEEDED private drive_c: true (not a Wine result)',
   'V5 Windows/users/program-file folders NOT precreated: true',
   'bootBuiltin.getAbsolutePath(),"-i"',
   'bootBuiltin.getCanonicalFile().getParentFile()',
   'kernel.getCanonicalFile().getParentFile()',
   'child(prefix,"drive_c/windows").isDirectory()',
   'child(prefix,"drive_c/windows/system32").isDirectory()',
   'child(prefix,"drive_c/users").isDirectory()',
   'child(prefix,"drive_c/users/xuser/AppData").isDirectory()',
   'WINELOADERNOEXEC','WINEDLLPATH','CHAROITE_WINE29_NATIVE_DIR',
   'CHAROITE_WINE29_PE_DIR','CHAROITE_WINE29_DATA_DIR',
   'env.clear()', 'TimeUnit.SECONDS.toNanos(45)',
   'serverProc.destroyForcibly()','peProc.destroyForcibly()',
   'NEVER rerun/delete v5'
  ):
   with self.subTest(token=token):self.assertIn(token,JAVA)
  self.assertLess(JAVA.index('CharoiteWine29Sealed012Stage.verifyOnly(context)'),JAVA.index('scratch.mkdir()'))
  self.assertLess(JAVA.index('prepareFreshDriveC(prefix)'),JAVA.index('serverProc=s.start()'))
  for forbidden in (
   'charoite-next-wine29-direct-init-v4','charoite-next-wine29-pe-dir-v3',
   'charoite-next-wine29-bootstrap-v2','charoite-next-wine29-pe-help-v1',
   'env.put("WINEBOOTSTRAPMODE"','Runtime.getRuntime(','.delete(',
   '.renameTo(', 'deleteOnExit(', 'clearApplicationUserData',
   'Os.symlink("/",','Os.symlink("../..",'
  ):
   with self.subTest(forbidden=forbidden):self.assertNotIn(forbidden,JAVA)
  self.assertNotIn('mkdir(child(prefix,"drive_c/windows")',JAVA)

 def test_explicit_consent_and_archived_v4(self):
  for marker in (
   '"CharoiteWine29V5DriveCProbe.java"',
   'final boolean showArchivedWine29V4Execution = false;',
   'wine29V5DriveC.setText("Wine29 v5 isolated C: mapping test (one-shot)")',
   'setPositiveButton("Authorize ONE new v5 C: test"',
   'setNegativeButton("Cancel — do not execute", null)',
   'CharoiteWine29V5DriveCProbe.run(this)',
   'nextCoreCard.addView(wine29V5DriveC);',
   'versionCode 120', '11.2-next.0.89'
  ):
   with self.subTest(marker=marker):self.assertIn(marker,UI)
  before=UI.split('wine29V5DriveC.setOnClickListener(v ->')[0]
  self.assertNotIn('CharoiteWine29V5DriveCProbe.run(this)',before)
  self.assertIn('Wine29 v6 parent/child Wineboot both EXITED 0.',UI)

 def test_ci_and_licensing(self):
  for marker in (
    'test_wine29_v5_c_drive_contract.py',
    'WINE29_V5_C_DRIVE_FRESH_MAPPING_CONSENT=PASS',
    'cp next-generation/CharoiteWine29V5DriveCProbe.java legal-bundle/CharoiteWine29V5DriveCProbe.java',
    "versionCode='120' versionName='11.2-next.0.89'"
  ):
   with self.subTest(marker=marker):self.assertIn(marker,WF)

if __name__=="__main__":
 unittest.main()

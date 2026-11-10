"""Strict opt-in read-only V28 postmortem; no fresh execution or old data."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
J=(R/"CharoiteWine29V28PreservedReadOnly.java").read_text()
P=(R/"prepare_next.py").read_text()
W=(R.parent/".github/workflows/charoite-next.yml").read_text()
class V28ReadOnly(unittest.TestCase):
    def test_named_file_bounds(self):
        for s in ("v28-foreground-wineserver.log","v28-wine-direct-init.log",
                  "v28-independent-defaultinstall.log","v28-independent-sc-rpcss-query.log",
                  'readIfSafe(prefix,"system.reg",1048576,b)',
                  "Os.lstat(", "OsConstants.S_ISREG", "getCanonicalFile().equals(",
                  "size>maximum", "bytes.size()+n>maximum",
                  "Registry values/names other than fixed allowlist"):
            self.assertIn(s,J)
        for unsafe in ("new ProcessBuilder(", "Runtime.getRuntime()", ".exec(",
                       "FileOutputStream(", ".mkdir(", ".mkdirs(", ".delete(",
                       ".renameTo(", "clearApplicationUserData(",
                       "getAssets().open(", "HttpURLConnection", "URL(",
                       "getSharedPreferences(", "copyVerified(",
                       "charoite-next-wine29-entry-v27", "charoite-next-wine29-entry-v26"):
            self.assertNotIn(unsafe,J)
    def test_explicit_separate_consent(self):
        for s in ("askConsent(Activity activity)", "Authorize bounded READ ONLY",
                  "Cancel — no file access","getNoBackupFilesDir()",
                  "public static String inspect(Context context)",
                  "Copy read-only report", "UNKNOWN (missing/over-cap log)",
                  "END OF V28 PRESERVED READ-ONLY POSTMORTEM"):
            self.assertIn(s,J)
        self.assertLess(J.index('setPositiveButton("Authorize bounded READ ONLY"'),
                        J.index("new Thread(() ->"))
    def test_ui_archive_update_source_and_app_identity(self):
        for s in ("final boolean showArchivedWine29V28Execution = false;",
                  "ARCHIVED V28; never expose an execution button again",
                  "Review V28 preserved diagnostics (READ ONLY)",
                  "CharoiteWine29V28PreservedReadOnly.askConsent(this)",
                  "wine29V28Action.addView(readOnlyV28)",
                  'sendV28GitHub.setText("Send report to GitHub")',
                  "versionCode 155","11.2-next.0.124",
                  '"CharoiteWine29V28PreservedReadOnly.java"'):
            self.assertIn(s,P)
        for s in ("CONSUMED_V28_STRICT_READ_ONLY_POSTMORTEM_SOURCE_GATE=PASS",
                  "CharoiteWine29V28PreservedReadOnly.java legal-bundle/",
                  "versionCode='155' versionName='11.2-next.0.124'",
                  "charoite-next-vc155",
                  "NEXT_STABLE_PORTAL_RELEASE_UNCHANGED=PASS"):
            self.assertIn(s,W)
if __name__=="__main__":unittest.main()

"""V28 System report and official GitHub release update source contract."""
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=(R/"prepare_next.py").read_text()
S=(R/"CharoiteWine29V28ReportShare.java").read_text()
U=(R/"CharoiteNextUpdateChecker.java").read_text()
W=(R.parent/".github/workflows/charoite-next.yml").read_text()

class NextSystemWorkflow(unittest.TestCase):
    def test_persistent_report_without_wine_rerun(self):
        for marker in (
            'sendV28GitHub.setText("Send report to GitHub")',
            "CharoiteWine29V28ReportShare.sendFromSystem(this)",
            "CharoiteWine29V28ReportShare.rememberReport(this, report)",
            "Review GitHub report", "nextCoreCard.addView(wine29V28Action)"
        ): self.assertIn(marker,P)
        for marker in (
            'public static void sendFromSystem(Activity activity)',
            "public static void rememberReport(Context context, String report)",
            "getSharedPreferences(PREFS,Context.MODE_PRIVATE)",
            'pasted.setHint("Paste the complete V28 short report you already copied")',
            "reviewSanitized(activity,json)",
            "Open GitHub issue draft"
        ): self.assertIn(marker,S)
        for unsafe in ("ProcessBuilder(", "FileInputStream(", "getNoBackupFilesDir(",
                       "HttpURLConnection", "Authorization", ".delete("):
            self.assertNotIn(unsafe,S)

    def test_startup_update_opt_in_only_experimental_and_official(self):
        for marker in (
            'nextCheckUpdates.setText("Check for updates")',
            "CharoiteNextUpdateChecker.checkNow(this)",
            "CharoiteNextUpdateChecker.checkOnLaunch(this)",
            '"CharoiteNextUpdateChecker.java"',
            "versionCode 157","11.2-next.0.126"
        ): self.assertIn(marker,P)
        for marker in (
            'private static final String PACKAGE = "com.charoitx"',
            "https://api.github.com/repos/rgarn023/CharoitePortal/releases?per_page=30",
            'String tag=r.optString("tag_name","")',
            'tag.matches("charoite-next-vc[1-9][0-9]{0,8}")',
            'APK_NAME = "Charoite-Next-Android.apk"',
            "browser_download_url",
            "sha256:[a-f0-9]{64}",
            "result.versionCode>installed",
            'setTitle("Charoite Next update available")',
            'setPositiveButton("Update in app"',
            'public static void checkOnLaunch(Activity activity)',
            'public static void checkNow(Activity activity)'
        ): self.assertIn(marker,U)
        for unsafe in ("getNoBackupFilesDir(", "FileOutputStream(", "ProcessBuilder(",
                       "delete(", "ACTION_INSTALL_PACKAGE", "REQUEST_INSTALL_PACKAGES",
                       "github_pat_", "Authorization", "Runtime.getRuntime()"):
            self.assertNotIn(unsafe,U)
        self.assertIn("7200L",U)

    def test_release_job_separate_and_portal_unmodified(self):
        for marker in (
            "publish-next-github-release:",
            "needs: [build-runtime-preview]",
            "contents: write",
            "charoite-next-vc157",
            '--latest=false',
            "gh release create",
            "gh run download",
            "Charoite-Next-Android.apk",
            "Charoite-Next-LGPL-Sources.zip",
            "NEXT_STABLE_PORTAL_RELEASE_UNCHANGED=PASS",
            "versionCode='157' versionName='11.2-next.0.126'",
            "CharoiteNextUpdateChecker.java legal-bundle/",
            "NEXT_SYSTEM_GITHUB_REPORT_AND_UPDATE_SOURCE_GATE=PASS"
        ): self.assertIn(marker,W)
        self.assertNotIn("gh release delete",W)
        self.assertNotIn("--clobber",W)

if __name__=="__main__":unittest.main()

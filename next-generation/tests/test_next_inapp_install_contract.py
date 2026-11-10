"""Owner-controlled, SHA-256-verified Charoite Next in-app Android updater."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
I=(ROOT/"CharoiteNextInAppInstaller.java").read_text()
R=(ROOT/"CharoiteNextInstallStatusReceiver.java").read_text()
C=(ROOT/"CharoiteNextUpdateChecker.java").read_text()
P=(ROOT/"prepare_next.py").read_text()
W=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()

class InAppUpdater(unittest.TestCase):
    def test_true_in_app_not_browser_and_android_approval(self):
        for s in (
            'setPositiveButton("Update in app"',
            "CharoiteNextInAppInstaller.updateWithConsent(",
            "result.expectedSize", "result.sha256", "result.versionCode",
            "checkOnLaunch(Activity activity)", "checkNow(Activity activity)"
        ):self.assertIn(s,C)
        for old in ("Open GitHub download","Intent.ACTION_VIEW"):
            self.assertNotIn(old,C)
        for s in (
            "params.setRequireUserAction(",
            "USER_ACTION_REQUIRED", "getPackageInstaller()",
            "session.commit(callback.getIntentSender())",
            "FLAG_MUTABLE", "canRequestPackageInstalls()",
            "Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES",
            "Cancel download"
        ):self.assertIn(s,I)
        for s in (
            "STATUS_PENDING_USER_ACTION",
            "showInstallerConfirmation(context,confirmation)",
            "Intent.EXTRA_INTENT", 'String ACTION="com.charoitx.action.NEXT_APK_INSTALL_STATUS"'
        ):self.assertIn(s,R)
        self.assertNotIn("USER_ACTION_NOT_REQUIRED",I)
        self.assertNotIn("UPDATE_PACKAGES_WITHOUT_USER_ACTION",I)

    def test_only_expected_next_release_and_no_data_access(self):
        for s in (
            'private static final String PACKAGE = "com.charoitx"',
            'github\\\\.com/rgarn023/CharoitePortal/releases/download/',
            "release-assets.githubusercontent.com",
            'host.equals("objects.githubusercontent.com")',
            "redirect<6", "setInstanceFollowRedirects(false)",
            "expectedDigest.matches(", "expectedBytes > MAX_APK",
            "count>expectedBytes", 'MessageDigest.getInstance("SHA-256")',
            "expectedDigest.equals(sha.toString())", "session.abandon()",
            "params.setAppPackageName(PACKAGE)", "newVersionCode<=installed",
            "cancel.get()", "BUSY.compareAndSet(false,true)"
        ):self.assertIn(s,I)
        for bad in ("getNoBackupFilesDir(", "getFilesDir(", "getCacheDir(",
                    "FileInputStream(", "FileOutputStream(", "ProcessBuilder(",
                    "getSharedPreferences(", "clearApplicationUserData(",
                    ".delete(", ".mkdir(", "Runtime.getRuntime()",
                    "Wine29V28FocusedInfProbe.run(", "startActivity(new Intent(Intent.ACTION_VIEW"):
            self.assertNotIn(bad,I)
        self.assertIn("CharoiteNextInstallStatusReceiver.class",I)
        self.assertIn('"com.charoitx".equals(context.getPackageName())',R)
        self.assertNotIn("ProcessBuilder(",R)

    def test_only_experimental_manifest_ci_and_release(self):
        for s in (
            "android.permission.REQUEST_INSTALL_PACKAGES",
            'com.charoitegames.core.CharoiteNextInstallStatusReceiver',
            'ns + "exported": "false"',
            '"CharoiteNextInAppInstaller.java"',
            '"CharoiteNextInstallStatusReceiver.java"',
            "versionCode 155","11.2-next.0.124",
            "No browser or manual APK"
        ):self.assertIn(s,P)
        for s in (
            "CharoiteNextInAppInstaller.java legal-bundle/",
            "CharoiteNextInstallStatusReceiver.java legal-bundle/",
            "NEXT_IN_APP_ANDROID_PACKAGE_INSTALLER_GATES=PASS",
            "charoite-next-vc155",
            "versionCode='155' versionName='11.2-next.0.124'",
            "--latest=false"
        ):self.assertIn(s,W)
        self.assertNotIn("gh release delete",W)
        self.assertNotIn("gh release upload --clobber",W)

if __name__=="__main__":unittest.main()

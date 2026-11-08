"""First in-app Charoite Core Manager: safe inventory, no runtime mutation."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANAGER = (ROOT / "CharoiteCoreManager.java").read_text(encoding="utf-8")
PREP = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
RUNTIME = (ROOT / "CharoiteNextRuntime.java").read_text(encoding="utf-8")
WF = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class ModularCoreManagerContract(unittest.TestCase):
    def test_shipped_in_system_screen_and_apk(self):
        self.assertIn('shutil.copy2(source_dir / "CharoiteCoreManager.java", core_manager_java)', PREP)
        self.assertIn('coreModules.setText("Manage Charoite Core modules")', PREP)
        self.assertIn('CharoiteCoreManager.show(this)', PREP)
        self.assertIn('nextCoreCard.addView(coreModules);', PREP)
        self.assertIn('cp next-generation/CharoiteCoreManager.java legal-bundle/CharoiteCoreManager.java', WF)
        self.assertIn('versionCode 132', PREP)
        self.assertIn('11.2-next.0.101', PREP)
        self.assertIn("versionCode='132' versionName='11.2-next.0.101'", WF)

    def test_defaults_to_existing_runtime_only(self):
        for phrase in (
            'AUTOMATIC — EXISTING ENGINE', 'CharoiteNextRuntime.WINE_BOX64',
            'NOT RUNNABLE', 'NOT ENABLED', 'NOT INTEGRATED',
            'No Wine, wineserver, Wineboot, shell, game or executable is run.',
            'getSharedPreferences(PREF, Context.MODE_PRIVATE)',
            'putBoolean(SHOW_ADVANCED, checked).apply()',
            'new AlertDialog.Builder(activity)',
            '65536',
        ):
            with self.subTest(phrase=phrase): self.assertIn(phrase, MANAGER)
        for forbidden in (
            'new ProcessBuilder(', 'Runtime.getRuntime(', '.exec(', 'startActivity(',
            'FileOutputStream', '.delete(', '.renameTo(', 'mkdirs(', 'getNoBackupFilesDir(',
            'getFilesDir(', 'System.loadLibrary', 'getExternalStorage',
            'clearApplicationUserData', 'DownloadManager',
            'CharoiteWine29V1PeHelpProbe.run(',
        ):
            self.assertNotIn(forbidden, MANAGER)

    def test_system_status_does_not_advertise_removed_buttons(self):
        self.assertIn('public static final String VERSION = "Experimental Wine29 v10 PE-entry diagnostic; SCM not verified"', RUNTIME)
        self.assertIn('Wine29 v9 Wineboot exited 0; services.exe and userenv.dll mapped. SCM still unverified.', RUNTIME)
        self.assertNotIn('0.70 (Wine29 v1 kernel32 read-only postmortem', RUNTIME)
        self.assertIn('Current Wine29 System test: consent-gated V10 native-loader / sc.exe PE-entry one-shot.', RUNTIME)
        self.assertNotIn('Use Test native Wine startup prerequisites', RUNTIME)
        self.assertNotIn('Use Stage expanded Wine 26-module data', RUNTIME)
        self.assertNotIn('Use Test source-built Wine --version', RUNTIME)
        self.assertIn('final boolean showArchivedWineTests = false;', PREP)
        self.assertIn('CharoiteWine29V1Forensics.run(this)', PREP)

if __name__ == "__main__":
    unittest.main()

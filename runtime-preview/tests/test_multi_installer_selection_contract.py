"""Installer folder ambiguity must require user selection, never guess-and-run."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PORTAL = (ROOT / "TouhouEntryActivity.java").read_text()
CORE = (ROOT / "charoite-core/CharoiteGameImport.java").read_text()
LIBRARY = (ROOT / "charoite-core/CharoiteGameLibrary.java").read_text()
DIAGNOSTICS = (ROOT / "charoite-core/CharoiteDiagnostics.java").read_text()


class MultipleInstallerContract(unittest.TestCase):
    def test_candidates_include_nested_setup_paths(self):
        self.assertIn('public final List<String> installerCandidates;', CORE)
        self.assertIn('public final String importDirectory;', CORE)
        self.assertIn('listInstallerCandidates(target)', CORE)
        self.assertIn('selection != Selection.STANDALONE_INSTALLER', CORE)
        self.assertIn('selection != CharoiteGameImport.Selection.STANDALONE_INSTALLER', PORTAL)
        self.assertIn('collectExecutables(root, root, all, 0)', CORE)
        self.assertIn('new File(root, relative).getAbsolutePath()', CORE)
        self.assertIn('relativeA.compareToIgnoreCase(relativeB)', CORE)
        self.assertIn('new String[]{"setup.exe", "install.exe", "installer.exe"}', CORE)
        self.assertIn('filename.startsWith("setup")', CORE)

    def test_folder_import_cannot_auto_run_an_ambiguous_setup(self):
        method = CORE.split('public static boolean shouldLaunchAfterImport(', 1)[1]
        method = method.split('public static boolean isLikelyInstaller(', 1)[0]
        self.assertIn('selection == Selection.STANDALONE_INSTALLER', method)
        self.assertIn('entry.put("installerCandidates",', PORTAL)
        self.assertIn('entry.put("installerSelectionPending",', PORTAL)
        self.assertIn('imported.installerCandidates.size() > 1', PORTAL)
        self.assertIn('showInstallerChooser(entry);', PORTAL)
        self.assertIn('!selectionPending && new File(path).isFile()', PORTAL)
        self.assertIn('choose.setEnabled(!busy && containerId > 0);', PORTAL)
        self.assertIn('if (CharoiteGameImport.shouldLaunchAfterImport(selection))', PORTAL)

    def test_user_can_choose_or_change_the_installer(self):
        self.assertIn('private void showInstallerChooser(JSONObject entry)', PORTAL)
        self.assertIn('Which installer should Charoite run?', PORTAL)
        self.assertIn('.setItems(labels, (dialog, which) -> {', PORTAL)
        self.assertNotIn('.setMessage("Multiple setup programs', PORTAL)
        self.assertIn('labels[i] = canonical.substring(root.length());', PORTAL)
        self.assertIn('!canonical.startsWith(root)', PORTAL)
        self.assertIn('!executable.isFile()', PORTAL)
        self.assertIn('installerSelectionPending", false', PORTAL)
        self.assertIn('saveEntry(entry);', PORTAL)
        self.assertIn('CHOOSE INSTALLER', PORTAL)
        self.assertIn('CHANGE INSTALLER', PORTAL)
        self.assertIn('Not now', PORTAL)

    def test_shard_panel_is_removed_but_diagnostics_remain(self):
        self.assertNotIn('CHECK SHARD OF DREAMS', PORTAL)
        self.assertNotIn('SHARD OF DREAMS INSTALLATION", 12, GOLD', PORTAL)
        self.assertIn('CharoiteDiagnostics.recordShardInstallationScan(', PORTAL)
        self.assertIn('SHARD OF DREAMS INSTALLATION CHECK:', DIAGNOSTICS)


if __name__ == '__main__':
    unittest.main()

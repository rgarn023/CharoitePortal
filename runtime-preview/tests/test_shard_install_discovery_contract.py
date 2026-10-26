"""Regression checks for Shard of Dreams installation detection and Library refresh.

The expansion's installed enbu_ap.exe must appear as a separate Library
game without needing an app restart or a new Wine prefix.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PORTAL = (ROOT / "TouhouEntryActivity.java").read_text()
SHARD = (ROOT / "charoite-core/CharoiteShardOfDreamsSupport.java").read_text()
PROFILES = (ROOT / "charoite-core/CharoiteGameProfiles.java").read_text()
DISCOVERY = (ROOT / "charoite-core/CharoiteGameDiscovery.java").read_text()
LIBRARY = (ROOT / "charoite-core/CharoiteGameLibrary.java").read_text()
SESSION = (ROOT / "charoite-core/CharoiteGameSessions.java").read_text()
DIAGNOSTICS = (ROOT / "charoite-core/CharoiteDiagnostics.java").read_text()

class ShardInstallDiscoveryContract(unittest.TestCase):
    def test_discovery_is_executable_based_and_non_destructive(self):
        self.assertIn('name.equals("enbu_ap.exe")', PROFILES)
        self.assertIn('Touhou Puppet Dance Performance: Shard of Dreams', PROFILES)
        self.assertIn('profile.acceptsInstalledExecutable(child.getName())', DISCOVERY)
        self.assertIn('java.util.List<org.json.JSONObject> installedGames', SHARD)
        self.assertIn('Shard executable found:', SHARD)
        self.assertIn('Shard executable enbu_ap.exe was NOT found', SHARD)
        self.assertIn('Shard installation folder(s) detected', SHARD)
        self.assertIn('Files.isSymbolicLink(child.toPath())', SHARD)
        self.assertIn('String.join("; ", candidates)', SHARD)
        self.assertIn('enbu_ap.exe', SHARD)
        self.assertIn('new File(containerRoot, ".wine/drive_c")', SHARD)
        self.assertIn('CharoiteGameLibrary.mergeInstalled(this, discovered)', PORTAL)
        self.assertIn('CharoiteGameLibrary.load', PORTAL)

    def test_visible_library_refreshed_immediately_after_scan(self):
        start = PORTAL.index('private void findInstalledGames(boolean afterInstaller)')
        end = PORTAL.index('private void importGame(', start)
        scanned = PORTAL[start:end]
        self.assertIn('CharoiteGameLibrary.mergeInstalled(this, discovered)', scanned)
        self.assertIn('refreshLibrary();', scanned)
        self.assertIn('if (count > 0 || shardFound) showSection(0);', scanned)
        self.assertLess(scanned.index('refreshLibrary();'), scanned.index('showSection(0)'))
        self.assertIn('CharoiteGameSessions.consumePendingInstallerScan(this);', scanned)
        self.assertNotIn('consumePendingInstallerScan(this))', PORTAL[
            PORTAL.index('@Override protected void onResume()'):
            PORTAL.index('@Override protected void onSaveInstanceState')])
        self.assertIn('CharoiteGameSessions.hasPendingInstallerScan(this)', PORTAL)
        self.assertIn('scanAfterInstallerReturn', PORTAL)
        self.assertIn('CharoiteGameLibrary.mergeInstalled', LIBRARY)

    def test_shard_diagnosis_available_even_with_no_installed_icon(self):
        self.assertIn('CHECK SHARD OF DREAMS', PORTAL)
        self.assertIn('SHARD OF DREAMS INSTALLATION', PORTAL)
        self.assertIn('CharoiteDiagnostics.shardInstallationScan(this)', PORTAL)
        self.assertIn('CharoiteDiagnostics.recordShardInstallationScan(this, shardReport);', PORTAL)
        self.assertIn('SHARD OF DREAMS INSTALLATION CHECK:', DIAGNOSTICS)
        self.assertIn('charoite_shard_install_scan', DIAGNOSTICS)
        self.assertIn('com.charoitegames.core.CharoiteShardOfDreamsSupport', PORTAL)
        self.assertIn('CharoiteShardOfDreamsSupport.checkAndRepair(host, executable)', SESSION)
        # Missing 'notkey' is only examined for a *discovered launched* exe.
        self.assertNotIn('Files.createSymbolicLink(', DISCOVERY)
        self.assertNotIn('deleteRecursively(', DISCOVERY)
        self.assertNotIn('Files.copy(', SHARD)
        self.assertNotIn('Files.move(', SHARD)

if __name__ == '__main__':
    unittest.main()

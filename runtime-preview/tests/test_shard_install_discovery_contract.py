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
        self.assertIn('CharoiteShardOfDreamsSupport.isExpansionGame(name)', PROFILES)
        self.assertIn('if (isExpansionGame(name))', SHARD)
        self.assertIn('JAPANESE_EXECUTABLE = "幻想人形演舞-ユメノカケラ-.exe"', SHARD)
        self.assertIn('installedExecutable(dest)', SHARD)
        self.assertIn('isExpansionGame(name)', SHARD)
        self.assertIn('File executable = installedExecutable(target)', SHARD)
        self.assertIn('Touhou Puppet Dance Performance: Shard of Dreams', PROFILES)
        self.assertIn('profile.acceptsInstalledExecutable(child.getName())', DISCOVERY)
        self.assertIn('java.util.List<org.json.JSONObject> installedGames', SHARD)
        self.assertIn('Shard executable found:', SHARD)
        self.assertIn('No recognized Shard executable (enbu_ap.exe or ', SHARD)
        self.assertIn('Shard installation directories detected', SHARD)
        self.assertIn('Files.isSymbolicLink(child.toPath())', SHARD)
        self.assertIn('String.join("; ", candidates)', SHARD)
        self.assertIn('discoverRegisteredExpansion(', SHARD)
        self.assertIn('registeredPath(File folder)', SHARD)
        self.assertIn('Charset.forName("windows-31j")', SHARD)
        self.assertIn('verifiedDestination(File drive, String windowsPath)', SHARD)
        self.assertIn('dest.toPath().startsWith(root.toPath())', SHARD)
        self.assertIn('File executable = installedExecutable(target);', SHARD)
        self.assertIn('installationEvidence(drive, candidates)', SHARD)
        self.assertIn('AppData registration:', SHARD)
        self.assertIn('Contents:', SHARD)
        self.assertIn('install.ini InstallPath:', SHARD)
        self.assertIn('discovered.addAll(com.charoitegames.core.CharoiteShardOfDreamsSupport', PORTAL)
        self.assertIn('Imported installer files:', PORTAL)
        self.assertIn('IMPORT COMPLETE INSTALLER FOLDER', PORTAL)
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
        self.assertIn('public static synchronized int mergeInstalled(', LIBRARY)

    def test_shard_diagnosis_available_even_with_no_installed_icon(self):
        # The Shard-specific setup panel is retired. Core installation
        # discovery and the full diagnostic report remain available.
        self.assertNotIn('CHECK SHARD OF DREAMS', PORTAL)
        self.assertNotIn('SHARD OF DREAMS INSTALLATION", 12, GOLD', PORTAL)
        self.assertNotIn('CharoiteDiagnostics.shardInstallationScan(this)', PORTAL)
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
        self.assertNotIn('Files.write(', SHARD)
        self.assertNotIn('new FileOutputStream(', SHARD)
        self.assertNotIn('delete()', SHARD)

if __name__ == '__main__':
    unittest.main()

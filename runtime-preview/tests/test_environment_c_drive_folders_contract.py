"""Each realm has a dedicated, stable folder in its own Windows C: drive.

New imports use that folder. Historic executable paths are retained; a new
version must never delete or silently move existing Wine games or saves.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENV = (ROOT / "charoite-core/CharoiteEnvironments.java").read_text()
IMP = (ROOT / "charoite-core/CharoiteGameImport.java").read_text()
BATTLE = (ROOT / "charoite-core/CharoiteBattleNetSupport.java").read_text()
PORTAL = (ROOT / "TouhouEntryActivity.java").read_text()


class EnvironmentCDriveFoldersContract(unittest.TestCase):
    def test_stable_isolated_environment_directory(self):
        self.assertIn('new File(containerRoot, ".wine/drive_c").getCanonicalFile()', ENV)
        self.assertIn('"CharoitePortal/Environments/" + environmentId', ENV)
        self.assertIn('environmentId.matches("[a-z0-9][a-z0-9-]{0,80}")', ENV)
        self.assertIn('!base.toPath().startsWith(drive.toPath())', ENV)
        self.assertIn('!result.toPath().startsWith(base.toPath())', ENV)
        self.assertIn('ensureStorageFolder(attached.getRootDir(), id, null)', ENV)
        self.assertIn('new ContainerManager(host).getContainerById(containerId)', ENV)
        self.assertNotIn('renameTo(', ENV)
        self.assertNotIn('deleteRecursively(', ENV)

    def test_new_game_imports_use_realm_directory(self):
        self.assertIn('File containerRoot, String environmentId,', IMP)
        self.assertIn('containerRoot, environmentId, "Imports"', IMP)
        self.assertNotIn('".wine/drive_c/TouhouPocket"', IMP)
        self.assertIn('CharoiteEnvironments.activeId(this)', PORTAL)
        self.assertIn('CharoiteGameImport.importSelected(', PORTAL)
        self.assertIn('deleteNewImport(target)', IMP)

    def test_battle_net_downloads_use_battle_net_realm_and_keep_old_file(self):
        self.assertIn('CharoiteEnvironments.BATTLE_NET, "Installers"', BATTLE)
        self.assertIn('"CharoitePortal/BattleNet/Installer/" + FILENAME', BATTLE)
        self.assertIn('if (file.isFile() && validPe(file)) return file;', BATTLE)
        self.assertIn('validPe(legacy) ? legacy : null;', BATTLE)
        self.assertIn('!validPe(part)', BATTLE)


if __name__ == "__main__":
    unittest.main()

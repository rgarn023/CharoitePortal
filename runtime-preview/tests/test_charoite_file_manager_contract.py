"""Safety and integration contracts for the built-in Wine C: file browser."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANAGER = (ROOT / "charoite-core/CharoiteFileManagerActivity.java").read_text()
PORTAL = (ROOT / "TouhouEntryActivity.java").read_text()
OVERLAY = (ROOT / "overlay.py").read_text()


class CharoiteFileManagerContract(unittest.TestCase):
    def test_system_tab_and_manifest(self):
        self.assertIn('OPEN WINDOWS FILE MANAGER', PORTAL)
        self.assertIn('startActivity(new Intent(this, CharoiteFileManagerActivity.class))', PORTAL)
        self.assertIn('CharoiteFileManagerActivity.java', OVERLAY)
        self.assertIn('com.charoitegames.core.CharoiteFileManagerActivity', OVERLAY)
        self.assertIn('a + "exported": "false"', OVERLAY)

    def test_existing_container_visibility_without_reset(self):
        self.assertIn('new ContainerManager(this).getContainers()', MANAGER)
        self.assertIn('CharoiteEnvironments.activeContainerId(this)', MANAGER)
        self.assertIn('new File(c.getRootDir(),".wine/drive_c")', MANAGER)
        self.assertIn('drive=root;directory=root;', MANAGER)
        for forbidden in ('getDatabasePath(', 'deleteRecursively(', 'deleteAll(', 'clearApplicationUserData(', 'deleteNewImport('):
            self.assertNotIn(forbidden, MANAGER)

    def test_android_scoped_storage_legacy_and_copy_protections(self):
        self.assertIn('Intent.ACTION_OPEN_DOCUMENT_TREE', MANAGER)
        self.assertIn('DocumentFile.fromTreeUri(this,uri)', MANAGER)
        self.assertIn('Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION', MANAGER)
        self.assertIn('Files.isSymbolicLink(f.toPath())', MANAGER)
        self.assertIn('f.getCanonicalFile().toPath().startsWith(root.getCanonicalFile().toPath())', MANAGER)
        self.assertIn('Refusing to overwrite', MANAGER)
        self.assertIn('Files.move(temp.toPath(),target.toPath())', MANAGER)
        self.assertNotIn('StandardCopyOption.REPLACE_EXISTING', MANAGER)
        self.assertNotIn('Runtime.getRuntime().exec(', MANAGER)
        self.assertNotIn('su -c', MANAGER)

    def test_exports_and_imports_are_user_initiated(self):
        self.assertIn('Intent.ACTION_CREATE_DOCUMENT', MANAGER)
        self.assertIn('getContentResolver().openOutputStream(uri,"w")', MANAGER)
        self.assertIn('Import a file here (no overwrite)', MANAGER)
        self.assertIn('Export this folder to your phone', MANAGER)
        self.assertIn('MAX_ITEMS=20000', MANAGER)


if __name__ == "__main__":
    unittest.main()

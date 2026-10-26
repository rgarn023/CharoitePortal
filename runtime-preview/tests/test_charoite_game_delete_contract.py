"""Charoite game deletion must be opt-in, scoped and separate from metadata."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PORTAL = (ROOT / "TouhouEntryActivity.java").read_text()
LIBRARY = (ROOT / "charoite-core/CharoiteGameLibrary.java").read_text()
REMOVAL = (ROOT / "charoite-core/CharoiteGameRemoval.java").read_text()
OVERLAY = (ROOT / "overlay.py").read_text()

class GameDeletionContract(unittest.TestCase):
    def test_core_packaging_and_library_button(self):
        self.assertIn('"CharoiteGameRemoval.java"', OVERLAY)
        self.assertIn('import com.charoitegames.core.CharoiteGameRemoval;', PORTAL)
        self.assertIn('outlinedButton("MANAGE",', PORTAL)
        self.assertIn('manageGame(name, path)', PORTAL)
        self.assertIn('onLongClickListener(v -> {', PORTAL)

    def test_remove_shortcut_keeps_files(self):
        self.assertIn('public static synchronized boolean remove(', LIBRARY)
        self.assertIn('if (found) persist(host, kept)', LIBRARY)
        self.assertIn('CharoiteGameLibrary.remove(this, executable)', PORTAL)
        self.assertIn('Game files retained.', PORTAL)
        self.assertNotIn('delete()', LIBRARY)

    def test_delete_is_confirmed_and_scoped(self):
        self.assertIn('Delete installed game', PORTAL)
        self.assertIn('setTitle("Permanently delete " + name + "?")', PORTAL)
        self.assertIn('worker.execute(() -> {', PORTAL)
        self.assertIn('CharoiteGameRemoval.deleteGameFolder(', PORTAL)
        self.assertIn('File drive = new File(container.getRootDir(), ".wine/drive_c").getCanonicalFile()', REMOVAL)
        self.assertIn('int depth = drive.toPath().relativize(target.toPath()).getNameCount();', REMOVAL)
        self.assertIn('if (depth < 2)', REMOVAL)
        self.assertIn('another.toPath().startsWith(target.toPath())', REMOVAL)
        self.assertIn('Files.isSymbolicLink(entry.toPath())', REMOVAL)
        self.assertIn('MAX_VISITED = 200000', REMOVAL)
        self.assertNotIn('deleteRecursively(', REMOVAL)
        self.assertNotIn('REPLACE_EXISTING', REMOVAL)

if __name__ == "__main__":
    unittest.main()

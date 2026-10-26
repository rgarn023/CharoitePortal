"""Charoite Portal Library uses real Windows executable icon resources.

The pinned Winlator engine ships PEParser / MSIcon. Asset rights stay with the
installed user's game; Charoite does not redistribute those third-party images.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ICON = (ROOT / "charoite-core/CharoiteGameIcons.java").read_text()
PORTAL = (ROOT / "TouhouEntryActivity.java").read_text()
OVERLAY = (ROOT / "overlay.py").read_text()

class RealGameIconsContract(unittest.TestCase):
    def test_core_shipped_and_displayed_for_installed_games(self):
        self.assertIn('"CharoiteGameIcons.java"', OVERLAY)
        self.assertIn('import com.charoitegames.core.CharoiteGameIcons;', PORTAL)
        self.assertIn('CharoiteGameIcons.bind(', PORTAL)
        self.assertIn('if (exists) CharoiteGameIcons.bind(', PORTAL)
        self.assertIn('officialGameIcon.setVisibility(View.GONE);', PORTAL)
        self.assertIn('ImageView.ScaleType.FIT_CENTER', PORTAL)
        self.assertIn('gameIconCharacter(path)', PORTAL)
        self.assertIn('gameTitle', PORTAL)
        self.assertIn('manageGame(name, path)', PORTAL)
        self.assertIn('tile.setOnLongClickListener(', PORTAL)

    def test_native_pe_icons_and_game_icon_fallback(self):
        self.assertIn('PEParser.extractIcon(exe)', ICON)
        self.assertIn('MSIcon.decodeFile(source)', ICON)
        self.assertIn('name + ".ico"', ICON)
        self.assertIn('name + ".png"', ICON)
        self.assertIn('fallback.setVisibility(View.VISIBLE);', ICON)
        self.assertIn('fallback.setVisibility(View.GONE);', ICON)
        self.assertNotIn('https://', ICON)
        self.assertNotIn('getAssets().open(', ICON)
        self.assertNotIn('WinlatorIconDownloads', ICON)

    def test_async_cache_never_modifies_games_or_blocks_ui(self):
        self.assertIn('Executors.newSingleThreadExecutor()', ICON)
        self.assertIn('WORKER.execute(() -> {', ICON)
        self.assertIn('WeakReference<ImageView>', ICON)
        self.assertIn('WeakReference<TextView>', ICON)
        self.assertIn('new File(app.getCacheDir(), "charoite-game-icons")', ICON)
        self.assertIn('exe.lastModified()', ICON)
        self.assertIn('Bitmap.CompressFormat.PNG', ICON)
        self.assertIn('target.setTag(executable);', ICON)
        self.assertIn('executable.equals(target.getTag())', ICON)
        self.assertNotIn('deleteRecursively(', ICON)
        self.assertNotIn('.wine/drive_c/', ICON)

if __name__ == "__main__":
    unittest.main()

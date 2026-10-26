"""Popup keyboard and safe Shard of Dreams base-game reference contract."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOFT = (ROOT/"charoite-core/CharoiteSoftKeyboard.java").read_text()
TOUCH = (ROOT/"charoite-core/CharoiteTpdpTouchControls.java").read_text()
SHARD = (ROOT/"charoite-core/CharoiteShardOfDreamsSupport.java").read_text()
SESSION = (ROOT/"charoite-core/CharoiteGameSessions.java").read_text()
DIAGNOSTICS = (ROOT/"charoite-core/CharoiteDiagnostics.java").read_text()
OVERLAY = (ROOT/"overlay.py").read_text()
PROFILE = (ROOT/"charoite-core/CharoiteGraphicsProfiles.java").read_text()
DISCOVERY = (ROOT/"charoite-core/CharoiteGameProfiles.java").read_text()

class KeyboardContract(unittest.TestCase):
    def test_native_keyboard_opens_from_game_without_new_runtime(self):
        self.assertIn('CharoiteSoftKeyboard.java', OVERLAY)
        self.assertIn('AppUtils.showKeyboard((AppCompatActivity) host)', SOFT)
        self.assertIn('host.isFinishing()', SOFT)
        self.assertIn('final Button keyboard = button(host, "KEYBOARD"', TOUCH)
        self.assertIn('root.addView(keyboard);', TOUCH)
        self.assertIn('keyboard.setOnClickListener(', TOUCH)
        self.assertIn('CharoiteSoftKeyboard.show(host);', TOUCH)
        self.assertIn('releaseAll.run();', TOUCH)
        # Keyboard belongs in the shoulder row, between L and R, never
        # over the game at the top edge.
        self.assertIn('position(keyboard, (width - keyboardW) / 2,', TOUCH)
        self.assertIn('shoulderY, keyboardW, barHeight);', TOUCH)
        self.assertIn('rightShoulderX - leftShoulderX - shoulderW - 2 * gap', TOUCH)
        self.assertNotIn('position(keyboard, (width - dp(host, 86)) / 2,', TOUCH)

    def test_ime_overlays_handheld_without_moving_windows_game(self):
        # Both Android window panning and Winlator's own mouse-follow
        # compositor translation have to be disabled for TPDP/Shard.
        self.assertIn('SOFT_INPUT_ADJUST_NOTHING', OVERLAY)
        self.assertIn('renderer.setScreenOffsetYRelativeToCursor(false);', OVERLAY)
        self.assertIn('keyboard_pan_anchor', OVERLAY)
        self.assertIn('CharoiteWindowPolicy.enlargeHandheldGame(', OVERLAY)
        self.assertIn('AppUtils.observeSoftKeyboardVisibility(drawerLayout,', OVERLAY)
        self.assertIn('renderer::setScreenOffsetYRelativeToCursor);', OVERLAY)
        self.assertIn('getBooleanExtra("touhou_desktop_window", false)', OVERLAY)
        self.assertIn('keyboard.setOnClickListener(', TOUCH)

class ShardContract(unittest.TestCase):
    def test_expansion_uses_verified_base_with_non_destructive_link(self):
        self.assertIn('CharoiteShardOfDreamsSupport.java', OVERLAY)
        self.assertIn('name.equals("enbu_ap.exe")', SHARD)
        self.assertIn('new File(baseDir, "gn_enbu.exe").isFile()', SHARD)
        self.assertIn('getName().equals(".wine")', SHARD)
        self.assertIn('Files.exists(existing.toPath(), java.nio.file.LinkOption.NOFOLLOW_LINKS)', SHARD)
        self.assertIn('Files.createSymbolicLink(existing.toPath(), base.toPath())', SHARD)
        self.assertIn('samePrefix(expansion, dir)', SHARD)
        self.assertIn('if (file.equals(expansion)) continue', SHARD)
        self.assertIn('files', SHARD.lower())
        for banned in ('deleteRecursively(', 'Files.copy(', 'Files.move(',
                       'Runtime.getRuntime().exec(', 'delete()', 'renameTo('):
            self.assertNotIn(banned, SHARD)
        self.assertIn('CharoiteShardOfDreamsSupport.checkAndRepair(host, executable)', SESSION)
        self.assertIn('CharoiteDiagnostics.recordExpansionStatus(host, expansionStatus)', SESSION)
        self.assertIn('SHARD OF DREAMS COMPATIBILITY:', DIAGNOSTICS)
        self.assertIn('charoite_shard_status', DIAGNOSTICS)
        self.assertIn('"enbu_ap.exe".equals(file)', PROFILE)
        self.assertIn('name.equals("enbu_ap.exe")', DISCOVERY)

if __name__ == '__main__':
    unittest.main()

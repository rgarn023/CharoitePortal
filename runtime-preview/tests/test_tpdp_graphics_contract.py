"""Regression contracts for automatic Charoite Core game graphics profiles.

The user's Galaxy S26 Ultra confirmed TPDP base gameplay with
DXVK 1.10.3 + Turnip. No graphics selection button is required.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORE = (ROOT / "charoite-core/CharoiteCore.java").read_text()
PROFILE = (ROOT / "charoite-core/CharoiteGraphicsProfiles.java").read_text()
WINDOW = (ROOT / "charoite-core/CharoiteWindowPolicy.java").read_text()
SESSION = (ROOT / "charoite-core/CharoiteGameSessions.java").read_text()
PORTAL = (ROOT / "TouhouEntryActivity.java").read_text()
OVERLAY = (ROOT / "overlay.py").read_text()
DIAGNOSTICS = (ROOT / "charoite-core/CharoiteDiagnostics.java").read_text()

class TpdpAutoGraphicsContract(unittest.TestCase):
    def test_core_is_source_of_graphics_truth(self):
        self.assertIn('TPDP_GRAPHICS_DXVK_D3D9_LEGACY = 6', CORE)
        self.assertIn('CharoiteGraphicsProfiles.diagnosticModeForExecutable(executable)', CORE)
        self.assertIn('class CharoiteGraphicsProfiles', PROFILE)
        self.assertIn('Profile forExecutable(String executable)', PROFILE)
        self.assertIn('"gn_enbu.exe".equals(file)', PROFILE)
        self.assertIn('"enbu_ap.exe".equals(file)', PROFILE)
        self.assertIn('CharoiteShardOfDreamsSupport.isExpansionGame(file)', PROFILE)
        self.assertIn('CharoiteShardOfDreamsSupport.isExpansionGame(file)', CORE)
        self.assertIn('CharoiteShardOfDreamsSupport.isExpansionGame(exe)', PORTAL)
        self.assertIn('return null;  // Preserve all saved settings for unknown games.', PROFILE)
        self.assertIn('GraphicsDrivers.TURNIP', PROFILE)
        self.assertIn('DXWrappers.DXVK', PROFILE)
        self.assertIn('"version=1.10.3"', PROFILE)
        self.assertIn('TPDP_GRAPHICS_DXVK_D3D9_LEGACY', PROFILE)

    def test_no_user_selection_or_old_preferences_required(self):
        self.assertIn('CharoiteGraphicsProfiles.diagnosticModeForExecutable(executable)', SESSION)
        self.assertIn('play.putExtra("charoite_tpdp_graphics_mode"', SESSION)
        self.assertIn('Charoite Core automatically selects proven compatibility', PORTAL)
        for old_ui in ('tpdpGraphicsButton', 'tpdpLegacyDxvkButton',
                       'tpdpStabilityButton', 'cycleTpdpGraphics',
                       'selectTpdpStability', 'selectTpdpLegacyDxvk',
                       'TRY DXVK 1.10.3 (D3D9)'):
            self.assertNotIn(old_ui, PORTAL)
        self.assertNotIn('setTpdpGraphicsMode(', SESSION)
        self.assertNotIn('tpdpGraphicsMode(host)', SESSION)
        self.assertNotIn('container.setGraphicsDriver(', PROFILE)
        self.assertNotIn('container.saveData(', PROFILE)

    def test_runtime_only_a_bridge_not_graphics_policy(self):
        self.assertIn('"CharoiteGraphicsProfiles.java", "CharoiteWindowPolicy.java"', OVERLAY)
        self.assertIn('CharoiteGraphicsProfiles.forExecutable(', OVERLAY)
        self.assertIn('graphicsDriver = coreGraphics.graphicsDriver;', OVERLAY)
        self.assertIn('dxwrapper = coreGraphics.dxWrapper;', OVERLAY)
        self.assertIn('dxwrapperConfig = coreGraphics.dxWrapperConfig;', OVERLAY)
        self.assertIn('CharoiteGraphicsProfiles.configureLaunchEnvironment(', OVERLAY)
        self.assertNotIn('getIntExtra("charoite_tpdp_graphics_mode", 0)', OVERLAY)
        self.assertNotIn('dxwrapperConfig = "renderer=vulkan";', OVERLAY)
        self.assertIn('DXVK_LOG_LEVEL', PROFILE)
        self.assertIn('DXVK_LOG_PATH', PROFILE)
        self.assertIn('shard ? "-all" :', PROFILE)
        self.assertIn('shard ? "none" : "info"', PROFILE)
        self.assertIn('!com.charoitegames.core.CharoiteShardOfDreamsSupport.isExpansionGame(', OVERLAY)
        self.assertIn('shard ? "-all" :', PROFILE)
        self.assertIn('shard ? "none" : "info"', PROFILE)
        self.assertIn('"version=1.10.3"', PROFILE)
        self.assertIn('setDxvkLogDirectory(context, dxvkLogs)', PROFILE)
        self.assertIn('DXVK D3D9 DIAGNOSTIC FILES:', DIAGNOSTICS)

    def test_core_owns_window_layout_and_touch_controls(self):
        self.assertIn('CharoiteWindowPolicy.centerGameWindow(', OVERLAY)
        self.assertIn('frame.setX((short)(frame.getX() + deltaX))', WINDOW)
        self.assertIn('frame.setY((short)(frame.getY() + deltaY))', WINDOW)
        self.assertIn('frame.getParent() != xServer.windowManager.rootWindow', WINDOW)
        self.assertIn('java.util.ArrayDeque', WINDOW)
        self.assertIn('onUpdateWindowGeometry(Window window, boolean resized)', OVERLAY)
        self.assertIn('onModifyWindowProperty(Window window, Property property)', OVERLAY)
        controls = (ROOT / 'charoite-core/CharoiteTpdpTouchControls.java').read_text()
        for token in (
            'KeyEvent.KEYCODE_DPAD_UP', 'KeyEvent.KEYCODE_DPAD_DOWN',
            'KeyEvent.KEYCODE_DPAD_LEFT', 'KeyEvent.KEYCODE_DPAD_RIGHT',
            'KeyEvent.KEYCODE_Z', 'KeyEvent.KEYCODE_X',
            'KeyEvent.KEYCODE_F11',
            'MotionEvent.ACTION_DOWN', 'MotionEvent.ACTION_UP',
            'MotionEvent.ACTION_CANCEL', 'releaseAll.run()',
        ):
            self.assertIn(token, controls)
        self.assertIn('CharoiteTpdpTouchControls.attach(', OVERLAY)
        self.assertNotIn('container.saveData(', WINDOW)

    def test_installer_behavior_stays_separate(self):
        self.assertIn('CharoiteCore.isJapaneseInstallerCandidate(', OVERLAY)
        self.assertIn('CharoiteCore.japaneseCompatibilityEnabled(this)', OVERLAY)
        self.assertIn('CharoiteCore.installerFontRepairEnabled(host)', SESSION)
        self.assertIn('if (installer)', SESSION)
        self.assertIn('if (tpdpGraphicsProbe)', DIAGNOSTICS)
        self.assertIn('TPDP DIRECT3D / GRAPHICS OUTPUT', DIAGNOSTICS)
        self.assertIn('recordAudioBackend(Context context, String driver)', DIAGNOSTICS)

if __name__ == '__main__':
    unittest.main()

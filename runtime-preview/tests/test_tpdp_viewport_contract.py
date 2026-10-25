"""TPDP must fill its upper handheld display without changing D3D9 resolution.

The user confirmed DXVK 1.10.3 + Turnip renders correctly; scaling is
compositor-only and must not force Wine to render at a new resolution.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
POLICY = (ROOT / "charoite-core/CharoiteWindowPolicy.java").read_text()
OVERLAY = (ROOT / "overlay.py").read_text()
PROFILE = (ROOT / "charoite-core/CharoiteGraphicsProfiles.java").read_text()
CONTROLS = (ROOT / "charoite-core/CharoiteTpdpTouchControls.java").read_text()

class TpdpViewportContract(unittest.TestCase):
    def test_enlarge_game_using_existing_aspect_preserving_compositor(self):
        self.assertIn('enlargeHandheldGame(String executable,', POLICY)
        self.assertIn('!desktopWindow && CharoiteCore.isTpdpGameExecutable(executable)', POLICY)
        self.assertIn('renderer.setForceWindowsFullscreen(true);', OVERLAY)
        self.assertIn('renderer.setForceWindowsFullscreen(shortcut != null', OVERLAY)
        self.assertIn('placeScaledGame(FullscreenTransformation transform,', POLICY)
        self.assertIn('fullscreenTransformation.update(xServer.screenInfo,', OVERLAY)
        self.assertIn('CharoiteWindowPolicy.placeScaledGame(', OVERLAY)
        self.assertIn('transform.y = (short)', POLICY)

    def test_portrait_game_stays_above_handheld_controls(self):
        self.assertIn('screenInfo.height <= screenInfo.width', POLICY)
        self.assertIn('screenInfo.height * 0.56f', POLICY)
        self.assertIn('screenInfo.height - transform.height', POLICY)
        self.assertIn('topControls', CONTROLS)
        self.assertIn('position(select, centerX, topControls', CONTROLS)
        self.assertIn('position(start, centerX + centerWidth + centerGap', CONTROLS)

    def test_game_pixels_and_profiles_unchanged(self):
        self.assertIn('"version=1.10.3"', PROFILE)
        self.assertIn('GraphicsDrivers.TURNIP', PROFILE)
        self.assertNotIn('container.setScreenSize(', POLICY)
        self.assertNotIn('container.saveData(', POLICY)
        self.assertNotIn('dxwrapper', POLICY)
        self.assertNotIn('setContentResolution(', POLICY)
        self.assertIn('getBooleanExtra("touhou_desktop_window", false)', OVERLAY)
        self.assertIn('getStringExtra("exec_path")', OVERLAY)

if __name__ == '__main__':
    unittest.main()

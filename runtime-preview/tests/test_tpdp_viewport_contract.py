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
        self.assertIn('final float portraitDisplayScale = 0.86f;', POLICY)
        self.assertIn('Math.round(transform.width * portraitDisplayScale)', POLICY)
        self.assertIn('Math.round(transform.height * portraitDisplayScale)', POLICY)
        # The unchanged TPDP base branch is separated from the Shard fit.
        self.assertIn('if (CharoiteShardOfDreamsSupport.isExpansionGame(executable)) {', POLICY)
        self.assertIn('Math.round(targetWidth * 0.75f)', POLICY)
        self.assertIn('Math.round(screenInfo.height * 0.50f) - top', POLICY)
        self.assertIn('Math.min((float) targetWidth / transform.width,', POLICY)
        self.assertIn('(float) targetHeight / transform.height)', POLICY)
        self.assertIn('Math.round(transform.width * fit)', POLICY)
        self.assertIn('Math.round(transform.height * fit)', POLICY)
        self.assertIn('} else {\n            transform.width =', POLICY)
        self.assertIn('transform.x = (short)((screenInfo.width - transform.width) / 2)', POLICY)
        self.assertIn('parentFullscreenTransformation.update(', OVERLAY)
        self.assertIn('CharoiteWindowPolicy.placeScaledGame(', OVERLAY)
        self.assertIn('tpdp_parent_scale_anchor', OVERLAY)
        # The Wine title bar should never be drawn separately from the
        # enlarged game image in the TPDP handheld view.
        self.assertIn('hideNativeFrame(Window frame, Window client,', POLICY)
        self.assertIn('CharoiteWindowPolicy.hideNativeFrame(', OVERLAY)
        self.assertIn('removeRenderableWindow(parent);', OVERLAY)
        self.assertIn('parent.setFullscreenTransformation(null);', OVERLAY)
        self.assertIn('Window client,', POLICY)
        self.assertIn('rememberClientScreen(transform, screenInfo, client, executable, desktopWindow);', POLICY)
        self.assertIn('isHandheldGameClient(client, screenInfo, executable, desktopWindow)', POLICY)
        self.assertIn('width >= 460 && width <= 485 && height >= 335 && height <= 375', POLICY)
        self.assertIn('CharoiteShardOfDreamsSupport.isExpansionGame(executable)', POLICY)
        self.assertIn('if (ratio < 0.95f || ratio > 2.4f) return false;', POLICY)
        self.assertIn('allowDecoratedShardClient(Window client,', POLICY)
        self.assertIn('client.getChildCount() == 0', POLICY)
        self.assertIn('client.hasDecoration(com.winlator.xserver.Decoration.TITLE)', POLICY)
        self.assertIn('shard_decorations_anchor', OVERLAY)
        self.assertIn('window.hasNoDecorations() ||', OVERLAY)
        self.assertIn('allowDecoratedShardClient(', OVERLAY)
        self.assertIn('allowOversizedShardGame(', POLICY)
        self.assertIn('oversized_shard_anchor', OVERLAY)
        self.assertIn('inBounds = inBounds ||', OVERLAY)
        self.assertIn('setHandheldOutline(View outline)', POLICY)
        self.assertIn('handheldScreenBounds()', POLICY)
        self.assertIn('class ScreenOutline extends View', CONTROLS)
        self.assertIn('view.viewOffsetY + area[1] * view.aspect', CONTROLS)
        self.assertIn('view.viewOffsetX + area[0] * view.aspect', CONTROLS)
        self.assertIn('CharoiteWindowPolicy.setHandheldOutline(outline)', CONTROLS)
        self.assertIn('canvas.drawRoundRect(bounds', CONTROLS)
        self.assertIn('CharoiteWindowPolicy.alignWindowFrame(', OVERLAY)
        self.assertIn('parentFullscreenTransformation, fullscreenTransformation,', OVERLAY)
        self.assertIn('frameWindow.getWidth() * scaleX', POLICY)
        self.assertIn('frameWindow.getHeight() * scaleY', POLICY)
        self.assertIn('frameWindow.getRootX() - clientWindow.getRootX()', POLICY)
        self.assertIn('frameWindow.getRootY() - clientWindow.getRootY()', POLICY)
        self.assertIn('if (enlargeHandheldGame(executable, desktopWindow)) return;', POLICY)
        self.assertNotIn('CharoiteWindowPolicy.placeScaledGame(\\n                                parentFullscreenTransformation', OVERLAY)
        # Native game resolution remains unchanged; only its display quad
        # and decorated parent are reduced to an 86%-width presentation.
        self.assertNotIn('window.setWidth(', POLICY)
        self.assertNotIn('window.setHeight(', POLICY)

    def test_portrait_game_stays_above_handheld_controls(self):
        self.assertIn('screenInfo.height <= screenInfo.width', POLICY)
        self.assertIn('screenInfo.height * 0.56f', POLICY)
        self.assertIn('screenInfo.height - transform.height', POLICY)
        self.assertIn('topControls', CONTROLS)
        # Esc/Select/Start/Enter now share one row beneath the game,
        # without changing the game viewport or shoulder positions.
        self.assertIn('position(esc, centerX, topControls', CONTROLS)
        self.assertIn('position(select, centerX + centerWidth + centerGap', CONTROLS)
        self.assertIn('position(start, centerX + 2 * (centerWidth + centerGap)', CONTROLS)
        self.assertIn('position(enter, centerX + 3 * (centerWidth + centerGap)', CONTROLS)

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

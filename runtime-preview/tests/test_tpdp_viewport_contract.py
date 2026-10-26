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
CORE = (ROOT / "charoite-core/CharoiteCore.java").read_text()
SESSIONS = (ROOT / "charoite-core/CharoiteGameSessions.java").read_text()
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
        self.assertIn('width >= 460 && width <= 485 &&', POLICY)
        self.assertIn('height >= 335 && height <= 375', POLICY)
        # Once a Shard game window has been selected, mode-switch resizing
        # must NOT discard the compositor transform just because it is now
        # less than the initial game's 460x335 threshold.
        self.assertIn('activeShardClientId == client.id', POLICY)
        self.assertIn('if (sameClient) {', POLICY)
        self.assertIn('width < 96 || height < 72', POLICY)
        self.assertIn('activeShardClientWidth = width;', POLICY)
        self.assertIn('boolean smallIdentifiedGame = shardIdentity && width >= 240', POLICY)
        self.assertIn('activeShardClientId = client.id;', POLICY)
        self.assertIn('activeShardClientId = -1;', POLICY)
        self.assertIn('recordShardWindowChange(', POLICY)
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

    def test_shard_resize_keeps_same_compositor_window(self):
        # Repeated taps may cause Shard itself to resize. Even if the input
        # debounce misses, the native guest resize must remain inside its
        # Charoite-scaled handheld frame instead of losing the transform.
        self.assertIn('boolean sameClient = activeShardClientId == client.id;', POLICY)
        self.assertIn('if (sameClient) {', POLICY)
        self.assertIn('return true;', POLICY)
        self.assertIn('activeShardClientWidth != width || activeShardClientHeight != height', POLICY)
        self.assertIn('CharoiteDiagnostics.recordShardWindowChange(', POLICY)
        self.assertIn('frame.hasDecoration(com.winlator.xserver.Decoration.TITLE)', POLICY)
        self.assertNotIn('window.setWidth(', POLICY)
        self.assertNotIn('window.setHeight(', POLICY)

    def test_shard_double_tap_does_not_shrink_window(self):
        # Intercept at the actual native TouchpadView click producer. Do not
        # change the game, X11 window size, native mouse or base-game controls.
        self.assertIn('touchpad_source = java_root / "com/winlator/widget/TouchpadView.java"', OVERLAY)
        self.assertIn('touchpad_tap_anchor', OVERLAY)
        self.assertIn('charoiteSuppressShardDoubleTap(finger1)', OVERLAY)
        self.assertIn('private boolean charoiteSuppressShardDoubleTap(Finger finger)', OVERLAY)
        self.assertIn('suppressShardTouchDoubleTap(', OVERLAY)
        self.assertIn('suppressShardTouchDoubleTap(String executable,', POLICY)
        self.assertIn('CharoiteShardOfDreamsSupport.isExpansionGame(executable)', POLICY)
        # Regression: coordinates handed to the touchpad callback MUST NOT
        # be compared to the differently transformed compositor outline.
        self.assertNotIn('touchX < frame[0]', POLICY)
        self.assertNotIn('frame[4] != screenInfo.width', POLICY)
        self.assertIn('ViewConfiguration.getDoubleTapTimeout()', POLICY)
        self.assertIn('Math.abs(touchX - lastShardTouchTapX) <= tolerance', POLICY)
        self.assertIn('Math.abs(touchY - lastShardTouchTapY) <= tolerance', POLICY)
        self.assertIn('int tolerance = Math.max(20, screenInfo.width / 16);', POLICY)
        self.assertIn('lastShardTouchTapAt = repeated ? 0 : now;', POLICY)
        self.assertIn('lastShardTouchTapAt = 0;', POLICY)
        self.assertIn('lastHandheldScreen = null;', POLICY)
        # Keep native first-tap click forwarding and all handheld key controls.
        self.assertIn('pressPointerButtonLeft(finger1);', OVERLAY)
        self.assertIn('!getIntent().getBooleanExtra("touhou_desktop_window", false)', OVERLAY)
        self.assertNotIn('window.setWidth(', POLICY)

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

    def test_shard_native_desktop_minimum_without_resetting_any_container(self):
        # Shard requires at least a 960px-wide Windows desktop. Phone
        # automatic mode is otherwise 720x1280; change only Shard's launch
        # intent rather than persisting container settings or modifying game.
        self.assertIn('public static String resolutionForExecutable(', CORE)
        self.assertIn('CharoiteShardOfDreamsSupport.isExpansionGame(executable)', CORE)
        self.assertIn('isDesktopWindow(host)) return chosen;', CORE)
        self.assertIn('if (height <= width || width >= 960) return chosen;', CORE)
        self.assertIn('if (height <= 1280) return "960x1280";', CORE)
        self.assertIn('if (height <= 1600) return "960x1600";', CORE)
        self.assertIn('return "960x1920";', CORE)
        self.assertIn('CharoiteCore.resolutionForExecutable(host, executable)', SESSIONS)
        self.assertIn('960x1280|960x1600|960x1920', OVERLAY)
        self.assertNotIn('setScreenSize(', SESSIONS)

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

"""Regression gates for Touhou 8 touchscreen input and purple handheld."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
UI = (ROOT / "charoite-core/CharoiteTpdpTouchControls.java").read_text()
INPUT = (ROOT / "charoite-core/CharoiteLegacyKeyboard.java").read_text()
PROFILE = (ROOT / "charoite-core/CharoiteGameControlProfiles.java").read_text()
OVERLAY = (ROOT / "overlay.py").read_text()


class PurpleHandheldInputContract(unittest.TestCase):
    def test_shell_hides_white_wine_desktop_without_covering_game(self):
        self.assertIn('private void drawShell(Canvas canvas, RectF screen)', UI)
        self.assertIn('drawShell(canvas, bounds);', UI)
        for piece in ('canvas.drawRect(0, 0, w, top, shell)',
                      'canvas.drawRect(0, bottom, w, h, shell)',
                      'canvas.drawRect(0, top, left, bottom, shell)',
                      'canvas.drawRect(right, top, w, bottom, shell)'):
            self.assertIn(piece, UI)
        self.assertIn('Shader.TileMode.CLAMP', UI)
        self.assertIn('new int[]{0xF0271643, 0xE84D3074, 0xF01A102E}', UI)
        self.assertIn('setClickable(false)', UI)
        self.assertNotIn('root.setBackgroundColor(Color.WHITE)', UI)

    def test_equal_sized_dpad_and_centered_cross(self):
        for clause in (
            'position(up, dpadCenterX, dpadCenterY - size - gap, size, size)',
            'position(down, dpadCenterX, dpadCenterY + size + gap, size, size)',
            'position(left, dpadCenterX - size - gap, dpadCenterY, size, size)',
            'position(right, dpadCenterX + size + gap, dpadCenterY, size, size)'
        ):
            self.assertIn(clause, UI)
        self.assertIn('position(dpadPlate, dpadX - dp(host, 3)', UI)
        self.assertIn('position(facePlate, diamondX - dp(host, 3)', UI)

    def test_game_detection_excludes_setup_and_reuses_shmup_profile(self):
        self.assertIn('public static boolean isTouhou8Executable(String path)', PROFILE)
        for name in ('name.startsWith("th08")', 'name.endsWith(".exe")',
                     '!name.contains("config")', '!name.contains("setup")',
                     '!name.contains("install")'):
            self.assertIn(name, PROFILE)
        self.assertIn('if (isTouhou8Executable(path)) return "touhou_shmup";', PROFILE)
        self.assertIn('return CharoiteGameControlProfiles.isTouhou8Executable(executable);', INPUT)

    def test_keyboard_mode_can_be_changed_without_affecting_other_games(self):
        for token in ('public static final int DUAL = 0;',
                      'public static final int WIN32_ONLY = 1;',
                      'public static final int X11_ONLY = 2;',
                      'public static boolean useWin32()',
                      'public static boolean useX11()',
                      'restoreX11Focus(xServer);'):
            self.assertIn(token, INPUT)
        self.assertIn('if (touhou8 && com.charoitegames.core', OVERLAY)
        self.assertIn('if (!touhou8 || com.charoitegames.core', OVERLAY)
        self.assertIn('final Button backend = touhou8 ? button(host, "INPUT: DUAL"', UI)
        self.assertIn('CharoiteLegacyKeyboard.nextMode()', UI)
        self.assertIn('final TextView inputStatus = touhou8 ?', UI)
        self.assertIn('keyboard.setVisibility(show ? View.VISIBLE : View.GONE);', UI)
        self.assertIn('inputStatus.setVisibility(show ? View.VISIBLE : View.GONE);', UI)


if __name__ == "__main__":
    unittest.main()

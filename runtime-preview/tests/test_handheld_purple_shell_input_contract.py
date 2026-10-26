"""Regression gates for Touhou 8 touchscreen input and purple handheld."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
UI = (ROOT / "charoite-core/CharoiteTpdpTouchControls.java").read_text()
INPUT = (ROOT / "charoite-core/CharoiteLegacyKeyboard.java").read_text()
PROFILE = (ROOT / "charoite-core/CharoiteGameControlProfiles.java").read_text()
OVERLAY = (ROOT / "overlay.py").read_text()


class PurpleHandheldInputContract(unittest.TestCase):
    def test_translucent_shell_covers_desktop_but_not_game(self):
        self.assertIn('private void drawShell(Canvas canvas, RectF screen)', UI)
        self.assertIn('drawShell(canvas, bounds);', UI)
        self.assertIn('canvas.clipOutRect(', UI)
        self.assertIn('shell.setColor(0xFF191325);', UI)
        self.assertIn('CharoiteHardwareSkin.drawInterior(canvas, (Activity)getContext(), w, h);', UI)
        self.assertIn('new int[]{0xA0664598, 0x66392165, 0xB04F327D}', UI)
        self.assertIn('Shader.TileMode.CLAMP', UI)
        self.assertIn('setClickable(false)', UI)
        self.assertNotIn('root.setBackgroundColor(Color.WHITE)', UI)

    def test_real_model_photo_over_generic_hardware_illustration(self):
        skin=(ROOT / 'charoite-core/CharoiteHardwareSkin.java').read_text()
        self.assertIn('Build.MODEL', skin)
        self.assertIn('Build.MANUFACTURER', skin)
        self.assertIn('modelKey() + ".png"', skin)
        self.assertIn('Intent.ACTION_OPEN_DOCUMENT', skin)
        self.assertIn('drawBitmap(image, source', skin)
        self.assertNotIn('drawCircuitArtwork', UI)
        self.assertIn('CharoiteHardwareSkin.choosePicture(host)', UI)
        self.assertIn('CharoiteHardwareSkin.onImageSelected(', OVERLAY)
        self.assertNotIn('inputStatus', UI)

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
                      'public static boolean useScan()',
                      'public static final int SCAN_ONLY = 3;',
                      'restoreX11Focus(xServer);'):
            self.assertIn(token, INPUT)
        self.assertIn('if (touhou8 && com.charoitegames.core', OVERLAY)
        self.assertIn('if (!touhou8 || com.charoitegames.core', OVERLAY)
        self.assertIn('final Button backend = touhou8 ? button(host, "INPUT: DUAL"', UI)
        self.assertIn('CharoiteLegacyKeyboard.nextMode()', UI)
        self.assertIn('final Button diagnostics = touhou8 ?', UI)
        self.assertIn('CharoiteLegacyKeyboard.diagnosticReport(', UI)
        self.assertIn('CharoiteLegacyKeyboard.recordX11(keyCode, pressed)', OVERLAY)
        self.assertIn('isCharoiteKeyboardReady()', OVERLAY)
        self.assertIn('keyboard.setVisibility(show ? View.VISIBLE : View.GONE);', UI)
        self.assertIn('CharoiteLegacyKeyboard.sendScan(', OVERLAY)

    def test_focus_targets_nested_actual_game_window(self):
        for clause in ('handheldGameClientId()', 'pending.add(wm.rootWindow)',
                       'for (Window child : candidate.getChildren())',
                       'wm.setFocus(game, WindowManager.FocusRevertTo.POINTER_ROOT)',
                       'handler.isCharoiteKeyboardReady()',
                       'handler.bringToFront(new File(executable).getName())'):
            self.assertIn(clause, INPUT)
        self.assertIn('return generalGameClientId;', (
            ROOT / 'charoite-core/CharoiteWindowPolicy.java').read_text())



if __name__ == "__main__":
    unittest.main()

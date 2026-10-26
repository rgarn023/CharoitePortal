"""Regression: original Touhou 8 buttons use a Windows keyboard backend.

Old Touhou 8 may read Win32 / DirectInput key state even when its X11
window has lost focus. This source contract keeps the change limited to
known Touhou 8 game variants and protects TPDP's existing X11 path.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INPUT = (ROOT / "charoite-core/CharoiteLegacyKeyboard.java").read_text()
OVERLAY = (ROOT / "overlay.py").read_text()
PROFILE = (ROOT / "charoite-core/CharoiteGameControlProfiles.java").read_text()
CONTROLS = (ROOT / "charoite-core/CharoiteTpdpTouchControls.java").read_text()

class Touhou8InputContract(unittest.TestCase):
    def test_th08_only_windows_keyboard_bridge(self):
        self.assertIn('CharoiteGameControlProfiles.isTouhou8Executable(executable)', INPUT)
        self.assertNotIn('"gn_enbu.exe".equals(', INPUT)
        self.assertNotIn('"enbu_ap.exe".equals(', INPUT)
        self.assertIn('handler.keyboardEvent((byte) vk, flags);', INPUT)
        self.assertIn('handler.bringToFront(new File(executable).getName());', INPUT)
        self.assertIn('xServer.windowManager.getFocusedWindow()', INPUT)
        self.assertIn('public static boolean send(XServer xServer, String executable,', INPUT)
        self.assertIn('if (!requiresWindowsKeyboard(executable)', INPUT)
        self.assertIn('if (vk < 0 || handler == null) return false;', INPUT)
        self.assertIn('return true;', INPUT)
        self.assertNotIn('delete(', INPUT)
        self.assertNotIn('container.saveData(', INPUT)

    def test_win32_defaults_and_key_hold_semantics(self):
        expected = {
            'KEYCODE_DPAD_LEFT': '0x25',
            'KEYCODE_DPAD_UP': '0x26',
            'KEYCODE_DPAD_RIGHT': '0x27',
            'KEYCODE_DPAD_DOWN': '0x28',
            'KEYCODE_Z': '0x5A',
            'KEYCODE_X': '0x58',
            'KEYCODE_SHIFT_LEFT': '0x10',
            'KEYCODE_CTRL_LEFT': '0x11',
            'KEYCODE_ESCAPE': '0x1B',
            'KEYCODE_ENTER': '0x0D',
        }
        for key, vk in expected.items():
            self.assertIn('case KeyEvent.' + key + ': return ' + vk + ';', INPUT)
        self.assertIn('int flags = (pressed ? 0 : 0x0002)', INPUT)
        self.assertIn('vk >= 0x25 && vk <= 0x28 ? 0x0001 : 0', INPUT)
        self.assertIn('final Map<Integer, Integer> held = new HashMap<>();', CONTROLS)
        self.assertIn('if (count == 0) sink.send(code, true);', CONTROLS)
        self.assertIn('sink.send(code, false);', CONTROLS)
        self.assertIn('private static final int[] TOUHOU_SHMUP', PROFILE)

    def test_overlay_packs_backend_and_preserves_x11_fallback(self):
        self.assertIn('"CharoiteLegacyKeyboard.java"', OVERLAY)
        self.assertIn('CharoiteLegacyKeyboard.useWin32()', OVERLAY)
        self.assertIn('CharoiteLegacyKeyboard.useX11()', OVERLAY)
        self.assertIn('CharoiteLegacyKeyboard.send(', OVERLAY)
        self.assertIn('xServer.injectKeyPress(key);', OVERLAY)
        self.assertIn('xServer.injectKeyRelease(key);', OVERLAY)
        self.assertIn('CharoiteGameControlProfiles', OVERLAY)
        self.assertIn('getIntent().getStringExtra("exec_path")', OVERLAY)

if __name__ == "__main__":
    unittest.main()

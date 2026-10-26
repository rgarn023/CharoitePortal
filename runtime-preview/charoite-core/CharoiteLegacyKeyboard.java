package com.charoitegames.core;

import android.view.KeyEvent;
import com.winlator.winhandler.WinHandler;
import com.winlator.xserver.XServer;
import java.io.File;
import java.util.Locale;

/**
 * Compatibility input for original Touhou 8 / th08.exe (2004).
 *
 * The normal Core gamepad sends held X11 key events. Legacy DirectInput games
 * may poll Win32 key state instead, and an X11 event can be dropped when the
 * pinned XServer's focused window is the desktop or null. For th08.exe,
 * use the upstream winhandler.exe Windows keyboard-event bridge, keeping
 * genuine key-down/key-up and simultaneous key holds.
 *
 * Scope is deliberately th08.exe ONLY. TPDP, modern games and installers
 * retain the existing X11 keyboard path. Never modifies Wine DLLs, game
 * settings, game files or saves.
 */
public final class CharoiteLegacyKeyboard {
    private CharoiteLegacyKeyboard() {}

    public static boolean requiresWindowsKeyboard(String executable) {
        return executable != null &&
                "th08.exe".equals(new File(executable).getName().toLowerCase(Locale.ROOT));
    }

    /** Win32 virtual-key values; KEYEVENTF_KEYUP = 0x0002. */
    public static int virtualKey(int androidKey) {
        switch (androidKey) {
            case KeyEvent.KEYCODE_DPAD_LEFT: return 0x25;  // VK_LEFT
            case KeyEvent.KEYCODE_DPAD_UP: return 0x26;    // VK_UP
            case KeyEvent.KEYCODE_DPAD_RIGHT: return 0x27; // VK_RIGHT
            case KeyEvent.KEYCODE_DPAD_DOWN: return 0x28;  // VK_DOWN
            case KeyEvent.KEYCODE_Z: return 0x5A;
            case KeyEvent.KEYCODE_X: return 0x58;
            case KeyEvent.KEYCODE_C: return 0x43;
            case KeyEvent.KEYCODE_V: return 0x56;
            case KeyEvent.KEYCODE_A: return 0x41;
            case KeyEvent.KEYCODE_S: return 0x53;
            case KeyEvent.KEYCODE_D: return 0x44;
            case KeyEvent.KEYCODE_P: return 0x50;
            case KeyEvent.KEYCODE_SHIFT_LEFT: return 0x10; // VK_SHIFT
            case KeyEvent.KEYCODE_CTRL_LEFT: return 0x11;  // VK_CONTROL
            case KeyEvent.KEYCODE_ENTER: return 0x0D;
            case KeyEvent.KEYCODE_ESCAPE: return 0x1B;
            case KeyEvent.KEYCODE_SPACE: return 0x20;
            case KeyEvent.KEYCODE_F11: return 0x7A;
            default: return -1;
        }
    }

    /** Returns false to retain the regular X11 path when not applicable. */
    public static boolean send(XServer xServer, String executable,
                               int androidKey, boolean pressed) {
        if (!requiresWindowsKeyboard(executable) || xServer == null) return false;
        int vk = virtualKey(androidKey);
        WinHandler handler = xServer.getWinHandler();
        if (vk < 0 || handler == null) return false;
        // The Android on-screen buttons are not X11 pointer presses.
        // The pinned XServer can have no focused game window after a Wine
        // fullscreen transition; recover the actual Win32 foreground window.
        // Do not refocus on every shot/move while focus is already valid.
        if (pressed && (xServer.windowManager.getFocusedWindow() == null ||
                xServer.windowManager.getFocusedWindow() ==
                        xServer.windowManager.rootWindow))
            handler.bringToFront("th08.exe");
        // The arrow cluster uses extended keyboard scan codes on Windows.
        // KEYEVENTF_EXTENDEDKEY=1 and KEYEVENTF_KEYUP=2.
        int flags = (pressed ? 0 : 0x0002) |
                (vk >= 0x25 && vk <= 0x28 ? 0x0001 : 0);
        handler.keyboardEvent((byte) vk, flags);
        return true;
    }
}

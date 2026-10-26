package com.charoitegames.core;

import android.view.KeyEvent;
import com.winlator.winhandler.WinHandler;
import com.winlator.xserver.XServer;
import com.winlator.xserver.XLock;
import com.winlator.xserver.Window;
import com.winlator.xserver.WindowManager;
import java.io.File;

/**
 * Compatibility input for original Touhou 8 / th08.exe (2004).
 *
 * The normal Core gamepad sends held X11 key events. Legacy DirectInput games
 * may poll Win32 key state instead, and an X11 event can be dropped when the
 * pinned XServer's focused window is the desktop or null. For th08.exe,
 * use the upstream winhandler.exe Windows keyboard-event bridge, keeping
 * genuine key-down/key-up and simultaneous key holds.
 *
 * Scope is deliberately Touhou 8 executables ONLY. The user can switch
 * between Dual, Win32 and X11 on the More controls if one backend does not
 * reach their patched game. TPDP and other games retain their existing input.
 * Never modifies Wine DLLs, game settings, game files or saves.
 */
public final class CharoiteLegacyKeyboard {
    public static final int DUAL = 0;
    public static final int WIN32_ONLY = 1;
    public static final int X11_ONLY = 2;
    private static volatile int inputMode = DUAL;

    private CharoiteLegacyKeyboard() {}

    public static boolean requiresWindowsKeyboard(String executable) {
        return CharoiteGameControlProfiles.isTouhou8Executable(executable);
    }

    public static void resetMode() { inputMode = DUAL; }
    public static int nextMode() {
        inputMode = (inputMode + 1) % 3;
        return inputMode;
    }
    public static boolean useWin32() { return inputMode != X11_ONLY; }
    public static boolean useX11() { return inputMode != WIN32_ONLY; }
    public static String modeLabel() {
        return inputMode == WIN32_ONLY ? "WIN32" :
                inputMode == X11_ONLY ? "X11" : "DUAL";
    }

    /** X11 and Win32 can lose input focus independently after fullscreen.
     * Recover only if XServer currently reports no focused app, and never
     * steal focus from a valid dialog or another active window.
     */
    private static void restoreX11Focus(XServer xServer) {
        try (XLock lock = xServer.lock(XServer.Lockable.WINDOW_MANAGER,
                XServer.Lockable.INPUT_DEVICE)) {
            WindowManager wm = xServer.windowManager;
            Window focused = wm.getFocusedWindow();
            if (focused != null && focused != wm.rootWindow) return;
            Window candidate = null;
            for (Window child : wm.rootWindow.getChildren()) {
                if (!child.isRenderable() || child.isDesktopWindow()) continue;
                String name = child.getClassName().toLowerCase(java.util.Locale.ROOT);
                if (name.contains("th08")) {
                    candidate = child;
                    break;
                }
                if (candidate == null && child.isApplicationWindow()) candidate = child;
            }
            if (candidate != null)
                wm.setFocus(candidate, WindowManager.FocusRevertTo.POINTER_ROOT);
        }
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
        if (pressed) {
            boolean missingFocus = xServer.windowManager.getFocusedWindow() == null ||
                    xServer.windowManager.getFocusedWindow() ==
                            xServer.windowManager.rootWindow;
            if (missingFocus) {
                restoreX11Focus(xServer);
                // The executable may be th08e.exe or a renamed translation.
                handler.bringToFront(new File(executable).getName());
            }
        }
        // Win32 KEYEVENTF_EXTENDEDKEY=1 (arrows), KEYEVENTF_KEYUP=2.
        int flags = (pressed ? 0 : 0x0002) |
                (vk >= 0x25 && vk <= 0x28 ? 0x0001 : 0);
        handler.keyboardEvent((byte) vk, flags);
        return true;
    }
}

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

    private static volatile String focusStatus = "Focus not checked";
    private static volatile String bridgeStatus = "Bridge not checked";
    private static volatile String x11Status = "X11 not checked";

    /** Scan nested Wine windows, not only root's direct children. */
    private static Window findGameWindow(WindowManager wm) {
        java.util.ArrayDeque<Window> pending = new java.util.ArrayDeque<>();
        pending.add(wm.rootWindow);
        int selected = CharoiteWindowPolicy.handheldGameClientId();
        Window matching = null, fallback = null;
        long maxSize = 0;
        while (!pending.isEmpty()) {
            Window candidate = pending.removeFirst();
            for (Window child : candidate.getChildren()) pending.addLast(child);
            if (candidate == wm.rootWindow || !candidate.isRenderable() ||
                    candidate.isDesktopWindow() || candidate.isDialogBox() ||
                    candidate.getWidth() < 300 || candidate.getHeight() < 180) continue;
            if (selected != -1 && selected == candidate.id) return candidate;
            String clazz = candidate.getClassName().toLowerCase(java.util.Locale.ROOT);
            String title = candidate.getName().toLowerCase(java.util.Locale.ROOT);
            if (clazz.contains("th08") || title.contains("imperishable") ||
                    title.contains("東方永夜抄")) matching = candidate;
            long size = (long)candidate.getWidth() * candidate.getHeight();
            if (candidate.getChildCount() == 0 && size > maxSize) {
                fallback = candidate;
                maxSize = size;
            }
        }
        return matching != null ? matching : fallback;
    }

    private static void restoreX11Focus(XServer xServer) {
        if (xServer == null) return;
        try (XLock lock = xServer.lock(XServer.Lockable.WINDOW_MANAGER,
                XServer.Lockable.INPUT_DEVICE)) {
            WindowManager wm = xServer.windowManager;
            Window focused = wm.getFocusedWindow();
            if (focused != null && focused.isDialogBox()) {
                focusStatus = "Windows dialog has focus";
                return;
            }
            Window game = findGameWindow(wm);
            if (game == null) {
                focusStatus = "No mapped game client available";
                return;
            }
            if (focused != game)
                wm.setFocus(game, WindowManager.FocusRevertTo.POINTER_ROOT);
            focusStatus = "X11 game client focused: " + game.id;
        } catch (RuntimeException error) {
            focusStatus = "Focus error: " + error.getClass().getSimpleName();
            android.util.Log.w("CharoiteInput", focusStatus, error);
        }
    }

    public static void prepareX11Focus(XServer xServer, String executable) {
        if (requiresWindowsKeyboard(executable)) restoreX11Focus(xServer);
    }

    /** Opt-in MORE diagnostic, not an overlay above the playing field. */
    public static String diagnosticReport(XServer xServer) {
        WinHandler handler = xServer == null ? null : xServer.getWinHandler();
        boolean ready = handler != null && handler.isCharoiteKeyboardReady();
        return "Touhou 8 input: " + modeLabel() +
                "\nWin32 bridge: " + (ready ? "ready" : "not initialized") +
                "\n" + bridgeStatus + "\n" + x11Status + "\n" + focusStatus +
                "\nKey injection does not guarantee the game received it.";
    }

    public static void recordX11(int key, boolean pressed) {
        x11Status = "X11 " + CharoiteGameControlProfiles.label(key) +
                (pressed ? " down" : " up");
        android.util.Log.d("CharoiteInput", x11Status);
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

    /** Only report queued input after the Wine keyboard bridge initializes. */
    public static boolean send(XServer xServer, String executable,
                               int androidKey, boolean pressed) {
        if (!requiresWindowsKeyboard(executable) || xServer == null) return false;
        int vk = virtualKey(androidKey);
        WinHandler handler = xServer.getWinHandler();
        if (vk < 0 || handler == null || !handler.isCharoiteKeyboardReady()) {
            bridgeStatus = "Win32 unavailable; X11 fallback enabled";
            android.util.Log.w("CharoiteInput", bridgeStatus);
            return false;
        }
        if (pressed) {
            restoreX11Focus(xServer);
            handler.bringToFront(new File(executable).getName());
        }
        int flags = (pressed ? 0 : 0x0002) |
                (vk >= 0x25 && vk <= 0x28 ? 0x0001 : 0);
        handler.keyboardEvent((byte)vk, flags);
        bridgeStatus = "Win32 queued " +
                CharoiteGameControlProfiles.label(androidKey) +
                (pressed ? " down" : " up");
        android.util.Log.d("CharoiteInput", bridgeStatus);
        return true;
    }

}

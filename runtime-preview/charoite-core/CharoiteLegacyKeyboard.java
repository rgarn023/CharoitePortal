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
    public static final int SCAN_ONLY = 3;
    private static volatile int inputMode = DUAL;

    private CharoiteLegacyKeyboard() {}

    public static boolean requiresWindowsKeyboard(String executable) {
        return CharoiteGameControlProfiles.isTouhou8Executable(executable);
    }

    public static void resetMode() { inputMode = DUAL; }
    public static int nextMode() {
        inputMode = (inputMode + 1) % 4;
        return inputMode;
    }
    public static boolean useWin32() { return inputMode == DUAL || inputMode == WIN32_ONLY; }
    public static boolean useX11() { return inputMode == DUAL || inputMode == X11_ONLY; }
    public static boolean useScan() { return inputMode == DUAL || inputMode == SCAN_ONLY; }
    public static String modeLabel() {
        return inputMode == WIN32_ONLY ? "WIN32" :
                inputMode == X11_ONLY ? "X11" :
                inputMode == SCAN_ONLY ? "SCAN" : "DUAL";
    }

    private static volatile String focusStatus = "Focus not checked";
    private static volatile String bridgeStatus = "Bridge not checked";
    private static volatile String x11Status = "X11 not checked";

    /**
     * Winlator's X11 key dispatcher does not deliver a key merely because a
     * window has focus. Its InputDeviceManager also requires an enabled
     * window subscribed to KEY_PRESS/KEY_RELEASE. The prior implementation
     * selected a renderable GL drawable regardless of keyboard event masks;
     * the diagnostic could say "focused" while every key was discarded.
     */
    private static boolean acceptsX11Keys(Window window) {
        return window != null && window.attributes.isEnabled() &&
                window.attributes.isMapped() &&
                window.hasEventListenerFor(com.winlator.xserver.events.Event.KEY_PRESS) &&
                window.hasEventListenerFor(com.winlator.xserver.events.Event.KEY_RELEASE);
    }

    private static Window findGameWindow(WindowManager wm) {
        java.util.ArrayDeque<Window> pending = new java.util.ArrayDeque<>();
        pending.add(wm.rootWindow);
        final int selected = CharoiteWindowPolicy.handheldGameClientId();
        Window chosen = null;
        long best = -1;
        while (!pending.isEmpty()) {
            Window window = pending.removeFirst();
            for (Window child : window.getChildren()) pending.addLast(child);
            if (window == wm.rootWindow || window.isDesktopWindow() ||
                    window.isDialogBox() || !acceptsX11Keys(window)) continue;
            String clazz = window.getClassName().toLowerCase(java.util.Locale.ROOT);
            String title = window.getName().toLowerCase(java.util.Locale.ROOT);
            long score = 0;
            if (window.id == selected) score += 10000000L;
            if (clazz.contains("th08") || title.contains("imperishable") ||
                    title.contains("東方永夜抄")) score += 1000000L;
            if (window.isApplicationWindow()) score += 100000L;
            if (window.isRenderable()) score += 10000L;
            score += Math.min(9999, (long)window.getWidth()*window.getHeight()/256);
            if (score > best) { best = score; chosen = window; }
        }
        return chosen;
    }

    private static void restoreX11Focus(XServer xServer) {
        if (xServer == null) return;
        try (XLock lock = xServer.lock(XServer.Lockable.WINDOW_MANAGER,
                XServer.Lockable.INPUT_DEVICE)) {
            WindowManager wm = xServer.windowManager;
            Window focused = wm.getFocusedWindow();
            if (focused != null && focused.isDialogBox()) {
                focusStatus = "Active Wine dialog retained";
                return;
            }
            // Respect a valid existing keyboard focus: scanning over it can
            // steal keys from the actual DirectInput game window.
            if (acceptsX11Keys(focused) && !focused.isDesktopWindow()) {
                focusStatus = "X11 keyboard subscriber #" + focused.id + " active";
                return;
            }
            Window game = findGameWindow(wm);
            if (game == null) {
                focusStatus = "NO enabled X11 key-event subscriber";
                android.util.Log.w("CharoiteInput", focusStatus);
                return;
            }
            if (focused != game)
                wm.setFocus(game, WindowManager.FocusRevertTo.POINTER_ROOT);
            focusStatus = "X11 key-event subscriber focused #" + game.id;
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
                "\nHelper: " + scanInstallPath +
                "\nScan: " + scanStatus +
                "\nScan acknowledged: " + scanAcknowledged +
                "\nKey injection does not guarantee the game received it.";
    }

    public static void recordX11(int key, boolean pressed) {
        x11Status = "X11 " + CharoiteGameControlProfiles.label(key) +
                (pressed ? " down" : " up");
        android.util.Log.d("CharoiteInput", x11Status);
    }

    private static volatile String scanInstallPath = "Not installed";

    private static final java.util.concurrent.ExecutorService scanSender =
            java.util.concurrent.Executors.newSingleThreadExecutor();
    private static volatile String scanStatus = "Scan bridge not started";
    private static volatile boolean scanAcknowledged = false;
    private static volatile boolean scanPrepared = false;
    private static final int SCAN_PORT = 7949;

    /**
     * Start the independently compiled Wine-side SendInput scan-code receiver.
     * This is a separate compatibility path: DirectInput may ignore a virtual
     * key event while accepting an actual scan-code key transition.
     * Queue through WinHandler.exec: Wine itself chooses the container.
     */
    public static synchronized void prepareScanBridge(android.app.Activity host,
                                                       XServer xServer) {
        if (scanPrepared || !(host instanceof com.winlator.XServerDisplayActivity) ||
                xServer == null) return;
        WinHandler handler = xServer.getWinHandler();
        com.winlator.container.Container container =
                ((com.winlator.XServerDisplayActivity)host).getContainer();
        if (handler == null || container == null || container.getRootDir() == null) {
            scanStatus = "Game container not available for scan helper";
            return;
        }
        try {
            // The guest's Z: drive is rooted in its own chroot, not Android's
            // /data/user/0/... directory. Copy into this environment's REAL
            // C: drive instead; do not assume Android paths are Wine-visible.
            java.io.File target = new java.io.File(container.getRootDir(),
                    ".wine/drive_c/CharoitePortal/Core/charoite_keyscan.exe");
            java.io.File parent = target.getParentFile();
            if (parent == null || (!parent.isDirectory() && !parent.mkdirs()))
                throw new java.io.IOException("Cannot create Wine Core directory");
            // Refresh on each app update. Atomic replacement avoids a torn EXE.
            java.io.File pending = new java.io.File(parent, "charoite_keyscan.new");
            try (java.io.InputStream input = host.getAssets().open(
                    "input/charoite_keyscan.exe");
                 java.io.FileOutputStream output = new java.io.FileOutputStream(pending)) {
                byte[] buffer = new byte[8192];
                int n;
                while ((n = input.read(buffer)) != -1) output.write(buffer, 0, n);
            }
            if (!pending.renameTo(target)) {
                if (!target.delete() || !pending.renameTo(target))
                    throw new java.io.IOException("Cannot replace Wine scan helper");
            }
            if (target.length() < 5000)
                throw new java.io.IOException("Invalid Wine scan helper");
            String winePath = "C:\\CharoitePortal\\Core\\charoite_keyscan.exe";
            scanInstallPath = winePath + " (" + target.length() + " bytes)";
            handler.exec(winePath, "");
            scanPrepared = true;
            scanStatus = "Scan helper launch requested inside Wine container";
            android.util.Log.i("CharoiteInput", scanStatus + ": " + scanInstallPath);
        } catch (Exception error) {
            scanStatus = "Scan helper setup failed: " + error.getClass().getSimpleName();
            android.util.Log.w("CharoiteInput", scanStatus, error);
        }
    }

    /** Send a fixed protocol packet and await the *Windows process* ACK.
     * All UDP traffic runs off the Android main thread, in key event order.
     */
    public static void sendScan(int code, boolean pressed) {
        int vk = virtualKey(code);
        if (vk < 0) return;
        scanSender.execute(() -> {
            byte[] packet = {(byte)'C',(byte)'K',(byte)'S',(byte)'1',
                             (byte)vk, (byte)(pressed ? 1 : 0)};
            try (java.net.DatagramSocket socket = new java.net.DatagramSocket()) {
                socket.setSoTimeout(180);
                java.net.InetAddress loopback =
                        java.net.InetAddress.getByName("127.0.0.1");
                java.net.DatagramPacket request = new java.net.DatagramPacket(
                        packet, packet.length, loopback, SCAN_PORT);
                // The first press can race Wine's startup; retry only DOWN.
                for (int attempt = 0; attempt < (pressed ? 3 : 1); attempt++) {
                    socket.send(request);
                    byte[] response = new byte[5];
                    java.net.DatagramPacket ack = new java.net.DatagramPacket(
                            response, response.length);
                    try {
                        socket.receive(ack);
                        if (ack.getLength() == 5 && response[0] == 'C' &&
                                response[1] == 'K' && response[2] == 'A' &&
                                response[3] == '1') {
                            scanAcknowledged = response[4] == '1';
                            scanStatus = scanAcknowledged ?
                                    "Wine SendInput scan-code ACK received" :
                                    "Wine SendInput returned failure";
                            android.util.Log.d("CharoiteInput", scanStatus);
                            return;
                        }
                    } catch (java.net.SocketTimeoutException timeout) {
                        // Retry a key down while Wine initializes.
                    }
                }
                scanStatus = "No scan-code receiver ACK (check Wine launch)";
            } catch (Exception error) {
                scanStatus = "Scan path error: " + error.getClass().getSimpleName();
                android.util.Log.w("CharoiteInput", scanStatus, error);
            }
        });
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

package com.charoitegames.core;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.view.KeyEvent;
import androidx.appcompat.app.AlertDialog;
import com.winlator.xserver.XKeycode;
import java.io.File;
import java.util.Locale;

/**
 * Core-owned keyboard profiles selected from an installed game's executable.
 * Windows executables have no universal "default controls" manifest: known
 * games use documented defaults, unknown games use a configurable fallback.
 * Nothing here edits the Windows EXE, game configuration or save files.
 */
public final class CharoiteGameControlProfiles {
    private CharoiteGameControlProfiles() {}

    // Identifiers are stable across the gamepad and per-game override store.
    public static final String[] BUTTONS = {
        "Esc", "Select", "Start", "Enter", "L", "R",
        "Up", "Left", "Right", "Down", "Y", "X", "A", "B"
    };
    private static final int[] TPDP = {
        KeyEvent.KEYCODE_ESCAPE, KeyEvent.KEYCODE_SHIFT_LEFT,
        KeyEvent.KEYCODE_SPACE, KeyEvent.KEYCODE_ENTER,
        KeyEvent.KEYCODE_A, KeyEvent.KEYCODE_D,
        KeyEvent.KEYCODE_DPAD_UP, KeyEvent.KEYCODE_DPAD_LEFT,
        KeyEvent.KEYCODE_DPAD_RIGHT, KeyEvent.KEYCODE_DPAD_DOWN,
        KeyEvent.KEYCODE_S, KeyEvent.KEYCODE_C,
        KeyEvent.KEYCODE_Z, KeyEvent.KEYCODE_X
    };
    // Original PC Touhou shmup defaults: arrows, Z shot/confirm, X bomb/
    // cancel, Shift focus, Ctrl dialogue skip, Esc pause.
    // Extra buttons duplicate these known inputs, not arbitrary V/Space.
    private static final int[] TOUHOU_SHMUP = {
        KeyEvent.KEYCODE_ESCAPE, KeyEvent.KEYCODE_CTRL_LEFT,
        KeyEvent.KEYCODE_Z, KeyEvent.KEYCODE_ENTER,
        KeyEvent.KEYCODE_SHIFT_LEFT, KeyEvent.KEYCODE_CTRL_LEFT,
        KeyEvent.KEYCODE_DPAD_UP, KeyEvent.KEYCODE_DPAD_LEFT,
        KeyEvent.KEYCODE_DPAD_RIGHT, KeyEvent.KEYCODE_DPAD_DOWN,
        KeyEvent.KEYCODE_CTRL_LEFT, KeyEvent.KEYCODE_SHIFT_LEFT,
        KeyEvent.KEYCODE_Z, KeyEvent.KEYCODE_X
    };
    private static final int[] FALLBACK = {
        KeyEvent.KEYCODE_ESCAPE, KeyEvent.KEYCODE_SHIFT_LEFT,
        KeyEvent.KEYCODE_ENTER, KeyEvent.KEYCODE_ENTER,
        KeyEvent.KEYCODE_SHIFT_LEFT, KeyEvent.KEYCODE_SPACE,
        KeyEvent.KEYCODE_DPAD_UP, KeyEvent.KEYCODE_DPAD_LEFT,
        KeyEvent.KEYCODE_DPAD_RIGHT, KeyEvent.KEYCODE_DPAD_DOWN,
        KeyEvent.KEYCODE_C, KeyEvent.KEYCODE_V,
        KeyEvent.KEYCODE_Z, KeyEvent.KEYCODE_X
    };

    /** Recognize the original Touhou 8 game and common translated executables.
     * Explicitly exclude configuration utilities and installers.
     */
    public static boolean isTouhou8Executable(String path) {
        String name = new File(path == null ? "" : path).getName().toLowerCase(Locale.ROOT);
        return (name.startsWith("th08") &&
                name.endsWith(".exe") &&
                !name.contains("config") && !name.contains("setup") &&
                !name.contains("install")) ||
                name.equals("imperishable-night.exe") ||
                name.equals("imperishable_night.exe");
    }

    public static String idForExecutable(String path) {
        String name = new File(path == null ? "" : path).getName().toLowerCase(Locale.ROOT);
        if (CharoiteCore.isTpdpGameExecutable(path)) return "tpdp";
        if (isTouhou8Executable(path)) return "touhou_shmup";
        // Known PC bullet-hell Touhou releases. Fighting spin-offs are not
        // included: a name match for every "th*.exe" would be misleading.
        if (name.matches("th(0[6789]|1[0-9]|20)\\.exe") &&
                !name.matches("th(10|12|13|14|15|16|17|18|19|20)\\.exe")) {
            return "touhou_shmup";
        }
        if (name.matches("th(10|11|12|13|14|15|16|17|18|19|20)\\.exe"))
            return "touhou_shmup";
        return "generic_unverified";
    }

    private static int[] defaults(String path) {
        switch (idForExecutable(path)) {
            case "tpdp": return TPDP;
            case "touhou_shmup": return TOUHOU_SHMUP;
            default: return FALLBACK;
        }
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences("charoite_game_controls", Context.MODE_PRIVATE);
    }

    private static String key(String path, int button) {
        // Full executable path scopes settings to one installation/realm.
        return (path == null ? "" : path.replace('\\', '/').toLowerCase(Locale.ROOT)) +
                "|" + button;
    }

    public static int keyFor(Context context, String path, int button) {
        if (button < 0 || button >= BUTTONS.length)
            throw new IllegalArgumentException("Invalid gamepad button");
        int fallback = defaults(path)[button];
        return prefs(context).getInt(key(path, button), fallback);
    }

    public static void setKey(Context context, String path, int button, int code) {
        if (button < 0 || button >= BUTTONS.length || toXKeycode(code) == null)
            throw new IllegalArgumentException("Unsupported gamepad mapping");
        prefs(context).edit().putInt(key(path, button), code).apply();
    }

    public static void reset(Context context, String path) {
        SharedPreferences.Editor editor = prefs(context).edit();
        for (int i = 0; i < BUTTONS.length; i++) editor.remove(key(path, i));
        editor.apply();
    }

    public static String label(int key) {
        switch (key) {
            case KeyEvent.KEYCODE_DPAD_UP: return "Up";
            case KeyEvent.KEYCODE_DPAD_DOWN: return "Down";
            case KeyEvent.KEYCODE_DPAD_LEFT: return "Left";
            case KeyEvent.KEYCODE_DPAD_RIGHT: return "Right";
            case KeyEvent.KEYCODE_SHIFT_LEFT: return "Shift";
            case KeyEvent.KEYCODE_CTRL_LEFT: return "Ctrl";
            case KeyEvent.KEYCODE_ENTER: return "Enter";
            case KeyEvent.KEYCODE_ESCAPE: return "Esc";
            case KeyEvent.KEYCODE_SPACE: return "Space";
            default: return KeyEvent.keyCodeToString(key).replace("KEYCODE_", "");
        }
    }

    /** Inject physical X11 keycodes directly; Android KeyEvent ACTION_UP
     * unconditionally releases Shift in the pinned runtime's Keyboard class,
     * breaking focus + shot when synthetic Android events are used.
     */
    public static XKeycode toXKeycode(int key) {
        switch (key) {
            case KeyEvent.KEYCODE_DPAD_UP: return XKeycode.KEY_UP;
            case KeyEvent.KEYCODE_DPAD_DOWN: return XKeycode.KEY_DOWN;
            case KeyEvent.KEYCODE_DPAD_LEFT: return XKeycode.KEY_LEFT;
            case KeyEvent.KEYCODE_DPAD_RIGHT: return XKeycode.KEY_RIGHT;
            case KeyEvent.KEYCODE_ESCAPE: return XKeycode.KEY_ESC;
            case KeyEvent.KEYCODE_ENTER: return XKeycode.KEY_ENTER;
            case KeyEvent.KEYCODE_SPACE: return XKeycode.KEY_SPACE;
            case KeyEvent.KEYCODE_SHIFT_LEFT: return XKeycode.KEY_SHIFT_L;
            case KeyEvent.KEYCODE_CTRL_LEFT: return XKeycode.KEY_CTRL_L;
            case KeyEvent.KEYCODE_Z: return XKeycode.KEY_Z;
            case KeyEvent.KEYCODE_X: return XKeycode.KEY_X;
            case KeyEvent.KEYCODE_C: return XKeycode.KEY_C;
            case KeyEvent.KEYCODE_V: return XKeycode.KEY_V;
            case KeyEvent.KEYCODE_A: return XKeycode.KEY_A;
            case KeyEvent.KEYCODE_S: return XKeycode.KEY_S;
            case KeyEvent.KEYCODE_D: return XKeycode.KEY_D;
            case KeyEvent.KEYCODE_P: return XKeycode.KEY_P;
            case KeyEvent.KEYCODE_F11: return XKeycode.KEY_F11;
            default: return null;
        }
    }

    // Editable per-game fallback for unfamiliar executables or overridden
    // game settings. This avoids claiming that Windows EXEs expose a common
    // keyboard-mapping API. Profiles are re-resolved at each launch.
    private static final int[] CHOICES = {
        KeyEvent.KEYCODE_DPAD_UP, KeyEvent.KEYCODE_DPAD_DOWN,
        KeyEvent.KEYCODE_DPAD_LEFT, KeyEvent.KEYCODE_DPAD_RIGHT,
        KeyEvent.KEYCODE_Z, KeyEvent.KEYCODE_X, KeyEvent.KEYCODE_C,
        KeyEvent.KEYCODE_V, KeyEvent.KEYCODE_A, KeyEvent.KEYCODE_S,
        KeyEvent.KEYCODE_D, KeyEvent.KEYCODE_SHIFT_LEFT,
        KeyEvent.KEYCODE_CTRL_LEFT, KeyEvent.KEYCODE_ENTER,
        KeyEvent.KEYCODE_ESCAPE, KeyEvent.KEYCODE_SPACE,
        KeyEvent.KEYCODE_P, KeyEvent.KEYCODE_F11
    };

    public static void showEditor(Activity host, String path) {
        String[] options = new String[BUTTONS.length];
        for (int i = 0; i < options.length; i++)
            options[i] = BUTTONS[i] + " → " + label(keyFor(host, path, i));
        String profile = idForExecutable(path);
        new AlertDialog.Builder(host)
                .setTitle("Game controls — " + new File(path).getName())
                .setMessage(profile.equals("generic_unverified")
                        ? "Unknown game's controls cannot be read reliably from its EXE. These are editable fallback keys."
                        : "Documented default profile: " + profile + ". Changes affect this installation only.")
                .setItems(options, (d, index) -> showKeyPicker(host, path, index))
                .setNeutralButton("Restore defaults", (d, which) -> {
                    reset(host, path);
                    showEditor(host, path);
                })
                .setNegativeButton("Close", null)
                .show();
    }

    private static void showKeyPicker(Activity host, String path, int button) {
        String[] choices = new String[CHOICES.length];
        for (int i = 0; i < choices.length; i++) choices[i] = label(CHOICES[i]);
        new AlertDialog.Builder(host)
                .setTitle(BUTTONS[button] + " keyboard key")
                .setItems(choices, (dialog, selected) -> {
                    setKey(host, path, button, CHOICES[selected]);
                    showEditor(host, path);
                })
                .setNegativeButton("Back", (dialog, selected) -> showEditor(host, path))
                .show();
    }
}

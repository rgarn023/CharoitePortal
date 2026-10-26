package com.charoitegames.core;

import android.app.Activity;
import androidx.appcompat.app.AppCompatActivity;
import com.winlator.core.AppUtils;

/**
 * Reusable Charoite Core system-keyboard entry point for Windows sessions.
 *
 * Use the exact IME action already supported by the pinned XServer runtime.
 * Its keyboard handler forwards supported hardware/IME KeyEvents to Wine.
 * This does not install third-party keyboards, change Wine keysyms, move
 * the game window, or write any game files.
 */
public final class CharoiteSoftKeyboard {
    private CharoiteSoftKeyboard() {}

    public static void show(Activity host) {
        if (host == null || host.isFinishing() || host.isDestroyed()) return;
        if (host instanceof AppCompatActivity) {
            AppUtils.showKeyboard((AppCompatActivity) host);
        }
    }
}

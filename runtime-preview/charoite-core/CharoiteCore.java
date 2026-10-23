package com.charoitegames.core;

import android.content.Context;
import android.graphics.Rect;
import android.os.Build;
import android.view.Display;
import android.view.WindowMetrics;

import androidx.appcompat.app.AppCompatActivity;
import androidx.preference.PreferenceManager;

import com.winlator.SettingsFragment;
import com.winlator.box64.Box64Preset;
import com.winlator.container.Container;
import com.winlator.container.DXWrappers;
import com.winlator.container.GraphicsDrivers;
import com.winlator.core.DefaultVersion;
import com.winlator.core.TarCompressorUtils;
import com.winlator.xenvironment.RootFS;
import com.winlator.xenvironment.RootFSInstaller;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;

/**
 * Charoite Core v0.1: reusable Android game runtime policies.
 *
 * This is an in-app source module, NOT a new operating system or a separately
 * installed service. The current engine is the attributed Winlator-derived
 * Wine/Box64 runtime; this class coordinates it for launchers.
 *
 * Compatibility contract:
 * - retain the launcher Activity's original getPreferences(MODE_PRIVATE) keys;
 * - never delete, reset, or recreate a Wine prefix on APK refresh;
 * - keep game-specific installation and library UI outside Charoite Core;
 * - keep selecting a display size scoped to one launch, not the saved container.
 */
public final class CharoiteCore {
    public static final String VERSION = "0.4";
    public static final String[] DISPLAY_MODES = {
            "Automatic (recommended)", "1280 × 720", "1600 × 900",
            "1920 × 1080", "800 × 600 (compatibility)"
    };
    private static final String[] WINE_RESOLUTIONS = {
            "", "1280x720", "1600x900", "1920x1080", "800x600"
    };
    private static final String PREPARED_APK_KEY = "engine_prepared_apk_timestamp";
    private static final String DISPLAY_MODE_KEY = "game_display_mode";
    private static final String DESKTOP_CAPTURE_KEY = "desktop_pointer_capture";

    private CharoiteCore() {}
    /** Existing Touhou preference keys remain unchanged; other profiles isolate settings. */
    private static String scopedKey(AppCompatActivity host, String key) {
        return CharoiteEnvironments.isTouhou(host)
                ? key : "portal_" + CharoiteEnvironments.activeId(host) + "_" + key;
    }

    public static boolean compatibleGraphics(AppCompatActivity host) {
        return host.getPreferences(Context.MODE_PRIVATE)
                .getBoolean(scopedKey(host, "compat_graphics"), false);
    }

    public static void setCompatibleGraphics(AppCompatActivity host, boolean enabled) {
        host.getPreferences(Context.MODE_PRIVATE).edit()
                .putBoolean(scopedKey(host, "compat_graphics"), enabled).apply();
    }


    public static int getDisplayModeIndex(AppCompatActivity host) {
        int index = host.getPreferences(Context.MODE_PRIVATE).getInt(scopedKey(host, DISPLAY_MODE_KEY), 0);
        return (index >= 0 && index < DISPLAY_MODES.length) ? index : 0;
    }

    public static void setDisplayMode(AppCompatActivity host, int index) {
        if (index < 0 || index >= DISPLAY_MODES.length)
            throw new IllegalArgumentException("Unsupported game resolution");
        host.getPreferences(Context.MODE_PRIVATE).edit()
                .putInt(scopedKey(host, DISPLAY_MODE_KEY), index).apply();
    }

    public static boolean isDesktopWindow(AppCompatActivity host) {
        Display display = host.getDisplay();
        return (display != null && display.getDisplayId() != Display.DEFAULT_DISPLAY)
                || host.isInMultiWindowMode();
    }

    public static String automaticGameResolution(AppCompatActivity host) {
        if (host.getPreferences(Context.MODE_PRIVATE).getBoolean(scopedKey(host, "compat_graphics"), false))
            return "800x600";
        if (!isDesktopWindow(host)) return "1280x720";
        int width = host.getResources().getDisplayMetrics().widthPixels;
        int height = host.getResources().getDisplayMetrics().heightPixels;
        if (Build.VERSION.SDK_INT >= 30) {
            WindowMetrics metrics = host.getWindowManager().getCurrentWindowMetrics();
            Rect bounds = metrics.getBounds();
            width = bounds.width();
            height = bounds.height();
        }
        int longSide = Math.max(width, height);
        int shortSide = Math.min(width, height);
        if (longSide >= 1850 && shortSide >= 980) return "1920x1080";
        if (longSide >= 1450 && shortSide >= 780) return "1600x900";
        return "1280x720";
    }

    /** Changes Wine's virtual X screen only for the next launch. */
    public static String chosenGameResolution(AppCompatActivity host) {
        int mode = getDisplayModeIndex(host);
        return mode == 0 ? automaticGameResolution(host) : WINE_RESOLUTIONS[mode];
    }

    public static boolean isDesktopPointerCaptured(AppCompatActivity host) {
        return host.getPreferences(Context.MODE_PRIVATE)
                .getBoolean(scopedKey(host, DESKTOP_CAPTURE_KEY), false);
    }

    public static void setDesktopPointerCaptured(AppCompatActivity host, boolean capture) {
        host.getPreferences(Context.MODE_PRIVATE).edit()
                .putBoolean(scopedKey(host, DESKTOP_CAPTURE_KEY), capture).apply();
    }

    public static boolean shouldCapturePointer(AppCompatActivity host) {
        if (isDesktopWindow(host)) return isDesktopPointerCaptured(host);
        return PreferenceManager.getDefaultSharedPreferences(host)
                .getBoolean("capture_pointer_on_external_mouse", true);
    }

    public static long installedApkTimestamp(AppCompatActivity host) {
        try {
            return host.getPackageManager().getPackageInfo(host.getPackageName(), 0).lastUpdateTime;
        } catch (Exception error) {
            // A failure keeps the state conservative and retryable.
            return 0L;
        }
    }

    public static boolean engineRefreshRequired(AppCompatActivity host) {
        return host.getPreferences(Context.MODE_PRIVATE)
                .getLong(PREPARED_APK_KEY, -1L) != installedApkTimestamp(host);
    }

    public static void markEnginePrepared(AppCompatActivity host) {
        host.getPreferences(Context.MODE_PRIVATE).edit()
                .putLong(PREPARED_APK_KEY, installedApkTimestamp(host)).apply();
    }

    /**
     * Refresh the bundled engine on first install or after an APK upgrade.
     * This deliberately mirrors the existing working Touhou runtime behavior
     * and is called on the launcher's background worker thread.
     *
     * rootfs.tzst must be checked before future upstream updates: the pinned
     * archive has an empty ./home/ entry, no xuser-N Wine prefixes.
     */
    public static void prepareBundledEngine(AppCompatActivity host) {
        RootFS root = RootFS.find(host);
        boolean freshRoot = !root.isValid();
        boolean rootOutdated = root.getVersion() < RootFSInstaller.LATEST_VERSION;
        boolean apkChanged = engineRefreshRequired(host);
        if (!(freshRoot || rootOutdated || apkChanged)) return;

        if (freshRoot || rootOutdated) {
            SettingsFragment.resetPreferenceVersions(host);
            PreferenceManager.getDefaultSharedPreferences(host).edit()
                    .putString("box64_version", DefaultVersion.BOX64).apply();
        }
        PreferenceManager.getDefaultSharedPreferences(host).edit()
                .remove("current_box64_version").apply();
        File rootDir = root.getRootDir();
        if (!rootDir.isDirectory() && !rootDir.mkdirs())
            throw new IllegalStateException("Cannot create private engine storage");

        boolean ok = TarCompressorUtils.extract(
                TarCompressorUtils.Type.ZSTD, host, "rootfs.tzst", rootDir);
        if (!ok) throw new IllegalStateException("Could not extract Windows engine resources");
        root.createRFSVersionFile(RootFSInstaller.LATEST_VERSION);
        if (!root.isValid()) throw new IllegalStateException("Engine verification failed");
    }

    /** Shared compatibility policy; each launcher chooses when to apply it. */
    public static void applyGraphicsProfile(Context host, Container container, boolean conservative) {
        container.setGraphicsDriver(conservative
                ? GraphicsDrivers.VORTEK + "," + GraphicsDrivers.VIRGL
                : GraphicsDrivers.getDefaultDriver(host));
        container.setDXWrapper(conservative ? DXWrappers.WINED3D : Container.DEFAULT_DXWRAPPER);
        container.setBox64Preset(conservative ? Box64Preset.CONSERVATIVE : Box64Preset.STABILITY);
        container.setScreenSize(conservative ? "800x600" : "1280x720");
        container.saveData();
    }

    /** Build only a NEW container configuration. Never touch existing saves. */
    public static JSONObject createContainerProfile(Context host, String name,
                                                     boolean conservative) throws JSONException {
        JSONObject profile = new JSONObject();
        profile.put("name", name);
        profile.put("screenSize", conservative ? "800x600" : "1280x720");
        profile.put("graphicsDriver", conservative
                ? GraphicsDrivers.VORTEK + "," + GraphicsDrivers.VIRGL
                : GraphicsDrivers.getDefaultDriver(host));
        profile.put("dxwrapper", conservative ? DXWrappers.WINED3D : Container.DEFAULT_DXWRAPPER);
        profile.put("box64Preset", conservative ? Box64Preset.CONSERVATIVE : Box64Preset.STABILITY);
        profile.put("audioDriver", Container.DEFAULT_AUDIO_DRIVER);
        return profile;
    }
}

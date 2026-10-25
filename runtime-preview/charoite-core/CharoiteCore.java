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
    public static final String VERSION = "0.9";
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
    // TPDP base game: sound / 60 FPS but a black DirectX 9 game surface is
    // reported under some Winlator graphics combinations. Overrides are
    // PER LAUNCH, never written into an existing Wine container.
    private static final String TPDP_GRAPHICS_KEY = "tpdp_graphics_mode";
    public static final int TPDP_GRAPHICS_SAVED = 0;
    public static final int TPDP_GRAPHICS_DXVK_TURNIP = 1;
    public static final int TPDP_GRAPHICS_WINED3D_VIRGL = 2;
    public static final int TPDP_GRAPHICS_WINED3D_ZINK = 3;

    private CharoiteCore() {}
    /** Existing Touhou preference keys remain unchanged; other profiles isolate settings. */
    private static String scopedKey(AppCompatActivity host, String key) {
        return CharoiteEnvironments.isTouhou(host)
                ? key : "portal_" + CharoiteEnvironments.activeId(host) + "_" + key;
    }

    /**
     * Charoite Core locale policy (per environment): Touhou Realm defaults to
     * Japanese CP932 / IPA Gothic for existing users, whereas other realms
     * default to their original English Wine locale until the user opts in.
     * This setting lives in the historical activity preferences to preserve
     * existing containers and avoid changing Android's system language.
     */
    public static boolean japaneseCompatibilityEnabled(Context host) {
        android.content.SharedPreferences preferences = host.getSharedPreferences(
                "TouhouEntryActivity", Context.MODE_PRIVATE);
        String environmentId = preferences.getString(
                "charoite_active_environment_v1", CharoiteEnvironments.TOUHOU);
        return preferences.getBoolean("charoite_japanese_support_" + environmentId,
                CharoiteEnvironments.TOUHOU.equals(environmentId));
    }

    public static void setJapaneseCompatibilityEnabled(AppCompatActivity host, boolean enabled) {
        String environmentId = CharoiteEnvironments.activeId(host);
        host.getSharedPreferences("TouhouEntryActivity", Context.MODE_PRIVATE)
                .edit().putBoolean("charoite_japanese_support_" + environmentId, enabled).apply();
    }

    /**
     * Inno Setup font repair is a Core capability, but injection remains
     * explicitly scoped: current environment must have Japanese support,
     * user must opt in (Touhou legacy defaults on), and launch must be a
     * recognized installer executable. The Win32 monitor must independently
     * verify a Japanese CP932 Inno TWizardForm before attaching any hook.
     */
    public static boolean installerFontRepairEnabled(Context host) {
        android.content.SharedPreferences prefs = host.getSharedPreferences(
                "TouhouEntryActivity", Context.MODE_PRIVATE);
        String id = prefs.getString("charoite_active_environment_v1", CharoiteEnvironments.TOUHOU);
        return japaneseCompatibilityEnabled(host)
                && prefs.getBoolean("charoite_installer_font_repair_" + id,
                        CharoiteEnvironments.TOUHOU.equals(id));
    }

    public static void setInstallerFontRepairEnabled(AppCompatActivity host, boolean enabled) {
        String id = CharoiteEnvironments.activeId(host);
        host.getSharedPreferences("TouhouEntryActivity", Context.MODE_PRIVATE)
                .edit().putBoolean("charoite_installer_font_repair_" + id, enabled).apply();
    }

    /**
     * Conservative opt-in Japanese installer recognizer. This is only the
     * first eligibility gate: the Win32 monitor MUST independently verify a
     * CP932 Inno TWizardForm containing Japanese Unicode text.
     */
    public static boolean isJapaneseInstallerCandidate(String executable) {
        if (executable == null) return false;
        String candidate = executable.trim().replace('\\', '/');
        int exeEnd = candidate.toLowerCase(java.util.Locale.ROOT).lastIndexOf(".exe");
        if (exeEnd < 0) return false;
        // Reject disguised files such as setup.exe.bak or setup.exe.config.
        // A plain closing quote is permitted around a Windows command.
        String suffix = candidate.substring(exeEnd + 4).trim();
        if (!suffix.isEmpty() && !suffix.equals("\"")) return false;
        candidate = candidate.substring(0, exeEnd + 4);
        int delimiter = Math.max(candidate.lastIndexOf('/'), candidate.lastIndexOf('"'));
        String filename = candidate.substring(delimiter + 1)
                .toLowerCase(java.util.Locale.ROOT);
        return filename.equals("setup.exe") || filename.equals("install.exe") ||
               filename.equals("installer.exe") ||
               (filename.startsWith("setup_") && filename.endsWith(".exe")) ||
               (filename.startsWith("install_") && filename.endsWith(".exe"));
    }

    /** Compatibility alias for the earlier Touhou-specific caller. */
    public static boolean useTouhouInstallerFontProbe(Context host) {
        return installerFontRepairEnabled(host);
    }

    /** Only known FocasLens game binaries qualify, never an installer or
     * other Windows game's executable. Reversible per-environment setting. */
    public static boolean isTpdpGameExecutable(String executable) {
        if (executable == null) return false;
        String path = executable.trim().replace('\\', '/');
        int slash = path.lastIndexOf('/');
        String file = path.substring(slash + 1).toLowerCase(java.util.Locale.ROOT);
        return file.equals("gn_enbu.exe") || file.equals("enbu_ap.exe");
    }

    public static int tpdpGraphicsMode(AppCompatActivity host) {
        int mode = host.getPreferences(Context.MODE_PRIVATE)
                .getInt(scopedKey(host, TPDP_GRAPHICS_KEY),
                        CharoiteEnvironments.isTouhou(host)
                                ? TPDP_GRAPHICS_WINED3D_VIRGL : TPDP_GRAPHICS_SAVED);
        return (mode >= TPDP_GRAPHICS_SAVED &&
                mode <= TPDP_GRAPHICS_WINED3D_ZINK) ? mode : TPDP_GRAPHICS_SAVED;
    }

    public static void setTpdpGraphicsMode(AppCompatActivity host, int mode) {
        if (mode < TPDP_GRAPHICS_SAVED || mode > TPDP_GRAPHICS_WINED3D_ZINK)
            throw new IllegalArgumentException("Unsupported TPDP graphics mode");
        host.getPreferences(Context.MODE_PRIVATE).edit()
                .putInt(scopedKey(host, TPDP_GRAPHICS_KEY), mode).apply();
    }

    /** A non-TPDP Windows program always receives the original container
     * DX wrapper and driver: no global Wine/DXVK configuration changes. */
    public static int tpdpGraphicsModeForLaunch(AppCompatActivity host,
                                                String executable) {
        return isTpdpGameExecutable(executable)
                ? tpdpGraphicsMode(host) : TPDP_GRAPHICS_SAVED;
    }

    public static String tpdpGraphicsModeLabel(int mode) {
        switch (mode) {
            case TPDP_GRAPHICS_DXVK_TURNIP: return "DXVK + TURNIP";
            case TPDP_GRAPHICS_WINED3D_VIRGL: return "WINED3D + VIRGL";
            case TPDP_GRAPHICS_WINED3D_ZINK: return "WINED3D + ZINK";
            default: return "SAVED SETTINGS";
        }
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

    /** Select a Wine desktop resolution for the CURRENT phone/window orientation. */
    public static String automaticGameResolution(AppCompatActivity host) {
        int width = host.getResources().getDisplayMetrics().widthPixels;
        int height = host.getResources().getDisplayMetrics().heightPixels;
        if (Build.VERSION.SDK_INT >= 30) {
            WindowMetrics metrics = host.getWindowManager().getCurrentWindowMetrics();
            Rect bounds = metrics.getBounds();
            width = bounds.width();
            height = bounds.height();
        }
        // Phone rotation can arrive before WindowMetrics catches up; the
        // Configuration orientation is authoritative for phone display.
        boolean portrait = host.getResources().getConfiguration().orientation
                == android.content.res.Configuration.ORIENTATION_PORTRAIT;
        if (isDesktopWindow(host)) portrait = height > width;
        boolean conservative = compatibleGraphics(host);
        if (conservative) return portrait ? "600x800" : "800x600";
        if (!isDesktopWindow(host)) return portrait ? "720x1280" : "1280x720";
        int longSide = Math.max(width, height);
        int shortSide = Math.min(width, height);
        String chosen = (longSide >= 1850 && shortSide >= 980) ? "1920x1080" :
                (longSide >= 1450 && shortSide >= 780) ? "1600x900" : "1280x720";
        return adaptToOrientation(chosen, portrait);
    }

    private static String adaptToOrientation(String resolution, boolean portrait) {
        String[] parts = resolution.split("x");
        if (parts.length != 2) return resolution;
        int a = Integer.parseInt(parts[0]);
        int b = Integer.parseInt(parts[1]);
        int longest = Math.max(a, b), shortest = Math.min(a, b);
        return portrait ? shortest + "x" + longest : longest + "x" + shortest;
    }

    /** Resolves each launch in the active orientation without changing user settings.
     * A running Wine app stays open during rotation; its surface is fitted live by
     * XServer, while the Wine desktop mode itself is selected on the next launch.
     */
    public static String chosenGameResolution(AppCompatActivity host) {
        int mode = getDisplayModeIndex(host);
        if (mode == 0) return automaticGameResolution(host);
        boolean portrait = host.getResources().getConfiguration().orientation
                == android.content.res.Configuration.ORIENTATION_PORTRAIT;
        if (isDesktopWindow(host)) {
            WindowMetrics metrics = Build.VERSION.SDK_INT >= 30
                    ? host.getWindowManager().getCurrentWindowMetrics() : null;
            if (metrics != null) portrait = metrics.getBounds().height() > metrics.getBounds().width();
        }
        return adaptToOrientation(WINE_RESOLUTIONS[mode], portrait);
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

package com.charoitegames.core;

import android.content.Context;
import com.winlator.container.DXWrappers;
import com.winlator.container.GraphicsDrivers;
import com.winlator.core.EnvVars;
import com.winlator.xenvironment.RootFS;
import java.io.File;
import java.util.Locale;

/**
 * Charoite Core's executable-aware Wine graphics compatibility catalog.
 *
 * A verified game profile is automatic, with no Portal button, preference,
 * migration, Wine-prefix reset, or modification of installed game files.
 * Unknown Windows executables retain their container's original graphics.
 *
 * Integration bridge: pinned Winlator supplies its saved driver/wrapper
 * strings, then calls forExecutable() and configureLaunchEnvironment().
 */
public final class CharoiteGraphicsProfiles {
    private CharoiteGraphicsProfiles() {}

    public static final class Profile {
        public final String id;
        public final String title;
        public final String graphicsDriver;
        public final String dxWrapper;
        public final String dxWrapperConfig;
        public final String graphicsDriverConfig;
        public final int diagnosticMode;

        private Profile(String id, String title, String graphicsDriver,
                        String dxWrapper, String dxWrapperConfig,
                        String graphicsDriverConfig, int diagnosticMode) {
            this.id = id;
            this.title = title;
            this.graphicsDriver = graphicsDriver;
            this.dxWrapper = dxWrapper;
            this.dxWrapperConfig = dxWrapperConfig;
            this.graphicsDriverConfig = graphicsDriverConfig;
            this.diagnosticMode = diagnosticMode;
        }
    }

    // Verified on Galaxy S26 Ultra with the TPDP base game. The expansion
    // executable uses the same D3D9 game family but remains untested.
    private static final Profile TPDP_D3D9 = new Profile(
            "tpdp-direct3d9-dxvk1103-turnip",
            "TPDP • DXVK 1.10.3 + Turnip (automatic)",
            GraphicsDrivers.TURNIP + "," + GraphicsDrivers.DEFAULT_OPENGL_DRIVER,
            DXWrappers.DXVK, "version=1.10.3", "",
            CharoiteCore.TPDP_GRAPHICS_DXVK_D3D9_LEGACY);

    /** Exact executable matching prevents touching installers and other games. */
    public static Profile forExecutable(String executable) {
        if (executable == null) return null;
        String normalized = executable.trim().replace('\\', '/');
        String file = normalized.substring(normalized.lastIndexOf('/') + 1)
                .toLowerCase(Locale.ROOT);
        if ("gn_enbu.exe".equals(file) || "enbu_ap.exe".equals(file))
            return TPDP_D3D9;
        return null;  // Preserve all saved settings for unknown games.
    }

    public static int diagnosticModeForExecutable(String executable) {
        Profile profile = forExecutable(executable);
        return profile != null ? profile.diagnosticMode :
                CharoiteCore.TPDP_GRAPHICS_SAVED;
    }

    public static String description(String executable) {
        Profile profile = forExecutable(executable);
        return profile == null ? "Container's saved graphics (automatic)" :
                profile.title;
    }

    /**
     * Applies launch-local diagnostics to the EXACT automatic profile.
     * Doesn't write Wine registry, container preferences, or any game path.
     * Note: the upstream Winlator DXVK installer manages Wine's own
     * wrapper DLL selection at launch; the user's installed games/saves
     * and persistent per-game profile selection are unaffected.
     */
    public static void configureLaunchEnvironment(Context context,
                                                   RootFS rootFS,
                                                   EnvVars envVars,
                                                   String executable) {
        Profile profile = forExecutable(executable);
        if (profile == null) return;
        envVars.put("WINEDEBUG", "err+all,warn+all,fixme+winediag,trace+loaddll");

        File dxvkLogs = new File(rootFS.getRootDir(),
                "tmp/charoite-tpdp-dxvk");
        if (!dxvkLogs.isDirectory() && !dxvkLogs.mkdirs()) {
            CharoiteDiagnostics.recordLine(
                    "Core: DXVK diagnostic directory is unavailable");
        }
        if (dxvkLogs.isDirectory()) {
            envVars.put("DXVK_LOG_PATH", dxvkLogs.getAbsolutePath());
            CharoiteDiagnostics.setDxvkLogDirectory(context, dxvkLogs);
        }
        envVars.put("DXVK_LOG_LEVEL", "info");
        CharoiteDiagnostics.recordLine(
                "Core auto-selected " + profile.id +
                "; DXVK=1.10.3, graphics=Turnip, previous UI preference ignored");
        CharoiteDiagnostics.recordLine(
                "Core automatic renderer: " + profile.title);
    }
}

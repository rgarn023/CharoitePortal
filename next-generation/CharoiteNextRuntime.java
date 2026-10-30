package com.charoitegames.core;

import android.content.Context;
import java.io.File;

/**
 * Charoite Core Next: selectable runner inventory and fail-closed readiness.
 *
 * The original Wine/Box64 runner is still the ONLY executable runner in
 * this first experimental build. The next stage will verify pinned Proton,
 * ARM64EC Wine, FEX and GPU assets in an isolated container before permitting
 * a modern-runner launch. Never infer readiness from a directory's existence.
 */
public final class CharoiteNextRuntime {
    public static final String EDITION = "Charoite Core Next";
    public static final String VERSION = "0.45 (read-only v3 PE import and architecture audit; gaming blocked)";

    public static final String WINE_BOX64 = "wine-box64";
    public static final String PROTON_ARM64EC_FEX = "proton-arm64ec-fex";
    public static final String WINE_STAGING_BOX64 = "wine-staging-box64";

    private CharoiteNextRuntime() {}

    public static final class Engine {
        public final String id;
        public final String label;
        public final boolean installed;
        public final boolean launchReady;
        public final String detail;
        Engine(String id, String label, boolean installed,
               boolean launchReady, String detail) {
            this.id = id;
            this.label = label;
            this.installed = installed;
            this.launchReady = launchReady;
            this.detail = detail;
        }
    }

    public static Engine inspect(Context context, String id) {
        if (WINE_BOX64.equals(id)) {
            return new Engine(id, "Existing Wine + Box64", true, true,
                "Bundled legacy engine. A Windows container and game must still be prepared.");
        }
        if (PROTON_ARM64EC_FEX.equals(id)) {
            File staging = new File(context.getFilesDir(),
                    "charoite-next/runtimes/proton-arm64ec-fex");
            // A directory is never executable evidence. A fully verified
            // manifest and dedicated, newly provisioned prefix are mandatory.
            return new Engine(id, "Modified Proton ARM64EC + FEX", false, false,
                staging.exists()
                ? "Staging exists, but has NOT passed signature/hash/ABI and prefix validation. Launch blocked."
                : "Not installed: pinned GE-Proton, patched Wine ntdll/wineserver, FEX, graphics and fresh-prefix tests required.");
        }
        if (WINE_STAGING_BOX64.equals(id)) {
            return new Engine(id, "Wine Staging + Box64", false, false,
                "Optional new runner is not installed or validated. Launch blocked.");
        }
        throw new IllegalArgumentException("Unknown Charoite engine: " + id);
    }

    public static boolean mayLaunch(Context context, String id) {
        return inspect(context, id).launchReady;
    }

    public static String report(Context context) {
        Engine legacy = inspect(context, WINE_BOX64);
        Engine proton = inspect(context, PROTON_ARM64EC_FEX);
        Engine staging = inspect(context, WINE_STAGING_BOX64);
        return "Charoite Core Next " + VERSION + "\n"
                + "CI Wine PE libraries: bundled as read-only diagnostic assets; not runnable.\n"
                + "Use System > Run Core Next device diagnostics to verify phone and PE hashes.\n"
                + "Use Test source-built Wine --version for the isolated Android-native loader smoke test.\n"
                + "Use Test source-built wineserver --version to verify native server ELF separately.\n"
                + "A --version pass does NOT establish a working Wine prefix, ARM64EC or FEX runtime.\n"
                + "Use Audit modern Wine bootstrap prerequisites to see attested import gaps.\n"
                + "Use Verify packaged modern Wine modules to SHA-check the 22-component archive and 76 NLS tables.\n"
                + "Use Stage isolated modern Wine PE/NLS modules for opt-in, hash-gated private DATA staging.\n"
                + "Use Test native Wine startup prerequisites to verify the staged 95 files and run native loader/server --version only.\n"
                + "Use Stage expanded Wine 26-module data to verify and stage a SEPARATE 23 PE/76 NLS source cohort.\n"
                + "Use Test matched Wine26 native startup to verify all 99 staged files and execute same-source native Wine/wineserver --version ONLY.\n"
                + "Earlier Wine26 v2 Wineboot failed at native NLS lookup; its scratch is retained.\n"
                + "Stage patched Wine27 0.6 data, verify matched native binaries, then explicitly approve NEW isolated v3 Wineboot test.\n"
                + legacy.label + ": bundled (existing compatibility engine)\n"
                + proton.label + ": NOT READY\n" + proton.detail + "\n"
                + staging.label + ": NOT READY\n" + staging.detail + "\n"
                + "Anti-cheat: respect game/vendor support; no bypass or kernel-driver emulation promised.\n"
                + "All game/prefix data is private to this separate Android application.";
    }
}

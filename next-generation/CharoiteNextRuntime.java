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
    public static final String VERSION = "0.70 (Wine29 v1 kernel32 read-only postmortem; PE-help still blocked)";

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
                + "Verify Wine29 0.7 package (read-only) audits the new APK-owned 27-component/76-NLS archive and three dedicated native libraries without running them.\n"
                + "Test Wine29 0.7 native --version (no prefix) executes ONLY the source-matched APK native loader and wineserver after explicit consent and hash audit. No Wineboot or Windows EXE.\n"
                + "Stage Wine29 0.7 PE/NLS data (no execution) copies source-verified PE/NLS into a NEW isolated private slot only after explicit consent. Windows execution remains blocked.\n"
                + "Verify staged Wine29 0.7 data (read-only) rechecks all 100 APK assets and sealed private slot; rejects extra files without executing Wine.\n"
                + "Preflight Wine29 0.7 PE loader layout (read-only) checks ARM64EC/ARM64 images, NLS selector layout and static imports without execution.\n"
                + "Stage Wine29 0.12 sealed 111-file data (no execution) creates a separate 34-DLL, Wineboot PE and 76-NLS private slot only with user consent.\n"
                + "Verify staged Wine29 0.12 sealed data (read-only) checks strict inventory and all hashes without writes or Wine execution.\n"
                + "Preflight Wine29 0.12 PE imports (read-only) inspects 34 hybrid DLL headers, ARM64 Wineboot and direct/delay DLL references after the sealed 111-file SHA audit; never executes Wine.\n"
                + "Wine29 v1 isolated Wineboot PE-help test (one-shot) requires a separate on-phone authorization; runs native wineserver/loader and ARM64 Wineboot --help ONLY in fresh scratch where Wine may auto-initialize a new prefix.\n"
                + "Inspect preserved Wine29 v1 kernel32 failure (read-only) examines only the existing v1 logs and five named PE file copies against source hashes; NO execution, retry or cleanup.\n"
                + "Earlier Wine26 v2 Wineboot failed at native NLS lookup; its scratch is retained.\n"
                + "Stage patched Wine27 0.6 data, verify matched native binaries, then explicitly approve NEW isolated v3 Wineboot test.\n"
                + legacy.label + ": bundled (existing compatibility engine)\n"
                + proton.label + ": NOT READY\n" + proton.detail + "\n"
                + staging.label + ": NOT READY\n" + staging.detail + "\n"
                + "Anti-cheat: respect game/vendor support; no bypass or kernel-driver emulation promised.\n"
                + "All game/prefix data is private to this separate Android application.";
    }
}

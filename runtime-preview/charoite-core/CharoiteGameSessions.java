package com.charoitegames.core;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import androidx.appcompat.app.AppCompatActivity;
import com.winlator.container.Container;
import com.winlator.container.ContainerManager;
import java.io.File;
import java.util.Locale;

/**
 * Single point of control for Android/Wine program sessions.
 * Core chooses the session display, diagnostics and installer-return policy.
 * Portal remains responsible only for the Play/Run button and UI status.
 */
public final class CharoiteGameSessions {
    private static final String PENDING_SCAN = "pending_installer_scan";
    private CharoiteGameSessions() {}

    public static boolean hasPendingInstallerScan(AppCompatActivity host) {
        return host.getPreferences(Context.MODE_PRIVATE).getBoolean(PENDING_SCAN, false);
    }

    /** Marks completion only after the host has returned from installer UI. */
    public static boolean consumePendingInstallerScan(AppCompatActivity host) {
        boolean needed = hasPendingInstallerScan(host);
        if (needed) host.getPreferences(Context.MODE_PRIVATE).edit()
                .putBoolean(PENDING_SCAN, false).apply();
        return needed;
    }

    /**
     * Never start a program merely because files were imported. The host calls
     * this only for explicit Play / Run Installer actions or opt-in launch
     * confirmed by the shared importer policy.
     *
     * Existing intent extra names are preserved for pinned XServer backend.
     */
    public static void launch(AppCompatActivity host, Class<? extends Activity> target,
                              int containerId, String executable, boolean installer) {
        if (containerId <= 0 || executable == null || !new File(executable).isFile())
            throw new IllegalArgumentException("Windows executable is missing");
        // Shard of Dreams uses the original TPDP installation. Some Wine
        // versions resolve its base folder through a local notkey link.
        // The Core check creates that single link only if absent and both
        // installed directories are verified inside the same Wine C: drive.
        // Never copy game assets, replace files, or touch saves.
        String expansionStatus = CharoiteShardOfDreamsSupport.isExpansionGame(executable)
                ? CharoiteShardOfDreamsSupport.checkAndRepair(host, executable)
                : "No Shard of Dreams launch.";
        CharoiteDiagnostics.recordExpansionStatus(host, expansionStatus);
        Intent play = new Intent(host, target);
        play.putExtra("container_id", containerId);
        play.putExtra("exec_path", executable);
        play.putExtra("touhou_desktop_window", CharoiteCore.isDesktopWindow(host));
        play.putExtra("touhou_display_size", CharoiteCore.chosenGameResolution(host));
        play.putExtra("touhou_pointer_capture", CharoiteCore.shouldCapturePointer(host));
        // Core auto-resolves every known game profile; users just press Play.
        play.putExtra("charoite_tpdp_graphics_mode",
                CharoiteGraphicsProfiles.diagnosticModeForExecutable(executable));

        // Keep the in-process font monitor limited to opted-in Japanese
        // Inno Setup installers, never game launchers or arbitrary EXEs.
        if (CharoiteCore.installerFontRepairEnabled(host)
                && CharoiteCore.isJapaneseInstallerCandidate(executable)) {
            try {
                Container c = new ContainerManager(host).getContainerById(containerId);
                CharoiteDiagnostics.setProbePath(host, c == null ? ""
                        : new File(c.getRootDir(), ".wine/drive_c/touhou_probe.log").getAbsolutePath());
            } catch (Exception e) {
                CharoiteDiagnostics.recordLine("Cannot configure installer probe: " + e);
                CharoiteDiagnostics.setProbePath(host, "");
            }
        } else CharoiteDiagnostics.setProbePath(host, "");

        if (installer) host.getPreferences(Context.MODE_PRIVATE).edit()
                .putBoolean(PENDING_SCAN, true).apply();
        try {
            host.startActivity(play);
        } catch (RuntimeException ex) {
            if (installer) host.getPreferences(Context.MODE_PRIVATE).edit()
                    .putBoolean(PENDING_SCAN, false).apply();
            throw ex;
        }
    }
}

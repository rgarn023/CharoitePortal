package com.charoitegames.core;

import android.content.Context;
import android.content.SharedPreferences;
import androidx.appcompat.app.AppCompatActivity;
import androidx.preference.PreferenceManager;
import com.winlator.container.Container;
import com.winlator.container.ContainerManager;
import com.winlator.core.FileUtils;
import java.io.File;
import java.io.IOException;

/**
 * Read-only Win32 GDI test bundled by Charoite Core.
 * Explicitly started by Portal; no Wine DLL or user game files are patched.
 */
public final class CharoiteRenderingDiagnostics {
    private static final String ASSET = "rendering/charoite_gdi_probe32.exe";
    private static final String EXE = "charoite_gdi_probe32.exe";
    private static final String LOG = "charoite_gdi_render.log";
    private static final String OWNER_ASSET = "rendering/charoite_ownerdraw_probe32.exe";
    private static final String OWNER_EXE = "charoite_ownerdraw_probe32.exe";
    private static final String OWNER_LOG = "charoite_ownerdraw_render.log";
    private static final String OWNER_MARKER = ".charoite-ownerdraw-probe-v1";
    private static final String VERSION_MARKER = ".charoite-gdi-probe-v1";
    private static final String REPORT_KEY = "charoite_render_probe_path";
    private CharoiteRenderingDiagnostics() {}

    /** Only copies a core-owned diagnostic program on explicit request. */
    public static String prepare(AppCompatActivity host, int containerId) throws IOException {
        return prepareInternal(host, containerId, ASSET, EXE, LOG, VERSION_MARKER);
    }

    /** Differential test for native owner-drawn Japanese Win32 listbox items. */
    public static String prepareOwnerDraw(AppCompatActivity host, int containerId)
            throws IOException {
        return prepareInternal(host, containerId, OWNER_ASSET, OWNER_EXE,
                OWNER_LOG, OWNER_MARKER);
    }

    private static String prepareInternal(AppCompatActivity host, int containerId,
            String asset, String executable, String logName, String versionMarker)
            throws IOException {
        if (containerId <= 0) throw new IOException("No active Windows environment");
        Container container = new ContainerManager(host).getContainerById(containerId);
        if (container == null) throw new IOException("Windows container is unavailable");
        File prefix = new File(container.getRootDir(), ".wine");
        File drive = new File(prefix, "drive_c");
        if (!drive.isDirectory()) throw new IOException("Windows C: drive is not ready");
        File program = new File(drive, executable);
        File marker = new File(prefix, versionMarker);
        if (!marker.isFile() || !program.isFile() || program.length() < 10000) {
            FileUtils.copy(host, asset, program);
            if (!program.isFile() || program.length() < 10000)
                throw new IOException("Cannot install read-only GDI diagnostic");
            if (!FileUtils.writeString(marker, "v1\n"))
                throw new IOException("Cannot record diagnostic version");
        }
        File output = new File(drive, logName);
        // The executable itself rewrites only its own report on launch.
        SharedPreferences p = PreferenceManager.getDefaultSharedPreferences(host);
        p.edit().putString(REPORT_KEY, output.getAbsolutePath()).apply();
        return program.getAbsolutePath();
    }

    public static void clearReportForAnotherLaunch(Context host, String executable) {
        if (executable != null &&
                (executable.endsWith(EXE) || executable.endsWith(OWNER_EXE))) return;
        PreferenceManager.getDefaultSharedPreferences(host)
                .edit().remove(REPORT_KEY).apply();
    }

    /** Reports only synthetic test strings and font coverage, never game data. */
    public static String report(Context context) {
        String location = PreferenceManager.getDefaultSharedPreferences(context)
                .getString(REPORT_KEY, "");
        if (location.isEmpty()) return "";
        try {
            File file = new File(location);
            if (!file.isFile()) return "\n\nGDI test log has not been created yet.";
            byte[] bytes = java.nio.file.Files.readAllBytes(file.toPath());
            String result = new String(bytes, java.nio.charset.StandardCharsets.UTF_8);
            return "\n\nCHAROITE CORE WINDOWS TEXT RENDERING TEST:\n" +
                   result.substring(0, Math.min(result.length(), 8000));
        } catch (Exception e) {
            return "\n\nGDI diagnostic log unavailable: " + e;
        }
    }
}

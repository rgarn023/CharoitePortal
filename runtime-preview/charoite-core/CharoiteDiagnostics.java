package com.charoitegames.core;

import android.content.Context;
import android.content.SharedPreferences;
import androidx.preference.PreferenceManager;
import com.winlator.core.Callback;
import java.util.ArrayDeque;

/** Shared Core diagnostics with legacy preferences and read-only Japanese probe logs. */
public final class CharoiteDiagnostics {
    private static final int MAX_LINES = 70;
    private static final ArrayDeque<String> lines = new ArrayDeque<>();
    private static final ArrayDeque<String> graphicsLines = new ArrayDeque<>();
    private static final int MAX_GRAPHICS_LINES = 75;
    private static volatile boolean tpdpGraphicsProbe;
    public static final Callback<String> CALLBACK = CharoiteDiagnostics::recordLine;

    private CharoiteDiagnostics() {}

    public static void begin(Context context, String executable) {
        CharoiteRenderingDiagnostics.clearReportForAnotherLaunch(context, executable);
        synchronized (lines) { lines.clear(); }
        synchronized (graphicsLines) { graphicsLines.clear(); }
        tpdpGraphicsProbe = CharoiteCore.isTpdpGameExecutable(executable);
        prefs(context).edit()
            .putString("touhou_launch_status", "starting")
            .putString("touhou_launch_file", executable == null ? "unknown" :
                executable.substring(Math.max(0, executable.lastIndexOf('/') + 1)))
            .putString("touhou_launch_error", "")
            .apply();
    }

    public static void recordLine(String line) {
        if (line == null || line.trim().isEmpty()) return;
        synchronized (lines) {
            if (lines.size() == MAX_LINES) lines.removeFirst();
            lines.addLast(line.length() > 600 ? line.substring(0, 600) : line);
        }
        // Keep a bounded Direct3D/error subset after a successful window
        // open. Previously successful launches hid their Wine log entirely.
        if (tpdpGraphicsProbe) {
            String lower = line.toLowerCase(java.util.Locale.ROOT);
            if (lower.contains("d3d") || lower.contains("dxvk") ||
                    lower.contains("vulkan") || lower.contains("virgl") ||
                    lower.contains("vortek") || lower.contains("mesa") ||
                    lower.contains("shader") || lower.contains("texture") ||
                    lower.contains("surface") || lower.contains("swapchain") ||
                    lower.contains("present") || lower.contains("winediag") ||
                    lower.contains("err:") || lower.contains("warn:")) {
                synchronized (graphicsLines) {
                    if (graphicsLines.size() == MAX_GRAPHICS_LINES)
                        graphicsLines.removeFirst();
                    graphicsLines.addLast(line.length() > 400 ?
                            line.substring(0, 400) : line);
                }
            }
        }
    }

    /** Record the backend selected by the actual Windows runtime, even if
     * the app reaches 60 FPS with no visible game pixels. */
    public static void recordGraphicsBackend(Context context, String wrapper,
                                             String driver, String openGlDriver,
                                             int tpdpMode) {
        prefs(context).edit()
            .putString("charoite_last_graphics_backend",
                    "DirectX wrapper: " + (wrapper == null ? "unknown" : wrapper) +
                    "\nVulkan driver: " + (driver == null ? "unknown" : driver) +
                    "\nOpenGL driver: " + (openGlDriver == null ? "unknown" : openGlDriver) +
                    "\nTPDP override: " +
                    CharoiteCore.tpdpGraphicsModeLabel(tpdpMode))
            .apply();
    }

    public static void windowOpened(Context context) {
        prefs(context).edit()
            .putString("touhou_launch_status", "game window appeared")
            .putString("touhou_launch_error", "")
            .apply();
    }

    public static void fail(Context context, String reason) {
        StringBuilder report = new StringBuilder();
        report.append(reason).append('\n');
        synchronized (lines) {
            for (String line : lines) report.append(line).append('\n');
        }
        prefs(context).edit()
            .putString("touhou_launch_status", "failed")
            .putString("touhou_launch_error", report.toString())
            .apply();
    }

    public static void setProbePath(Context context, String file) {
        prefs(context).edit().putString("touhou_probe_path", file == null ? "" : file).apply();
    }

    public static String getReport(Context context) {
        SharedPreferences p = prefs(context);
        String report = "Charoite Portal / Japanese installer diagnostics v11" +
            "\nGame: " + p.getString("touhou_launch_file", "(none)") +
            "\nStatus: " + p.getString("touhou_launch_status", "not attempted") +
            "\n\n" + p.getString("touhou_launch_error", "No error captured.");
        report += "\n\nGRAPHICS BACKEND:\n" +
                p.getString("charoite_last_graphics_backend",
                        "Not recorded in this build.");
        String probePath = p.getString("touhou_probe_path", "");
        if (!probePath.isEmpty()) {
            try {
                java.io.File file = new java.io.File(probePath);
                if (file.isFile()) {
                    String details = new String(
                        java.nio.file.Files.readAllBytes(file.toPath()),
                        java.nio.charset.StandardCharsets.UTF_8);
                    report += "\n\nJAPANESE PATH / CODEPAGE PROBE:\n" +
                        details.substring(0, Math.min(14000, details.length()));
                } else {
                    report += "\n\nJapanese probe report not present; keep the installer open on its destination page.";
                }
            } catch (Exception error) {
                report += "\n\nJapanese probe report could not be read: " + error;
            }
        }
        if (!probePath.isEmpty()) {
            java.io.File parent = new java.io.File(probePath).getParentFile();
            if (parent != null) for (String name : new String[]{
                    "touhou_font_helper.log", "touhou_font_hook.log"}) {
                try {
                    java.io.File log = new java.io.File(parent, name);
                    if (log.isFile()) {
                        String output = new String(java.nio.file.Files.readAllBytes(log.toPath()),
                                java.nio.charset.StandardCharsets.UTF_8);
                        report += "\n\n" + name + ":\n" +
                                output.substring(Math.max(0, output.length() - 16000));
                    } else report += "\n\n" + name + ": no report yet";
                } catch (Exception error) {
                    report += "\n" + name + ": " + error;
                }
            }
        }
        if (tpdpGraphicsProbe) {
            report += "\n\nTPDP DIRECT3D / GRAPHICS OUTPUT (last " +
                    MAX_GRAPHICS_LINES + " matching lines):\n";
            synchronized (graphicsLines) {
                if (graphicsLines.isEmpty())
                    report += "No graphics messages captured; this does NOT verify rendering.\n";
                else for (String line : graphicsLines) report += line + "\n";
            }
            report += "A visible image must still be confirmed on the phone.\n";
        }
        report += CharoiteRenderingDiagnostics.report(context);
        return report;
    }

    private static SharedPreferences prefs(Context context) {
        return PreferenceManager.getDefaultSharedPreferences(context);
    }
}

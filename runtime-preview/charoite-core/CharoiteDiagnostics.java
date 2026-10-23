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
    public static final Callback<String> CALLBACK = CharoiteDiagnostics::recordLine;

    private CharoiteDiagnostics() {}

    public static void begin(Context context, String executable) {
        synchronized (lines) { lines.clear(); }
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
        String report = "Game: " + p.getString("touhou_launch_file", "(none)") +
            "\nStatus: " + p.getString("touhou_launch_status", "not attempted") +
            "\n\n" + p.getString("touhou_launch_error", "No error captured.");
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
                                output.substring(0, Math.min(7000, output.length()));
                    } else report += "\n\n" + name + ": no report yet";
                } catch (Exception error) {
                    report += "\n" + name + ": " + error;
                }
            }
        }
        return report;
    }

    private static SharedPreferences prefs(Context context) {
        return PreferenceManager.getDefaultSharedPreferences(context);
    }
}

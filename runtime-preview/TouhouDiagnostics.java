package com.winlator;

import android.content.Context;
import android.content.SharedPreferences;
import androidx.preference.PreferenceManager;
import com.winlator.core.Callback;
import java.util.ArrayDeque;

/** Only diagnostics: never edits imported game files or sends telemetry. */
public final class TouhouDiagnostics {
    private static final int MAX_LINES = 70;
    private static final ArrayDeque<String> lines = new ArrayDeque<>();
    public static final Callback<String> CALLBACK = TouhouDiagnostics::recordLine;

    private TouhouDiagnostics() {}

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

    public static String getReport(Context context) {
        SharedPreferences p = prefs(context);
        return "Game: " + p.getString("touhou_launch_file", "(none)") +
            "\nStatus: " + p.getString("touhou_launch_status", "not attempted") +
            "\n\n" + p.getString("touhou_launch_error", "No error captured.");
    }

    private static SharedPreferences prefs(Context context) {
        return PreferenceManager.getDefaultSharedPreferences(context);
    }
}

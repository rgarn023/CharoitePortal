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
    // Distinct early graphics failures must survive later esync warning spam.
    private static final java.util.LinkedHashMap<String, String> earlyGraphics =
            new java.util.LinkedHashMap<>();
    private static final int MAX_EARLY_GRAPHICS = 24;
    private static final ArrayDeque<String> mappedWindows = new ArrayDeque<>();
    // Actual X11 window size transitions observed on Shard (not click guesses).
    private static final ArrayDeque<String> shardWindowChanges = new ArrayDeque<>();
    private static final ArrayDeque<String> audioLines = new ArrayDeque<>();
    private static final java.util.LinkedHashMap<String,String> crashLines =
            new java.util.LinkedHashMap<>();
    private static final int MAX_CRASH_LINES = 20;
    private static volatile long startedAtMillis;
    private static final int MAX_AUDIO_LINES = 40;
    private static final int MAX_GRAPHICS_LINES = 75;
    private static volatile boolean tpdpGraphicsProbe;
    // Shard-only GL compositor timing. GLRenderer is RENDERMODE_WHEN_DIRTY:
    // this records actual Android draw callbacks, not simulated game FPS.
    // Idle gaps >=250ms are excluded since static game screens need no draws.
    private static volatile boolean shardFrameTimingEnabled;
    private static volatile long shardLastDrawNanos;
    private static volatile long shardIntervals;
    private static volatile long shardGapsOver33Ms;
    private static volatile long shardGapsOver50Ms;
    private static volatile long shardGapsOver100Ms;
    private static volatile long shardMaxActiveGapMs;
    private static volatile long shardRenderSamples;
    private static volatile long shardDrawOver16Ms;
    private static volatile long shardDrawOver33Ms;
    private static volatile long shardLongestDrawMs;
    private static final String PORTAL_EXIT_REQUESTED = "charoite_portal_exit_requested";
    public static final Callback<String> CALLBACK = CharoiteDiagnostics::recordLine;

    private CharoiteDiagnostics() {}

    /** Persisted read-only installation discovery summary independent from game launches. */
    public static void recordShardInstallationScan(Context context, String result) {
        prefs(context).edit().putString("charoite_shard_install_scan",
                result == null ? "Not checked." : result).apply();
    }

    public static String shardInstallationScan(Context context) {
        return prefs(context).getString("charoite_shard_install_scan",
                "No Shard installation scan recorded. It runs automatically after installers.");
    }

    /** Persistent, read-only account of the expansion prerequisite check. */
    public static void recordExpansionStatus(Context context, String result) {
        prefs(context).edit().putString("charoite_shard_status",
                result == null ? "Not checked." : result).apply();
    }

    public static void begin(Context context, String executable) {
        CharoiteRenderingDiagnostics.clearReportForAnotherLaunch(context, executable);
        synchronized (lines) { lines.clear(); }
        synchronized (graphicsLines) { graphicsLines.clear(); }
        synchronized (earlyGraphics) { earlyGraphics.clear(); }
        synchronized (mappedWindows) { mappedWindows.clear(); }
        synchronized (shardWindowChanges) { shardWindowChanges.clear(); }
        synchronized (audioLines) { audioLines.clear(); }
        synchronized (crashLines) { crashLines.clear(); }
        startedAtMillis = android.os.SystemClock.elapsedRealtime();
        tpdpGraphicsProbe = CharoiteCore.isTpdpGameExecutable(executable);
        shardFrameTimingEnabled =
                CharoiteShardOfDreamsSupport.isExpansionGame(executable);
        shardLastDrawNanos = 0L;
        shardIntervals = 0L;
        shardGapsOver33Ms = 0L;
        shardGapsOver50Ms = 0L;
        shardGapsOver100Ms = 0L;
        shardMaxActiveGapMs = 0L;
        shardRenderSamples = 0L;
        shardDrawOver16Ms = 0L;
        shardDrawOver33Ms = 0L;
        shardLongestDrawMs = 0L;
        prefs(context).edit()
            .putBoolean(PORTAL_EXIT_REQUESTED, false)
            .putString("touhou_launch_status", "starting")
            .putString("charoite_last_guest_exit", "No launcher termination callback yet.")
            .putString("charoite_dxvk_log_dir", "")
            .putString("charoite_dxvk_log_excerpt", "No DXVK diagnostic files captured.")
            .putString("touhou_launch_file", executable == null ? "unknown" :
                executable.substring(Math.max(0, executable.lastIndexOf('/') + 1)))
            .putString("touhou_launch_error", "")
            .putString("charoite_last_mapped_windows", "No mapped Windows program window yet.")
            .putString("charoite_last_window_layout", "No TPDP window repositioned.")
            .putString("charoite_last_x11_updates", "No image-content callbacks yet.")
            .apply();
        recordLaunchPackage(context, executable);
    }

    /** Inspect filenames/counts only: no game data or saved files are changed. */
    private static void recordLaunchPackage(Context context, String executable) {
        String report = "No executable provided.";
        if (executable != null) {
            java.io.File exe = new java.io.File(executable);
            java.io.File folder = exe.getParentFile();
            if (exe.isFile() && folder != null) {
                java.io.File[] contents = folder.listFiles();
                int files = 0, folders = 0, parts = 0;
                if (contents != null) for (java.io.File part : contents) {
                    if (part.isDirectory()) folders++;
                    else if (part.isFile()) {
                        files++;
                        String name = part.getName().toLowerCase(java.util.Locale.ROOT);
                        if (name.endsWith(".cab") || name.endsWith(".bin") ||
                                name.endsWith(".dat") || name.endsWith(".pak")) parts++;
                    }
                }
                report = "Executable: present (" + exe.length() + " bytes)" +
                        "\nAdjacent files: " + Math.max(0, files - 1) +
                        "; folders: " + folders + "; media archives: " + parts;
                if (CharoiteCore.isTpdpGameExecutable(executable)) {
                    java.io.File dat = new java.io.File(folder, "dat");
                    report += "\nTPDP dat folder: " + dat.isDirectory();
                    if (dat.isDirectory()) {
                        java.io.File[] contents2 = dat.listFiles();
                        if (contents2 != null) {
                            int count = 0, subs = 0; long bytes = 0;
                            for (java.io.File file : contents2) {
                                if (file.isFile()) { count++; bytes += file.length(); }
                                else if (file.isDirectory()) subs++;
                            }
                            report += "\nTPDP dat files: " + count +
                                    "; subfolders: " + subs +
                                    "; direct bytes: " + bytes;
                        } else report += " (unreadable)";
                    }
                    report += "\nGame-local d3d9.dll: " +
                            new java.io.File(folder, "d3d9.dll").isFile();
                }
                if (CharoiteCore.isJapaneseInstallerCandidate(executable) &&
                        files <= 1 && folders == 0)
                    report += "\nThis imported installer has no adjacent media. " +
                            "For multi-file installers, use IMPORT COMPLETE INSTALLER FOLDER.";
            } else report = "Executable file present: " + exe.isFile();
        }
        prefs(context).edit().putString("charoite_last_launch_files", report).apply();
    }

    /** Window mapping is not proof of visible Direct3D pixels. */
    public static void recordMappedWindow(Context context, String clazz,
                                          String title, int width, int height,
                                          int rootX, int rootY) {
        String cls = clazz == null ? "" : clazz.replace('\n', ' ').replace('\r', ' ');
        String caption = title == null ? "" : title.replace('\n', ' ').replace('\r', ' ');
        if (cls.length() > 65) cls = cls.substring(0, 65);
        if (caption.length() > 65) caption = caption.substring(0, 65);
        synchronized (mappedWindows) {
            if (mappedWindows.size() == 12) mappedWindows.removeFirst();
            mappedWindows.addLast("class=" + cls + " title=" + caption +
                    " size=" + width + "x" + height +
                    " rootX=" + rootX + " rootY=" + rootY);
            StringBuilder detail = new StringBuilder();
            for (String item : mappedWindows) detail.append(item).append('\n');
            prefs(context).edit().putString("charoite_last_mapped_windows",
                    detail.toString()).apply();
        }
    }

    /** Counts X11 drawing callbacks; does not claim that pixels are visible. */
    public static void recordX11ContentActivity(Context context,
                                                 int updates, int surfaces) {
        prefs(context).edit().putString("charoite_last_x11_updates",
                "Drawable updates: " + updates + "; surfaces: " + surfaces +
                "\nThis does not establish successful Direct3D presentation.").apply();
    }

    /** Purely informational: reports the existing saved audio backend. */
    public static void recordAudioBackend(Context context, String driver) {
        prefs(context).edit().putString("charoite_last_audio_backend",
                "Selected audio driver: " + (driver == null ? "unknown" : driver) +
                "\nNo audio playback verification is available from window FPS.").apply();
    }

    public static void recordWindowPlacement(Context context, String caption,
                                             int x, int y, int width, int height) {
        prefs(context).edit().putString("charoite_last_window_layout",
                "TPDP window centered: x=" + x + " y=" + y +
                " size=" + width + "x" + height).apply();
    }

    /** Owned runtime temp directory, explicitly outside all imported games. */
    public static void setDxvkLogDirectory(Context context, java.io.File folder) {
        if (folder == null || !folder.isDirectory()) return;
        prefs(context).edit().putString("charoite_dxvk_log_dir",
                folder.getAbsolutePath()).apply();
    }

    /** Read only a bounded tail of DXVK logs before the temporary rootfs
     * directory is cleared at the next launch. Never read game/save files. */
    private static void captureDxvkLogs(Context context) {
        String folder = prefs(context).getString("charoite_dxvk_log_dir", "");
        if (folder.isEmpty() || !folder.endsWith("/tmp/charoite-tpdp-dxvk"))
            return;
        java.io.File[] logs = new java.io.File(folder).listFiles();
        if (logs == null) return;
        java.util.Arrays.sort(logs, (a, b) -> a.getName().compareTo(b.getName()));
        StringBuilder report = new StringBuilder();
        int included = 0;
        for (java.io.File log : logs) {
            if (!log.isFile() || !log.getName().endsWith(".log")) continue;
            if (++included > 4) break;
            report.append("\n").append(log.getName())
                  .append(" (").append(log.length()).append(" bytes):\n");
            try (java.io.RandomAccessFile input =
                    new java.io.RandomAccessFile(log, "r")) {
                long offset = Math.max(0L, input.length() - 12000L);
                input.seek(offset);
                byte[] data = new byte[(int)(input.length() - offset)];
                input.readFully(data);
                report.append(new String(data,
                        java.nio.charset.StandardCharsets.UTF_8)).append("\n");
            } catch (Exception e) {
                report.append("Cannot read DXVK diagnostic: ").append(e).append("\n");
            }
        }
        if (included == 0)
            report.append("DXVK did not produce a .log file in its private directory. "
                    + "Verify native d3d9.dll loaded.\n");
        prefs(context).edit().putString("charoite_dxvk_log_excerpt",
                report.toString()).apply();
    }

    /** Called only after the user's explicit confirmation in Portal. */
    public static void requestPortalExit(Context context) {
        prefs(context).edit()
                .putBoolean(PORTAL_EXIT_REQUESTED, true)
                .putString("touhou_launch_status", "closed via Portal")
                .putString("touhou_launch_error", "")
                .apply();
    }

    public static void finishGuestProcess(Context context, int exitCode) {
        captureDxvkLogs(context);
        long elapsed = Math.max(0L,
                android.os.SystemClock.elapsedRealtime() - startedAtMillis);
        // Portal intentionally closes Wine/X11 and can cause launcher code
        // 137. This is not a game crash, and must not overwrite diagnostics
        // with "failed". Unexpected 137 without a user exit remains a failure.
        boolean intentionalExit = prefs(context).getBoolean(PORTAL_EXIT_REQUESTED, false);
        prefs(context).edit().putString("charoite_last_guest_exit",
                (intentionalExit ? "Portal exit confirmed; " : "Guest launcher ") +
                "returned " + exitCode + " after " +
                elapsed / 1000L + " seconds (does not prove game process exit).").apply();
        if (intentionalExit) {
            prefs(context).edit()
                    .putString("touhou_launch_status", "closed via Portal")
                    .putString("touhou_launch_error", "")
                    .apply();
        } else if (exitCode != 0) {
            fail(context, "Wine/Box64 exited with status " +
                    exitCode + ". See game exception details.");
        } else if (!"game window appeared".equals(
                prefs(context).getString("touhou_launch_status", ""))) {
            fail(context, "Windows program exited without a mapped game/installer window. " +
                    "If setup includes separate media files, import the whole installer folder.");
        }
    }

    /**
     * Sampling on GLRenderer's existing draw callback, no file I/O, no
     * strings, no allocations, no synchronization, and no render requests.
     * Exclude >=250ms idle intervals rather than mislabel paused scenes.
     * Native DXVK FPS and Android display pacing can still differ.
     */
    public static void recordAndroidDraw() {
        if (!shardFrameTimingEnabled) return;
        long now = android.os.SystemClock.elapsedRealtimeNanos();
        long previous = shardLastDrawNanos;
        shardLastDrawNanos = now;
        if (previous <= 0 || now <= previous) return;
        long milliseconds = (now - previous) / 1000000L;
        if (milliseconds >= 250L) return;
        shardIntervals++;
        if (milliseconds > 33L) shardGapsOver33Ms++;
        if (milliseconds > 50L) shardGapsOver50Ms++;
        if (milliseconds > 100L) shardGapsOver100Ms++;
        if (milliseconds > shardMaxActiveGapMs)
            shardMaxActiveGapMs = milliseconds;
    }

    /**
     * Profile CPU time spent submitting one Android GL draw. The renderer
     * itself may still be waiting on native GPU or guest frame production;
     * these counters DO NOT represent GPU execution or movie FPS.
     */
    public static long beginAndroidDrawMeasure() {
        return shardFrameTimingEnabled
                ? android.os.SystemClock.elapsedRealtimeNanos() : 0L;
    }

    public static void endAndroidDrawMeasure(long startNanos) {
        if (!shardFrameTimingEnabled || startNanos == 0L) return;
        long elapsed = android.os.SystemClock.elapsedRealtimeNanos() - startNanos;
        if (elapsed < 0L) return;
        long ms = elapsed / 1000000L;
        shardRenderSamples++;
        if (ms > 16L) shardDrawOver16Ms++;
        if (ms > 33L) shardDrawOver33Ms++;
        if (ms > shardLongestDrawMs) shardLongestDrawMs = ms;
    }

    public static String shardAndroidDrawReport() {
        if (!shardFrameTimingEnabled)
            return "No Shard frame-timing session recorded in this process.";
        long intervals = shardIntervals;
        if (intervals == 0)
            return "No continuous Android compositor draw intervals recorded.";
        return "GL compositor active intervals: " + intervals +
                "\nOver 33ms: " + shardGapsOver33Ms +
                "\nOver 50ms: " + shardGapsOver50Ms +
                "\nOver 100ms: " + shardGapsOver100Ms +
                "\nLongest active gap: " + shardMaxActiveGapMs + "ms" +
                "\nGL draw CPU samples: " + shardRenderSamples +
                "\nGL draws over 16ms: " + shardDrawOver16Ms +
                "\nGL draws over 33ms: " + shardDrawOver33Ms +
                "\nLongest GL draw CPU time: " + shardLongestDrawMs + "ms" +
                "\nExcluded idle intervals >=250ms. Neither metric is native guest FPS.";
    }

    public static void recordShardWindowChange(int id, int oldWidth,
                                               int oldHeight, int width,
                                               int height, String reason) {
        String entry = "X11 window " + id + ": " + oldWidth + "x" + oldHeight +
                " -> " + width + "x" + height + " (" + reason + ")";
        synchronized (shardWindowChanges) {
            if (shardWindowChanges.size() >= 16) shardWindowChanges.removeFirst();
            shardWindowChanges.addLast(entry);
        }
    }

    public static void recordLine(String line) {
        if (line == null || line.trim().isEmpty()) return;
        synchronized (lines) {
            if (lines.size() == MAX_LINES) lines.removeFirst();
            lines.addLast(line.length() > 600 ? line.substring(0, 600) : line);
        }
        if (tpdpGraphicsProbe) {
            String lower = line.toLowerCase(java.util.Locale.ROOT);
            if (lower.contains("err:seh") || lower.contains("winedbg") ||
                    lower.contains("unhandled exception") ||
                    lower.contains("fatal error") || lower.contains("segfault") ||
                    lower.contains("unimplemented") ||
                    lower.contains("not implemented")) {
                String clipped = line.length() > 450 ? line.substring(0, 450) : line;
                String key = clipped.replaceFirst("^[0-9a-fA-F]+:", "");
                synchronized (crashLines) {
                    if (!crashLines.containsKey(key) &&
                            crashLines.size() < MAX_CRASH_LINES)
                        crashLines.put(key, clipped);
                }
            }
        }
        // Wine game audio failures can occur independently of the D3D9
        // black screen. Preserve only short lines of the native backend
        // error stream; never alter ALSA/PulseAudio runtime selection.
        if (tpdpGraphicsProbe) {
            String check = line.toLowerCase(java.util.Locale.ROOT);
            if (check.contains("dsound") || check.contains("mmdevapi") ||
                    check.contains("alsa") || check.contains("pulse") ||
                    check.contains("audio") || check.contains("winmm") ||
                    check.contains("midi") || check.contains("xaudio")) {
                synchronized (audioLines) {
                    if (audioLines.size() == MAX_AUDIO_LINES) audioLines.removeFirst();
                    audioLines.addLast(line.length() > 400 ?
                            line.substring(0, 400) : line);
                }
            }
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
                // Prioritize meaningful renderer setup errors, not repetitive
                // esync and RPC teardown warnings that filled the old report.
                boolean significant = lower.contains("winediag") ||
                        lower.contains("wined3d") || lower.contains("wgl:") ||
                        lower.contains("ddraw") || lower.contains("d3d9") ||
                        lower.contains("vulkan") || lower.contains("dxvk") ||
                        lower.contains("shader") || lower.contains("pbuffer") ||
                        lower.contains("context_attribute") ||
                        lower.contains("surface") || lower.contains("texture");
                if (significant) {
                    String message = line.length() > 320 ? line.substring(0, 320) : line;
                    String key = message.replaceFirst("^[0-9a-fA-F]+:", "");
                    synchronized (earlyGraphics) {
                        if (!earlyGraphics.containsKey(key) &&
                                earlyGraphics.size() < MAX_EARLY_GRAPHICS)
                            earlyGraphics.put(key, message);
                    }
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
        report += "\n\nSHARD OF DREAMS INSTALLATION CHECK:\n" +
                shardInstallationScan(context);
        report += "\n\nSHARD OF DREAMS COMPATIBILITY:\n" +
                p.getString("charoite_shard_status", "Not checked.");
        report += "\n\nLAUNCH PACKAGE:\n" +
                p.getString("charoite_last_launch_files", "Not inspected.");
        report += "\n\nMAPPED WINDOWS:\n" +
                p.getString("charoite_last_mapped_windows", "No window events recorded.");
        report += "\n\nX11 DRAWABLE UPDATES:\n" +
                p.getString("charoite_last_x11_updates", "Not recorded.");
        report += "\n\nSHARD ANDROID FRAME PACING:\n" +
                shardAndroidDrawReport();
        report += "\n\nSHARD HANDHELD WINDOW SIZE CHANGES:\n";
        synchronized (shardWindowChanges) {
            if (shardWindowChanges.isEmpty()) report += "No Shard X11 window dimensions captured.";
            else for (String change : shardWindowChanges) report += change + "\n";
        }
        report += "\n\nTPDP WINDOW LAYOUT:\n" +
                p.getString("charoite_last_window_layout", "Not recorded.");
        report += "\n\nGUEST LAUNCHER EXIT:\n" +
                p.getString("charoite_last_guest_exit", "Not recorded.");
        report += "\n\nAUDIO BACKEND:\n" +
                p.getString("charoite_last_audio_backend", "Not recorded.");
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
            report += "\n\nDXVK D3D9 DIAGNOSTIC FILES:\n" +
                    p.getString("charoite_dxvk_log_excerpt",
                            "No DXVK diagnostic files captured.");
            report += "\n\nEXCEPTIONS / UNIMPLEMENTED GRAPHICS OPERATIONS:\n";
            synchronized (crashLines) {
                if (crashLines.isEmpty()) report += "None captured.\n";
                else for (String event : crashLines.values())
                    report += event + "\n";
            }
            report += "\n\nFIRST DISTINCT DIRECT3D / GPU EVENTS:\n";
            synchronized (earlyGraphics) {
                if (earlyGraphics.isEmpty())
                    report += "No renderer setup event captured.\n";
                else for (String event : earlyGraphics.values())
                    report += event + "\n";
            }
            report += "\n\nTPDP DIRECT3D / GRAPHICS OUTPUT (last " +
                    MAX_GRAPHICS_LINES + " matching lines):\n";
            synchronized (graphicsLines) {
                if (graphicsLines.isEmpty())
                    report += "No graphics messages captured; this does NOT verify rendering.\n";
                else for (String line : graphicsLines) report += line + "\n";
            }
            report += "A visible image must still be confirmed on the phone.\n";
            report += "\nTPDP AUDIO / DIRECTSOUND OUTPUT (last " +
                    MAX_AUDIO_LINES + " matching lines):\n";
            synchronized (audioLines) {
                if (audioLines.isEmpty())
                    report += "No audio messages captured; silence is not ruled out.\n";
                else for (String line : audioLines) report += line + "\n";
            }
        }
        report += CharoiteRenderingDiagnostics.report(context);
        return report;
    }

    private static SharedPreferences prefs(Context context) {
        return PreferenceManager.getDefaultSharedPreferences(context);
    }
}

package com.charoitegames.core;

import android.content.Context;
import java.io.File;
import java.io.FileInputStream;
import java.io.RandomAccessFile;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Comparator;

/**
 * Read-only forensic report about the already-used, one-shot Wine27 v3 scratch.
 * Absolutely no native code, Wineboot, wineserver, staging or new prefix starts.
 * Never opens Wine22, earlier v1/v2 scratch, rootfs, installed games or saves.
 */
public final class CharoiteWine27V3Forensics {
    private static final String PACKAGE = "com.charoitx";
    private static final String SCRATCH = "charoite-next-wine27-first-prefix-v3";
    private static final int LOG_LIMIT = 12288;
    private CharoiteWine27V3Forensics() {}

    private static File checked(File root, String relative) throws Exception {
        File base = root.getCanonicalFile();
        File item = new File(base, relative);
        File resolved = item.getCanonicalFile();
        // Never follow symbolic links, including links created inside a prefix.
        if (resolved.equals(base) || !resolved.toPath().startsWith(base.toPath())
                || !resolved.equals(item.getAbsoluteFile()))
            throw new SecurityException("v3 inspection path is not an isolated direct child");
        return item;
    }

    private static String display(String s) {
        return s.replace('\n', '_').replace('\r', '_');
    }

    private static void list(StringBuilder out, File root, String path) throws Exception {
        File dir = checked(root, path);
        out.append(path).append(" entries: ");
        if (!dir.exists()) {
            out.append("absent\n");
            return;
        }
        if (!dir.isDirectory()) {
            out.append("not a directory\n");
            return;
        }
        File[] entries = dir.listFiles();
        if (entries == null) {
            out.append("unreadable\n");
            return;
        }
        Arrays.sort(entries, Comparator.comparing(File::getName));
        out.append(entries.length).append(" (showing at most 32)\n");
        int count = 0;
        for (File entry : entries) {
            if (count++ == 32) break;
            String name = entry.getName();
            if (!name.matches("[A-Za-z0-9_.@ :+()$-]{1,128}")) {
                out.append("  [unusual entry name omitted]\n");
                continue;
            }
            // Canonical mismatch means a symlink; do not follow it.
            File direct = new File(dir, name);
            boolean safe = direct.getCanonicalFile().equals(direct.getAbsoluteFile());
            out.append("  ").append(display(name)).append(": ");
            if (!safe) out.append("link (not followed)");
            else if (entry.isDirectory()) out.append("directory");
            else if (entry.isFile()) out.append("file, ").append(entry.length()).append(" bytes");
            else out.append("other");
            out.append('\n');
        }
    }

    private static void status(StringBuilder out, File root, String path) throws Exception {
        File file = checked(root, path);
        out.append(path).append(": ");
        if (!file.exists()) out.append("absent");
        else if (file.isFile()) out.append("file, ").append(file.length()).append(" bytes");
        else if (file.isDirectory()) out.append("directory");
        else out.append("other");
        out.append('\n');
    }

    private static String clippedLog(File file) throws Exception {
        if (!file.isFile()) return "(not present)";
        long length = file.length();
        if (length == 0) return "(empty)";
        if (length > 32L * 1024L * 1024L) return "(oversized; not read)";
        try (RandomAccessFile input = new RandomAccessFile(file, "r")) {
            int n = (int) Math.min(length, LOG_LIMIT);
            if (length <= LOG_LIMIT) {
                byte[] bytes = new byte[n];
                input.readFully(bytes);
                return new String(bytes, StandardCharsets.UTF_8);
            }
            int half = LOG_LIMIT / 2;
            byte[] start = new byte[half];
            byte[] tail = new byte[half];
            input.readFully(start);
            input.seek(length - half);
            input.readFully(tail);
            return new String(start, StandardCharsets.UTF_8)
                    + "\n[... middle omitted, total " + length + " bytes ...]\n"
                    + new String(tail, StandardCharsets.UTF_8);
        }
    }

    public static String run(Context context) {
        StringBuilder out = new StringBuilder();
        out.append("CHAROITE NEXT — READ-ONLY FAILED WINE27 V3 FORENSICS\n");
        out.append("No Wineboot, native execution, wineserver, scratch write or cleanup.\n");
        out.append("Only the exact existing v3 private scratch is inspected.\n");
        out.append("Existing Wine22, prior v1/v2 scratch, games, saves and prefixes: NOT ACCESSED\n");
        if (!PACKAGE.equals(context.getPackageName()))
            return out.append("RESULT: BLOCKED — wrong Android package\n").toString();
        try {
            File base = context.getNoBackupFilesDir().getCanonicalFile();
            File scratch = checked(base, SCRATCH);
            if (!scratch.isDirectory()
                    || !scratch.getCanonicalFile().equals(scratch.getAbsoluteFile())
                    || !scratch.getCanonicalFile().getParentFile().equals(base))
                return out.append("RESULT: BLOCKED — isolated v3 scratch absent or unsafe\n").toString();
            out.append("v3 scratch exists: true (not modified)\n");
            for (String item : new String[]{
                    "wineboot.log", "wineserver-stop.log",
                    "runtime/share/wine/nls/locale.nls",
                    "runtime/share/wine/nls/l_intl.nls",
                    "runtime/lib/wine/arm64-windows/wineboot.exe",
                    "runtime/lib/wine/arm64ec-windows/ntdll.dll",
                    "prefix", "prefix/system.reg", "prefix/user.reg",
                    "prefix/userdef.reg", "prefix/.update-timestamp"
            }) status(out, scratch, item);
            list(out, scratch, "prefix");
            // Wine may initialize a few key subdirectories before the error.
            for (String item : new String[]{"prefix/drive_c", "prefix/dosdevices"})
                list(out, scratch, item);
            out.append("Wineboot log (head/tail, max 12 KiB):\n")
               .append(clippedLog(checked(scratch, "wineboot.log"))).append('\n');
            out.append("Isolated wineserver-stop log (head/tail, max 12 KiB):\n")
               .append(clippedLog(checked(scratch, "wineserver-stop.log"))).append('\n');
            out.append("RESULT: PASS — read-only v3 evidence collected; boot failure unresolved\n");
        } catch (Exception ex) {
            out.append("RESULT: BLOCKED — read-only inspection: ")
               .append(ex.getClass().getSimpleName()).append('\n');
        }
        out.append("No new attempt authorized or executed. Preserve v1/v2/v3 evidence.\n");
        return out.toString();
    }
}

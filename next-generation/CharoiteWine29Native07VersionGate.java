package com.charoitegames.core;

import android.content.Context;
import android.os.Build;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Explicitly opted-in, BOUNDED, native-only Wine29 .0.7 version preflight.
 *
 * This is NOT Wineboot, Windows PE execution, a prefix/session or a game.
 * Before any execution: requires the complete read-only archive/legacy audit
 * and separately re-hashes all three APK-owned native ELF binaries. No file
 * is created, moved, extracted, unlinked or modified; older Wine28 v1-v9
 * evidence and all game/prefix data are never accessed.
 */
public final class CharoiteWine29Native07VersionGate {
    private static final String PACKAGE = "com.charoitx";
    private static final String SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767";
    private static final String VERSION = "wine10-arm64ec-bootstrap.0.7";
    private static final String ASSET = "charoite-next/wine29-native07/wine29-native07-index.json";
    private static final String SOURCE_ARCHIVE =
            "charoite-next/wine29-native07/wine29-source-matched.bundle";
    private static final long SOURCE_RUN = 41749167248L;
    private static final long SOURCE_ARTIFACT = 13284932342L;
    private static final int MAX_JSON = 65536;
    private static final int MAX_OUTPUT = 4096;
    private static final long MAX_ELF = 32L * 1024L * 1024L;
    private static final long TIMEOUT_SECONDS = 7L;
    private static final String LOADER = "libcharoite_wine29_loader.so";
    private static final String SERVER = "libcharoite_wine29_wineserver.so";
    private static final String NTDLL = "libcharoite_wine29_ntdll.so";

    private CharoiteWine29Native07VersionGate() {}

    private static String readIndex(Context context) throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (InputStream input = context.getAssets().open(ASSET)) {
            byte[] buffer = new byte[2048];
            int count;
            while ((count = input.read(buffer)) != -1) {
                if (bytes.size() + count > MAX_JSON)
                    throw new SecurityException("Wine29 source index exceeds bound");
                bytes.write(buffer, 0, count);
            }
        }
        return bytes.toString("UTF-8");
    }

    private static String sha(File file) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        try (InputStream input = new FileInputStream(file)) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) != -1) md.update(buffer, 0, count);
        }
        StringBuilder value = new StringBuilder();
        for (byte b : md.digest())
            value.append(String.format(Locale.US, "%02x", b & 255));
        return value.toString();
    }

    private static File verifyElf(File directory, JSONObject components, String key,
                                  String source, String filename) throws Exception {
        JSONObject rec = components.getJSONObject(key);
        if (!filename.equals(rec.getString("filename")) ||
            !source.equals(rec.getString("source")) ||
            !"AArch64".equals(rec.getString("machine")) ||
            rec.getLong("size") <= 0 || rec.getLong("size") > MAX_ELF ||
            !rec.getString("sha256").matches("[0-9a-f]{64}"))
            throw new SecurityException("Wine29 ELF source/ABI identity mismatch: " + key);
        JSONArray alignments = rec.getJSONArray("load_alignments");
        if (alignments.length() == 0) throw new SecurityException("Missing 16 KiB ELF alignment");
        for (int i = 0; i < alignments.length(); i++)
            if (alignments.getLong(i) < 16384)
                throw new SecurityException("Invalid ELF alignment: " + key);
        JSONArray deps = rec.getJSONArray("needed");
        for (int i = 0; i < deps.length(); i++)
            if ("libwine.so".equals(deps.getString(i)))
                throw new SecurityException("Unapproved Wine native dependency: " + key);
        File binary = new File(directory, filename);
        if (!binary.getCanonicalFile().getParentFile().equals(directory) ||
            !binary.getCanonicalFile().equals(binary.getAbsoluteFile()) ||
            !binary.isFile() || !binary.canExecute() ||
            binary.length() != rec.getLong("size") ||
            !sha(binary).equals(rec.getString("sha256")))
            throw new SecurityException("Wine29 APK native ELF hash mismatch: " + key);
        return binary;
    }

    private static String capture(InputStream stream) throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (InputStream in = stream) {
            byte[] buffer = new byte[512];
            int count;
            while ((count = in.read(buffer)) != -1) {
                if (bytes.size() + count > MAX_OUTPUT)
                    throw new SecurityException("Unbounded Wine29 version output");
                bytes.write(buffer, 0, count);
            }
        }
        return bytes.toString("UTF-8").trim();
    }

    private static String version(File binary, File nativeDir, String exact) throws Exception {
        Process process = null;
        try {
            // Exact command and one argument only. No shell, no .exe, no wineboot.
            ProcessBuilder builder = new ProcessBuilder(binary.getAbsolutePath(), "--version");
            builder.redirectErrorStream(true);
            Map<String, String> env = builder.environment();
            env.clear(); // Excludes inherited HOME, WINEPREFIX, LD_*, Wine28 selectors.
            env.put("PATH", "/system/bin:/system/xbin");
            env.put("WINEDEBUG", "-all");
            // The source-built Wine29 loader rejects PARTIAL triad selectors.
            // For --version ONLY, point all three to the same verified,
            // read-only APK-owned library directory. This directory holds NO
            // Windows PE or NLS layout. A later PE/NLS load must FAIL CLOSED:
            // this is never an environment for Windows EXE/Wineboot execution.
            final String apkNative = nativeDir.getCanonicalPath();
            if (new File(nativeDir, "ntdll.dll").exists() ||
                new File(nativeDir, "apisetschema.dll").exists() ||
                new File(nativeDir, "nls").exists())
                throw new SecurityException("Native version-only directory unexpectedly contains PE/NLS files");
            env.put("CHAROITE_WINE29_NATIVE_DIR", apkNative);
            env.put("CHAROITE_WINE29_PE_DIR", apkNative);
            env.put("CHAROITE_WINE29_DATA_DIR", apkNative);
            process = builder.start();
            if (!process.waitFor(TIMEOUT_SECONDS, TimeUnit.SECONDS)) {
                process.destroyForcibly();
                process.waitFor(2L, TimeUnit.SECONDS);
                throw new SecurityException("Wine29 version-only process timed out");
            }
            int status = process.exitValue();
            String output = capture(process.getInputStream());
            if (status != 0 || !exact.equals(output))
                throw new SecurityException("Wine29 --version exit=" + status + " output=" + output);
            return output;
        } finally {
            if (process != null && process.isAlive()) process.destroyForcibly();
        }
    }

    public static String run(Context context) {
        StringBuilder out = new StringBuilder();
        out.append("CHAROITE NEXT — ISOLATED WINE29 .0.7 NATIVE VERSION-ONLY GATE\n");
        out.append("Scope: verified APK native loader + wineserver --version ONLY\n");
        out.append("All three mandatory selectors are APK-native-directory only; PE/NLS runtime NOT staged\n");
        out.append("User consent: THIS BUTTON ONLY; no automatic start\n");
        out.append("Wineboot, PE/Windows EXE, prefix, graphics, FEX, games: NOT ATTEMPTED\n");
        out.append("Wine28 v1–v9, existing prefixes, game saves, rootfs: NOT ACCESSED\n\n");
        if (!PACKAGE.equals(context.getPackageName()) || Build.VERSION.SDK_INT < 26)
            return out.append("RESULT: BLOCKED — untrusted package or Android version\n").toString();

        // First run the existing independently verified, read-only phone audit.
        String audit = CharoiteWine29Native07Audit.run(context);
        if (!audit.contains(
              "RESULT: PASS — APK-owned Wine29 0.7 source and native hashes verified; NOT RUNNABLE")) {
            out.append(audit);
            return out.append("RESULT: BLOCKED — prerequisite Wine29 APK audit not passed\n")
                      .toString();
        }
        out.append("Existing .0.6 unchanged, Wine29 .0.7 archive, 3 APK ELFs: SHA-256 PASS\n");
        try {
            JSONObject index = new JSONObject(readIndex(context));
            if (index.getInt("schema_version") != 1 ||
                !PACKAGE.equals(index.getString("package")) ||
                !VERSION.equals(index.getString("bundle_version")) ||
                !SOURCE.equals(index.getString("wine_source_commit")) ||
                SOURCE_RUN != index.getLong("source_run") ||
                SOURCE_ARTIFACT != index.getLong("source_artifact") ||
                !SOURCE_ARCHIVE.equals(index.getString("archive_asset")) ||
                index.getInt("component_count") != 27 || index.getInt("pe_count") != 24 ||
                index.getInt("nls_count") != 76 || index.getInt("native_elf_count") != 3 ||
                !index.getBoolean("native_elf_installed_as_apk_libs") ||
                !index.getBoolean("source_native_cohort_verified") ||
                index.getBoolean("native_elf_executed") ||
                index.getBoolean("wineboot_executed") ||
                index.getBoolean("windows_exe_executed") ||
                index.getBoolean("launch_ready") ||
                index.getBoolean("device_tested") ||
                index.getBoolean("installable_as_runtime") ||
                index.getBoolean("prefix_created") ||
                index.getBoolean("fex_installed") ||
                index.getBoolean("graphics_verified") ||
                index.getBoolean("anti_cheat_supported"))
                throw new SecurityException("Invalid isolated Wine29 0.7 version-only source gate");

            File directory = new File(context.getApplicationInfo().nativeLibraryDir)
                    .getCanonicalFile();
            JSONObject components = index.getJSONObject("native_components");
            if (components.length() != 3)
                throw new SecurityException("Not exactly three Wine29 native components");
            File loader = verifyElf(directory, components, "wine",
                    "runtime/bin/wine", LOADER);
            verifyElf(directory, components, "ntdll_unix",
                    "runtime/lib/ntdll.so", NTDLL);
            File server = verifyElf(directory, components, "wineserver",
                    "runtime/bin/wineserver", SERVER);
            out.append("Three APK-native Wine29 ELF hashes: REVERIFIED PASS\n");
            out.append("Wine29 loader --version: ")
               .append(version(loader, directory, "wine-10.0")).append('\n');
            out.append("Wine29 wineserver --version: ")
               .append(version(server, directory, "Wine 10.0")).append('\n');
            out.append("Both native --version exits: 0\n");
            out.append("RESULT: PASS — isolated Wine29 native version-only gate; NOT RUNNABLE\n");
        } catch (Exception error) {
            out.append("RESULT: BLOCKED — ")
               .append(error.getClass().getSimpleName())
               .append(": ").append(error.getMessage()).append('\n');
        }
        out.append("New Wine29 prefix, Wineboot and Windows EXE: NOT ATTEMPTED\n");
        return out.toString();
    }
}

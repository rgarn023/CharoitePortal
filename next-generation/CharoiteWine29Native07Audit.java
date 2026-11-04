package com.charoitegames.core;

import android.content.Context;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.Locale;
import org.json.JSONObject;

/**
 * READ-ONLY verification of the isolated Wine29 0.7 APK cohort.
 *
 * No staging, process creation, Wineboot, Windows execution, filesystem writes,
 * network calls, rootfs, old Wine28 scratch or user-prefix access.
 * The 0.7 ELF library names differ from all older native Wine generations.
 */
public final class CharoiteWine29Native07Audit {
    private static final String PACKAGE = "com.charoitx";
    private static final String SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767";
    private static final String VERSION = "wine10-arm64ec-bootstrap.0.7";
    private static final String INDEX = "charoite-next/wine29-native07/wine29-native07-index.json";
    private static final String BUNDLE = "charoite-next/wine29-native07/wine29-source-matched.bundle";
    private static final String OLD_BUNDLE = "charoite-next/wine-bootstrap-29.bundle";
    private static final String OLD_INDEX = "charoite-next/wine-bootstrap-29-index.json";
    private static final long SOURCE_RUN = 41749167248L;
    private static final long SOURCE_ARTIFACT = 13284932342L;
    private static final long MAX_ARCHIVE = 128L * 1024L * 1024L;
    private static final String[] KEYS = {"wine", "wineserver", "ntdll_unix"};
    private static final String[] SOURCES = {
        "runtime/bin/wine", "runtime/bin/wineserver", "runtime/lib/ntdll.so"
    };
    private static final String[] FILES = {
        "libcharoite_wine29_loader.so",
        "libcharoite_wine29_wineserver.so",
        "libcharoite_wine29_ntdll.so"
    };

    private CharoiteWine29Native07Audit() {}

    private static String hex(byte[] raw) {
        StringBuilder out = new StringBuilder();
        for (byte b : raw)
            out.append(String.format(Locale.US, "%02x", b & 255));
        return out.toString();
    }

    private static String hashStream(InputStream input, long limit, long expectedSize) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] buffer = new byte[32768];
        long total = 0;
        try (InputStream in = input) {
            int count;
            while ((count = in.read(buffer)) != -1) {
                total += count;
                if (total > limit || total > expectedSize)
                    throw new SecurityException("Wine29 source asset size exceeds verified limit");
                digest.update(buffer, 0, count);
            }
        }
        if (total != expectedSize) throw new SecurityException("Wine29 source asset size drift");
        return hex(digest.digest());
    }

    private static JSONObject jsonAsset(Context context, String asset) throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (InputStream input = context.getAssets().open(asset)) {
            byte[] chunk = new byte[4096];
            int n;
            while ((n = input.read(chunk)) != -1) {
                if (bytes.size() + n > 32768)
                    throw new SecurityException("Wine29 source index too large");
                bytes.write(chunk, 0, n);
            }
        }
        return new JSONObject(bytes.toString("UTF-8"));
    }

    private static void verifyReadiness(JSONObject index) throws Exception {
        if (!PACKAGE.equals(index.getString("package")) ||
            index.getInt("schema_version") != 1 ||
            !SOURCE.equals(index.getString("wine_source_commit")) ||
            !VERSION.equals(index.getString("bundle_version")) ||
            index.getLong("source_run") != SOURCE_RUN ||
            index.getLong("source_artifact") != SOURCE_ARTIFACT ||
            !BUNDLE.equals(index.getString("archive_asset")) ||
            !OLD_BUNDLE.equals(index.getString("original_wine29_asset")) ||
            index.getInt("component_count") != 27 ||
            index.getInt("pe_count") != 24 ||
            index.getInt("nls_count") != 76 ||
            index.getInt("native_elf_count") != 3 ||
            index.getInt("native_elf_in_archive") != 3 ||
            !index.getBoolean("native_elf_installed_as_apk_libs") ||
            !index.getBoolean("source_native_cohort_verified") ||
            index.getBoolean("native_elf_executed") ||
            index.getBoolean("windows_exe_executed") ||
            index.getBoolean("wineboot_executed") ||
            index.getBoolean("launch_ready") ||
            index.getBoolean("device_tested") ||
            index.getBoolean("installable_as_runtime") ||
            index.getBoolean("prefix_created") ||
            index.getBoolean("fex_installed") ||
            index.getBoolean("graphics_verified") ||
            index.getBoolean("anti_cheat_supported"))
            throw new SecurityException("Untrusted Wine29 source cohort or runnable claim");
        for (String name : new String[] {
            "archive_sha256", "original_wine29_sha256",
            "source_delta_sha256", "source_proof_sha256"
        }) {
            if (!index.getString(name).matches("[0-9a-f]{64}"))
                throw new SecurityException("Untrusted Wine29 source digest: " + name);
        }
    }

    public static String run(Context context) {
        StringBuilder out = new StringBuilder();
        out.append("CHAROITE NEXT — ISOLATED WINE29 0.7 APK READ-ONLY VERIFY\n");
        out.append("Scope: separate source-matched archive and three APK native ELF hashes\n");
        out.append("No Wine, Wineboot, wineserver, Windows EXE or prefix execution\n");
        out.append("Existing Wine28 v1–v9, game saves, rootfs and user prefixes: NOT ACCESSED\n\n");
        if (!PACKAGE.equals(context.getPackageName()))
            return out.append("RESULT: BLOCKED — wrong Android package\n").toString();
        try {
            JSONObject proof = jsonAsset(context, INDEX);
            verifyReadiness(proof);
            long size = proof.getLong("archive_size");
            if (size <= 0 || size > MAX_ARCHIVE)
                throw new SecurityException("Wine29 archive outside verified size bound");
            String archiveHash = hashStream(context.getAssets().open(BUNDLE), MAX_ARCHIVE, size);
            if (!archiveHash.equals(proof.getString("archive_sha256")))
                throw new SecurityException("Wine29 0.7 archive mismatch");
            out.append("Wine29 .0.7 27-component / 76-NLS source archive: SHA-256 PASS\n");

            // Verify the prior .0.6 cohort is still packaged and unchanged.
            // Never open old on-device staging directories or Wine prefixes.
            JSONObject prior = jsonAsset(context, OLD_INDEX);
            if (!"wine10-arm64ec-bootstrap.0.6".equals(prior.getString("bundle_version")) ||
                !proof.getString("original_wine29_sha256").equals(prior.getString("archive_sha256")))
                throw new SecurityException("Old Wine29 archive metadata changed");
            long olderSize = prior.getLong("archive_size");
            if (olderSize <= 0 || olderSize > MAX_ARCHIVE)
                throw new SecurityException("Old Wine29 asset missing or invalid");
            String oldHash = hashStream(context.getAssets().open(OLD_BUNDLE), MAX_ARCHIVE, olderSize);
            if (!oldHash.equals(proof.getString("original_wine29_sha256")))
                throw new SecurityException("Original Wine29 0.6 archive changed");
            out.append("Previous Wine29 .0.6 APK archive: UNCHANGED SHA-256 PASS\n");

            File directory = new File(context.getApplicationInfo().nativeLibraryDir).getCanonicalFile();
            JSONObject nativeFiles = proof.getJSONObject("native_components");
            if (nativeFiles.length() != 3)
                throw new SecurityException("Unexpected Wine29 native library inventory");
            for (int i = 0; i < KEYS.length; i++) {
                JSONObject record = nativeFiles.getJSONObject(KEYS[i]);
                String name = FILES[i];
                File binary = new File(directory, name);
                if (!name.equals(record.getString("filename")) ||
                    !SOURCES[i].equals(record.getString("source")) ||
                    !"AArch64".equals(record.getString("machine")) ||
                    !binary.getCanonicalFile().getParentFile().equals(directory) ||
                    !binary.getCanonicalFile().equals(binary.getAbsoluteFile()) ||
                    !binary.isFile() || record.getLong("size") <= 0 ||
                    record.getLong("size") > 32L * 1024L * 1024L ||
                    !record.getString("sha256").matches("[0-9a-f]{64}"))
                    throw new SecurityException("Untrusted Wine29 ELF: " + KEYS[i]);
                long expected = record.getLong("size");
                String value = hashStream(new FileInputStream(binary), 32L * 1024L * 1024L, expected);
                if (!value.equals(record.getString("sha256")))
                    throw new SecurityException("Wine29 ELF hash drift: " + KEYS[i]);
                out.append("APK-native ").append(KEYS[i]).append(": SHA-256 PASS\n");
            }
            out.append("Wine29 version: ").append(VERSION).append('\n');
            out.append("Native Wine29 code: NEVER EXECUTED\n");
            out.append("Wineboot and game engine: NOT TESTED\n");
            out.append("RESULT: PASS — APK-owned Wine29 0.7 source and native hashes verified; NOT RUNNABLE\n");
        } catch (Exception error) {
            out.append("RESULT: BLOCKED — ").append(error.getClass().getSimpleName())
                .append(": ").append(error.getMessage()).append('\n');
        }
        return out.toString();
    }
}

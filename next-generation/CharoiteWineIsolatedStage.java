package com.charoitegames.core;

import android.content.Context;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * User-approved and fail-closed staging of verified Windows PE/NLS DATA ONLY.
 * Never stages ELF/native executables, runs a process, creates a Wine prefix,
 * touches the existing rootfs, or deletes/replaces an existing staged file.
 * An interrupted .pending directory is left untouched and blocks a retry.
 */
public final class CharoiteWineIsolatedStage {
    private static final String PACKAGE = "com.charoitx";
    private static final String SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767";
    private static final String INDEX = "charoite-next/wine-module-staging-index.json";
    private static final String PAYLOAD = "charoite-next/wine-bootstrap-payload.json";
    private static final String ASSET_ROOT = "charoite-next/wine-modules/";
    private static final String ROOT = "charoite-next-isolated-wine";
    private static final String FINAL = "wine10-arm64ec-bootstrap-0.4-staged";
    private static final String PENDING = ".wine10-arm64ec-bootstrap-0.4-pending";
    private static final long MAX_SINGLE = 32L * 1024L * 1024L;
    private static final long MAX_TOTAL = 128L * 1024L * 1024L;
    private CharoiteWineIsolatedStage() {}

    private static String jsonAsset(Context context, String path) throws Exception {
        try (InputStream input = context.getAssets().open(path)) {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            byte[] buffer = new byte[2048];
            int read;
            while ((read = input.read(buffer)) != -1) {
                if (output.size() + read > 65536)
                    throw new SecurityException("Oversized source inventory");
                output.write(buffer, 0, read);
            }
            return output.toString("UTF-8");
        }
    }

    private static String hex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte b : bytes)
            result.append(String.format(Locale.US, "%02x", b & 255));
        return result.toString();
    }

    private static boolean hashMatches(File file, long size, String expected) throws Exception {
        if (!file.isFile() || file.length() != size || !file.getCanonicalFile().equals(file.getAbsoluteFile()))
            return false;
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream input = new FileInputStream(file)) {
            byte[] buffer = new byte[32768];
            int n;
            while ((n = input.read(buffer)) != -1) digest.update(buffer, 0, n);
        }
        return expected.equals(hex(digest.digest()));
    }

    private static File within(File directory, String relative) throws Exception {
        File target = new File(directory, relative);
        File resolved = target.getCanonicalFile();
        File root = directory.getCanonicalFile();
        if (!resolved.toPath().startsWith(root.toPath()) || resolved.equals(root)
                || !resolved.equals(target.getAbsoluteFile()))
            throw new SecurityException("Staging path escapes isolated root");
        return target;
    }

    private static String verifiedPath(String relative) {
        if (!(relative.matches("pe/arm64ec/[a-z0-9_]+\\.dll")
                || relative.equals("pe/arm64/wineboot.exe")
                || relative.matches("nls/[a-z_0-9]+\\.nls")))
            throw new SecurityException("Unrecognized Windows PE/NLS path");
        return relative;
    }

    private static JSONObject validatedInventory(Context context) throws Exception {
        if (!PACKAGE.equals(context.getPackageName()))
            throw new SecurityException("Wrong Android package");
        // Cross-check the immutable full archive before staging any individual modules.
        String archiveReport = CharoiteWinePayloadAudit.report(context);
        if (!archiveReport.contains("RESULT: PASS — immutable APK payload verified; NOT runnable"))
            throw new SecurityException("Full source-built bundle verification failed");
        JSONObject payload = new JSONObject(jsonAsset(context, PAYLOAD));
        JSONObject index = new JSONObject(jsonAsset(context, INDEX));
        if (index.getInt("schema_version") != 1
                || !PACKAGE.equals(index.getString("android_package"))
                || !SOURCE.equals(index.getString("wine_source_sha"))
                || index.getLong("source_run") != 40898982875L
                || !payload.getString("archive_sha256").equals(index.getString("archive_sha256"))
                || index.getInt("file_count") != 95
                || index.getInt("pe_count") != 19
                || index.getInt("nls_count") != 76
                || index.getBoolean("launch_ready")
                || index.getBoolean("native_elf_installed")
                || index.getBoolean("prefix_created")
                || index.getBoolean("wineboot_tested")
                || index.getBoolean("anti_cheat_supported"))
            throw new SecurityException("Untrusted staging inventory");
        JSONArray files = index.getJSONArray("files");
        if (files.length() != 95 || index.getLong("total_bytes") > MAX_TOTAL)
            throw new SecurityException("Wrong staging count or limit");
        long total = 0;
        int pe = 0, nls = 0;
        String previous = "";
        HashSet<String> seenAssets = new HashSet<>();
        for (int i = 0; i < files.length(); i++) {
            JSONObject item = files.getJSONObject(i);
            String relative = verifiedPath(item.getString("path"));
            String asset = ASSET_ROOT + relative.replace('/', '_') + ".bin";
            String digest = item.getString("sha256");
            long size = item.getLong("size");
            if (!relative.equals(item.getString("source").replaceFirst("^runtime/", ""))
                    || !asset.equals(item.getString("asset"))
                    || relative.compareTo(previous) <= 0
                    || !seenAssets.add(asset)
                    || size < 1 || size > MAX_SINGLE
                    || !digest.matches("[0-9a-f]{64}"))
                throw new SecurityException("Unsafe or duplicate staged module entry");
            previous = relative;
            total += size;
            if (relative.startsWith("nls/")) nls++; else pe++;
        }
        if (total != index.getLong("total_bytes") || total > MAX_TOTAL
                || pe != 19 || nls != 76)
            throw new SecurityException("Inconsistent staged PE/NLS inventory");
        return index;
    }

    private static void verifyFiles(File finalDirectory, JSONArray entries) throws Exception {
        if (!finalDirectory.isDirectory())
            throw new SecurityException("No complete staged directory");
        for (int i = 0; i < entries.length(); i++) {
            JSONObject entry = entries.getJSONObject(i);
            File target = within(finalDirectory, entry.getString("path"));
            if (!hashMatches(target, entry.getLong("size"), entry.getString("sha256")))
                throw new SecurityException("Staged file does not match audited SHA-256");
        }
    }

    /**
     * Read-only verification of an already staged slot. Does not mkdir, copy,
     * delete, rename or execute anything; a pending transaction blocks testing.
     */
    public static String verifyOnly(Context context) {
        StringBuilder report = new StringBuilder();
        report.append("CHAROITE NEXT — STAGED PE/NLS READ-ONLY VERIFY\\n");
        report.append("Existing prefixes, saves, and rootfs: NOT ACCESSED\\n");
        try {
            JSONObject index = validatedInventory(context);
            File base = context.getNoBackupFilesDir().getCanonicalFile();
            File directory = new File(base, ROOT);
            if (!directory.getCanonicalFile().getParentFile().equals(base)
                    || !directory.isDirectory())
                throw new SecurityException("Isolated staging directory missing");
            File pending = within(directory, PENDING);
            File complete = within(directory, FINAL);
            if (pending.exists())
                throw new SecurityException("Incomplete pending staging is quarantined");
            verifyFiles(complete, index.getJSONArray("files"));
            report.append("Staged Windows PE: 19/19 verified\\n");
            report.append("Staged Wine NLS: 76/76 verified\\n");
            report.append("No native executable or Wine prefix was installed\\n");
            report.append("RESULT: PASS — staged module data verified; NOT runnable\\n");
        } catch (Exception error) {
            report.append("RESULT: BLOCKED — ").append(error.getClass().getSimpleName()).append("\\n");
        }
        return report.toString();
    }

    public static String run(Context context) {
        StringBuilder report = new StringBuilder();
        report.append("CHAROITE NEXT — ISOLATED WINE PE/NLS STAGING\n");
        report.append("Permission: user-initiated module DATA staging only\n");
        report.append("Target: Next-owned no-backup staging directory\n");
        report.append("Existing Wine prefixes, game saves, rootfs: NOT ACCESSED\n");
        report.append("Android native ELF, FEX, graphics: NOT INSTALLED\n");
        report.append("No Wine executable, wineserver session or wineboot is started\n");
        try {
            JSONObject index = validatedInventory(context);
            JSONArray entries = index.getJSONArray("files");
            File noBackup = context.getNoBackupFilesDir().getCanonicalFile();
            File directory = new File(noBackup, ROOT);
            if (!directory.getCanonicalFile().getParentFile().equals(noBackup))
                throw new SecurityException("Non-private staging parent");
            if (!directory.exists() && !directory.mkdir())
                throw new SecurityException("Cannot create isolated staging root");
            File pending = within(directory, PENDING);
            File complete = within(directory, FINAL);
            if (pending.exists())
                throw new SecurityException("Existing incomplete staging; no overwrite or cleanup attempted");
            if (complete.exists()) {
                verifyFiles(complete, entries);
                report.append("Existing staged PE/NLS hashes: 95/95 PASS\n");
                report.append("RESULT: PASS — existing isolated data verified; NOT runnable\n");
                return report.toString();
            }
            if (!pending.mkdir())
                throw new SecurityException("Cannot create private pending staging");
            byte[] buffer = new byte[32768];
            for (int i = 0; i < entries.length(); i++) {
                JSONObject entry = entries.getJSONObject(i);
                String relative = entry.getString("path");
                File destination = within(pending, relative);
                File parent = destination.getParentFile();
                if ((!parent.exists() && !parent.mkdirs()) || destination.exists())
                    throw new SecurityException("Cannot safely create isolated module");
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                long remaining = entry.getLong("size");
                try (InputStream input = context.getAssets().open(entry.getString("asset"));
                     FileOutputStream output = new FileOutputStream(destination)) {
                    while (remaining > 0) {
                        int n = input.read(buffer, 0, (int)Math.min((long)buffer.length, remaining));
                        if (n < 0) throw new SecurityException("Incomplete staged asset");
                        if (n == 0) continue;
                        output.write(buffer, 0, n);
                        digest.update(buffer, 0, n);
                        remaining -= n;
                    }
                    if (input.read() != -1)
                        throw new SecurityException("Staged asset exceeds declared size");
                    output.getFD().sync();
                }
                if (!entry.getString("sha256").equals(hex(digest.digest())))
                    throw new SecurityException("Module SHA-256 mismatch; pending data remains quarantined");
            }
            verifyFiles(pending, entries);
            if (!pending.renameTo(complete))
                throw new SecurityException("Cannot atomically mark complete staging");
            verifyFiles(complete, entries);
            report.append("PE components: 19/19 staged and verified\n");
            report.append("Wine NLS tables: 76/76 staged and verified\n");
            report.append("No executable bit or launch capability granted\n");
            report.append("RESULT: PASS — isolated source-built data staged; NOT runnable\n");
        } catch (Exception error) {
            report.append("RESULT: BLOCKED — ").append(error.getClass().getSimpleName()).append("\n");
            report.append("Incomplete staging (if present) left quarantined; existing data untouched\n");
        }
        return report.toString();
    }
}

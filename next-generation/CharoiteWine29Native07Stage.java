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
 * Explicit-consent, hash-verified Wine29 .0.7 Windows PE/NLS DATA ONLY stage.
 *
 * Writes exclusively into a NEW private no_backup directory not shared with
 * Wine28, Wine26, user prefixes, games, saves or rootfs. Does NOT run Wine,
 * wineserver, Wineboot, PE/Windows programs, FEX, graphics or games.
 *
 * Atomic fresh slot: .pending -> final. NEVER delete/overwrite partial data.
 * Existing complete slot is only rehashed; a failed pending slot is quarantined.
 */
public final class CharoiteWine29Native07Stage {
    private static final String PACKAGE = "com.charoitx";
    private static final String VERSION = "wine10-arm64ec-bootstrap.0.7";
    private static final String SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767";
    private static final String ARCHIVE_SHA =
        "66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e";
    private static final long SOURCE_RUN = 41749167248L;
    private static final long SOURCE_ARTIFACT = 13284932342L;
    private static final String INDEX = "charoite-next/wine29-native07/wine29-native07-index.json";
    private static final String ASSET_ROOT = "charoite-next/wine29-native07/modules/";
    private static final String ROOT = "charoite-next-wine29-07-pe-nls";
    private static final String FINAL = "wine10-arm64ec-bootstrap-0.7-pe-nls";
    private static final String PENDING = ".wine10-arm64ec-bootstrap-0.7-pe-nls-pending";
    private static final long MAX_FILE = 32L * 1024L * 1024L;
    private static final long MAX_TOTAL = 128L * 1024L * 1024L;
    private static final int MAX_JSON = 65536;
    private CharoiteWine29Native07Stage() {}

    private static String hex(byte[] digest) {
        StringBuilder out = new StringBuilder();
        for (byte b : digest)
            out.append(String.format(Locale.US, "%02x", b & 255));
        return out.toString();
    }

    private static JSONObject readIndex(Context context) throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (InputStream input = context.getAssets().open(INDEX)) {
            byte[] buf = new byte[2048];
            int count;
            while ((count = input.read(buf)) != -1) {
                if (bytes.size() + count > MAX_JSON)
                    throw new SecurityException("Oversized Wine29 module index");
                bytes.write(buf, 0, count);
            }
        }
        return new JSONObject(bytes.toString("UTF-8"));
    }

    private static String approvedPath(String path) {
        if (!(path.matches("pe/arm64ec/[a-z0-9_]+\\.dll") ||
              path.equals("pe/arm64/wineboot.exe") ||
              path.matches("nls/[a-z0-9_]+\\.nls")))
            throw new SecurityException("Invalid Wine29 isolated module path");
        return path;
    }

    /** Fail-closed metadata and explicit APK-owned PE/NLS allowlist. */
    private static JSONArray inventory(Context context, JSONObject index) throws Exception {
        if (!PACKAGE.equals(context.getPackageName()) ||
            index.getInt("schema_version") != 1 ||
            !PACKAGE.equals(index.getString("package")) ||
            !SOURCE.equals(index.getString("wine_source_commit")) ||
            !VERSION.equals(index.getString("bundle_version")) ||
            SOURCE_RUN != index.getLong("source_run") ||
            SOURCE_ARTIFACT != index.getLong("source_artifact") ||
            !ARCHIVE_SHA.equals(index.getString("archive_sha256")) ||
            !index.getBoolean("module_assets_verified") ||
            index.getBoolean("module_staged_on_phone") ||
            index.getBoolean("wine29_pe_nls_runnable") ||
            index.getInt("component_count") != 27 ||
            index.getInt("pe_count") != 24 ||
            index.getInt("nls_count") != 76 ||
            index.getInt("module_count") != 100 ||
            index.getInt("native_elf_count") != 3 ||
            index.getBoolean("native_elf_executed") ||
            index.getBoolean("wineboot_executed") ||
            index.getBoolean("windows_exe_executed") ||
            index.getBoolean("launch_ready") ||
            index.getBoolean("installable_as_runtime") ||
            index.getBoolean("prefix_created") ||
            index.getBoolean("device_tested") ||
            index.getBoolean("anti_cheat_supported"))
            throw new SecurityException("Untrusted Wine29 0.7 data-only source inventory");
        JSONArray files = index.getJSONArray("module_files");
        if (files.length() != 100)
            throw new SecurityException("Wine29 source module count mismatch");
        long total = 0;
        int pe = 0;
        int nls = 0;
        String prior = "";
        HashSet<String> seen = new HashSet<>();
        for (int i = 0; i < files.length(); i++) {
            JSONObject rec = files.getJSONObject(i);
            String name = approvedPath(rec.getString("path"));
            String asset = ASSET_ROOT + name.replace('/', '_') + ".bin";
            if (name.compareTo(prior) <= 0 ||
                !("runtime/" + name).equals(rec.getString("source")) ||
                !asset.equals(rec.getString("asset")) ||
                !seen.add(asset) ||
                !rec.getString("sha256").matches("[0-9a-f]{64}"))
                throw new SecurityException("Incorrect sorted Wine29 source asset allowlist");
            long size = rec.getLong("size");
            if (size <= 0 || size > MAX_FILE)
                throw new SecurityException("Wine29 PE/NLS file exceeds safe size");
            total += size;
            if (name.startsWith("nls/")) nls++; else pe++;
            prior = name;
        }
        if (nls != 76 || pe != 24 ||
            !seen.contains(ASSET_ROOT + "pe_arm64ec_apisetschema.dll.bin") ||
            !seen.contains(ASSET_ROOT + "pe_arm64_wineboot.exe.bin") ||
            total <= 0 || total > MAX_TOTAL ||
            index.getLong("modules_total_bytes") != total)
            throw new SecurityException("Wine29 PE/NLS total, API-set, or wineboot missing");
        return files;
    }

    private static File inside(File root, String relative) throws Exception {
        File file = new File(root, relative);
        File parent = root.getCanonicalFile();
        File canonical = file.getCanonicalFile();
        if (canonical.equals(parent) ||
            !canonical.toPath().startsWith(parent.toPath()) ||
            !canonical.equals(file.getAbsoluteFile()))
            throw new SecurityException("Wine29 file would escape new isolated slot");
        return file;
    }

    private static String hash(InputStream input, long size) throws Exception {
        if (size <= 0 || size > MAX_FILE)
            throw new SecurityException("Wine29 individual hash outside safe bound");
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        long remaining = size;
        byte[] buffer = new byte[32768];
        try (InputStream stream = input) {
            while (remaining > 0) {
                int count = stream.read(buffer, 0, (int)Math.min((long)buffer.length, remaining));
                if (count <= 0) throw new SecurityException("Short Wine29 PE/NLS module");
                md.update(buffer, 0, count);
                remaining -= count;
            }
            if (stream.read() != -1)
                throw new SecurityException("Trailing unverified Wine29 module bytes");
        }
        return hex(md.digest());
    }

    /** Verify ALL 100 APK assets before creating any on-device directory. */
    private static void verifyAssets(Context context, JSONArray entries) throws Exception {
        for (int i = 0; i < entries.length(); i++) {
            JSONObject entry = entries.getJSONObject(i);
            String actual = hash(context.getAssets().open(entry.getString("asset")),
                                 entry.getLong("size"));
            if (!entry.getString("sha256").equals(actual))
                throw new SecurityException("Wine29 APK asset digest mismatch: " +
                                            entry.getString("path"));
        }
    }

    /**
     * Sealed DATA-only slot: reject extra modules, directories, links and
     * unexpected files before accepting the 100 source-approved hashes.
     * Never follow an unapproved directory into any other app data.
     */
    private static void verifyClosedInventory(File slot, JSONArray entries) throws Exception {
        HashSet<String> expected = new HashSet<>();
        for (int i = 0; i < entries.length(); i++)
            expected.add(entries.getJSONObject(i).getString("path"));
        HashSet<String> directories = new HashSet<>();
        directories.add("pe");
        directories.add("pe/arm64ec");
        directories.add("pe/arm64");
        directories.add("nls");
        HashSet<String> observed = new HashSet<>();
        java.util.ArrayDeque<File> queue = new java.util.ArrayDeque<>();
        queue.add(slot);
        int nodes = 0;
        while (!queue.isEmpty()) {
            File dir = queue.removeFirst();
            File[] children = dir.listFiles();
            if (children == null) throw new SecurityException("Unreadable Wine29 staging directory");
            for (File child : children) {
                if (++nodes > 104 ||
                    !child.getCanonicalFile().equals(child.getAbsoluteFile()))
                    throw new SecurityException("Unexpected or linked Wine29 staging entry");
                String relative = slot.toPath().relativize(child.toPath())
                    .toString().replace(File.separatorChar, '/');
                if (child.isDirectory()) {
                    if (!directories.contains(relative))
                        throw new SecurityException("Unknown Wine29 staging directory");
                    queue.add(child);
                } else if (child.isFile()) {
                    if (!expected.contains(relative) || !observed.add(relative))
                        throw new SecurityException("Unexpected Wine29 staging file");
                } else {
                    throw new SecurityException("Unsupported Wine29 staging file type");
                }
            }
        }
        if (observed.size() != entries.length())
            throw new SecurityException("Incomplete Wine29 sealed 100-module inventory");
    }

    /** Only the expected final slot may exist for a read-only, sealed audit. */
    private static void verifyRootContents(File root) throws Exception {
        File[] children = root.listFiles();
        if (children == null) throw new SecurityException("Unreadable Wine29 private root");
        for (File child : children) {
            if (!FINAL.equals(child.getName()) ||
                !child.getCanonicalFile().equals(child.getAbsoluteFile()) ||
                !child.isDirectory())
                throw new SecurityException("Unexpected or quarantined Wine29 root entry");
        }
    }

    private static void verifyFiles(File slot, JSONArray entries) throws Exception {
        if (!slot.isDirectory() ||
            !slot.getCanonicalFile().equals(slot.getAbsoluteFile()))
            throw new SecurityException("Wine29 final data-only slot absent or unsafe");
        verifyClosedInventory(slot, entries);
        for (int i = 0; i < entries.length(); i++) {
            JSONObject entry = entries.getJSONObject(i);
            File target = inside(slot, entry.getString("path"));
            if (!target.isFile() || target.length() != entry.getLong("size") ||
                !entry.getString("sha256").equals(
                    hash(new FileInputStream(target), entry.getLong("size"))))
                throw new SecurityException("Wine29 staged module hash mismatch: " +
                                            entry.getString("path"));
        }
    }

    private static File privateRoot(Context context) throws Exception {
        File base = context.getNoBackupFilesDir().getCanonicalFile();
        File target = new File(base, ROOT);
        if (!target.getCanonicalFile().getParentFile().equals(base) ||
            (target.exists() && !target.getCanonicalFile().equals(target.getAbsoluteFile())))
            throw new SecurityException("Wine29 private staging root not isolated");
        return target;
    }

    public static String verifyOnly(Context context) {
        StringBuilder out = new StringBuilder();
        out.append("CHAROITE NEXT — WINE29 .0.7 PRIVATE PE/NLS READ-ONLY VERIFY\n");
        out.append("Wine28 experiments, prefixes, games and saves: NOT ACCESSED\n");
        try {
            String audit = CharoiteWine29Native07Audit.run(context);
            if (!audit.contains(
                "RESULT: PASS — APK-owned Wine29 0.7 source and native hashes verified; NOT RUNNABLE"))
                throw new SecurityException("Prior Wine29 APK audit did not pass");
            JSONArray entries = inventory(context, readIndex(context));
            verifyAssets(context, entries);
            File root = privateRoot(context);
            if (!root.isDirectory())
                throw new SecurityException("New Wine29 data slot not previously staged");
            File pending = inside(root, PENDING);
            if (pending.exists()) throw new SecurityException("Quarantined pending slot present");
            verifyRootContents(root);
            verifyFiles(inside(root, FINAL), entries);
            out.append("Windows PE: 24/24 SHA-256 PASS\n");
            out.append("Wine NLS: 76/76 SHA-256 PASS\n");
            out.append("APK source assets and sealed 100-file private inventory: SHA-256 PASS\n");
            out.append("Native Wine/PE/Wineboot execution: NOT ATTEMPTED\n");
            out.append("RESULT: PASS — isolated Wine29 0.7 data-only stage; NOT RUNNABLE\n");
        } catch (Exception error) {
            out.append("RESULT: BLOCKED — ").append(error.getClass().getSimpleName())
               .append(": ").append(error.getMessage()).append('\n');
        }
        return out.toString();
    }

    /** Explicit UI consent required; no automatic run or files outside ROOT. */
    public static String run(Context context) {
        StringBuilder out = new StringBuilder();
        out.append("CHAROITE NEXT — ISOLATED WINE29 .0.7 PE/NLS DATA STAGING\n");
        out.append("Creates a NEW separate private source-hash-verified data slot only\n");
        out.append("Old Wine28 v1–v9, prefixes, games, saves, rootfs: NOT ACCESSED\n");
        out.append("Wine, wineserver, Wineboot, Windows EXE, FEX, graphics: NOT EXECUTED\n\n");
        try {
            String audit = CharoiteWine29Native07Audit.run(context);
            if (!audit.contains(
                "RESULT: PASS — APK-owned Wine29 0.7 source and native hashes verified; NOT RUNNABLE"))
                throw new SecurityException("Prerequisite Wine29 source archive audit failed");
            JSONArray entries = inventory(context, readIndex(context));
            // In particular, do not touch private storage until all APK source hashes pass.
            verifyAssets(context, entries);
            File root = privateRoot(context);
            File pending = inside(root, PENDING);
            File complete = inside(root, FINAL);
            if (pending.exists())
                throw new SecurityException("Partial Wine29 pending slot quarantined; NO retry");
            if (complete.exists()) {
                verifyRootContents(root);
                verifyFiles(complete, entries);
                out.append("Existing Wine29 data slot reverified, no writes\n");
                out.append("RESULT: PASS — existing Wine29 .0.7 data; NOT RUNNABLE\n");
                return out.toString();
            }
            if (root.exists()) {
                File[] existing = root.listFiles();
                if (existing == null || existing.length != 0)
                    throw new SecurityException("Refusing nonempty Wine29 private root");
            }
            if (!root.exists() && !root.mkdir())
                throw new SecurityException("Failed to create new Wine29 private root");
            if (!pending.mkdir())
                throw new SecurityException("Failed to create Wine29 pending slot");
            byte[] buffer = new byte[32768];
            for (int i = 0; i < entries.length(); i++) {
                JSONObject entry = entries.getJSONObject(i);
                String path = entry.getString("path");
                File target = inside(pending, path);
                File parent = target.getParentFile();
                if ((!parent.exists() && !parent.mkdirs()) || target.exists())
                    throw new SecurityException("Refusing pre-existing Wine29 module file");
                long remaining = entry.getLong("size");
                MessageDigest md = MessageDigest.getInstance("SHA-256");
                try (InputStream input = context.getAssets().open(entry.getString("asset"));
                     FileOutputStream output = new FileOutputStream(target)) {
                    while (remaining > 0) {
                        int count = input.read(buffer, 0, (int)Math.min((long)buffer.length,remaining));
                        if (count <= 0) throw new SecurityException("Short Wine29 source asset");
                        output.write(buffer, 0, count);
                        md.update(buffer, 0, count);
                        remaining -= count;
                    }
                    if (input.read() != -1) throw new SecurityException("Trailing Wine29 asset bytes");
                    output.getFD().sync();
                }
                if (!entry.getString("sha256").equals(hex(md.digest())))
                    throw new SecurityException("Wine29 module SHA-256 mismatch during copy");
            }
            verifyFiles(pending, entries);
            if (!pending.renameTo(complete))
                throw new SecurityException("Cannot atomically finalize new Wine29 slot");
            verifyFiles(complete, entries);
            out.append("Windows PE: 24/24 source hashes PASS\n");
            out.append("Wine NLS: 76/76 source hashes PASS\n");
            verifyRootContents(root);
            out.append("Sealed 100-file inventory with no extra files: PASS\n");
            out.append("Separate new private slot: ").append(FINAL).append('\n');
            out.append("Native Wine/PE/Wineboot execution: NOT ATTEMPTED\n");
            out.append("RESULT: PASS — Wine29 0.7 data staged; NOT RUNNABLE\n");
        } catch (Exception error) {
            out.append("RESULT: BLOCKED — ")
               .append(error.getClass().getSimpleName())
               .append(": ").append(error.getMessage()).append('\n');
            out.append("Any incomplete pending data remains quarantined; no existing slot deleted\n");
        }
        return out.toString();
    }
}

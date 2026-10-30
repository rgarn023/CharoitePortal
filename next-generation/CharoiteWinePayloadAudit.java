package com.charoitegames.core;

import android.content.Context;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.Locale;
import org.json.JSONObject;

/**
 * User-initiated immutable APK payload integrity check. No extraction, execution,
 * filesystem writes, Wine prefix access or game data access.
 */
public final class CharoiteWinePayloadAudit {
    private static final String PACKAGE = "com.charoitx";
    private static final String INDEX = "charoite-next/wine-bootstrap-payload.json";
    private static final String ASSET = "charoite-next/wine-bootstrap-22.tar.gz";
    private static final String WINE_SHA = "c74acb09d51b447f5d5ac56c87608d3ec565a767";
    private static final long SOURCE_RUN = 40898982875L;
    private static final long MAX_BYTES = 64L * 1024L * 1024L;
    private CharoiteWinePayloadAudit() {}

    private static String hex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte b : bytes) result.append(String.format(Locale.US, "%02x", b & 255));
        return result.toString();
    }

    private static String index(Context context) throws Exception {
        try (InputStream input = context.getAssets().open(INDEX)) {
            java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
            byte[] chunk = new byte[1024];
            int n;
            while ((n = input.read(chunk)) != -1) {
                if (out.size() + n > 8192) throw new SecurityException("Oversize payload manifest");
                out.write(chunk, 0, n);
            }
            return out.toString("UTF-8");
        }
    }

    public static String report(Context context) {
        StringBuilder out = new StringBuilder();
        out.append("CHAROITE NEXT — COHERENT WINE MODULE PAYLOAD\n");
        out.append("Scope: APK-owned archive verification, READ ONLY\n");
        out.append("Prefix, games, and saved data: NOT ACCESSED\n");
        out.append("No modules extracted or executed.\n");
        if (!PACKAGE.equals(context.getPackageName()))
            return out.append("RESULT: BLOCKED — wrong Android package\n").toString();
        try {
            JSONObject info = new JSONObject(index(context));
            if (info.getInt("schema_version") != 1
                    || !PACKAGE.equals(info.getString("android_package"))
                    || !WINE_SHA.equals(info.getString("wine_source_sha"))
                    || info.getLong("source_run") != SOURCE_RUN
                    || info.getLong("source_artifact") != 12908731604L
                    || !ASSET.equals(info.getString("archive_asset"))
                    || info.getInt("component_count") != 22
                    || info.getInt("pe_component_count") != 19
                    || info.getInt("native_component_count") != 3
                    || info.getInt("nls_count") != 76
                    || info.getInt("windows_imports_not_bundled_count") < 0
                    || !info.getString("bundle_manifest_sha256").matches("[0-9a-f]{64}")
                    || !info.getString("dependency_review_sha256").matches("[0-9a-f]{64}")
                    || info.getBoolean("launch_ready")
                    || info.getBoolean("installable_as_runtime")
                    || info.getBoolean("archive_extracted")
                    || info.getBoolean("prefix_created")
                    || info.getBoolean("fex_installed")
                    || info.getBoolean("graphics_verified")
                    || info.getBoolean("device_boot_tested")
                    || info.getBoolean("anti_cheat_supported"))
                throw new SecurityException("Unsafe or untrusted runtime metadata");
            long expectedSize = info.getLong("archive_size");
            String expectedHash = info.getString("archive_sha256");
            if (expectedSize < 1L || expectedSize > MAX_BYTES
                    || !expectedHash.matches("[0-9a-f]{64}"))
                throw new SecurityException("Invalid archive hash/size");
            MessageDigest hash = MessageDigest.getInstance("SHA-256");
            long count = 0;
            try (InputStream input = context.getAssets().open(ASSET)) {
                byte[] buf = new byte[32768];
                int n;
                while ((n = input.read(buf)) != -1) {
                    count += n;
                    if (count > expectedSize || count > MAX_BYTES)
                        throw new SecurityException("Archive exceeds expected size");
                    hash.update(buf, 0, n);
                }
            }
            if (count != expectedSize || !expectedHash.equals(hex(hash.digest())))
                throw new SecurityException("APK Wine archive does not match audited source");
            out.append("Source-built Wine components: 22/22\n");
            out.append("Windows PE components: 19\n");
            out.append("Native ELF components: 3\n");
            out.append("Wine NLS tables: 76\n");
            out.append("Archive SHA-256: PASS\n");
            out.append("Observed PE import gaps: ")
                    .append(info.getInt("windows_imports_not_bundled_count")).append("\n");
            out.append("FEX, graphics, fresh prefix: NOT READY\n");
            out.append("Modern Wine runtime: NOT INSTALLED; launch blocked\n");
            out.append("RESULT: PASS — immutable APK payload verified; NOT runnable\n");
        } catch (Exception error) {
            out.append("RESULT: BLOCKED — ").append(error.getClass().getSimpleName()).append("\n");
        }
        return out.toString();
    }
}

package com.charoitegames.core;

import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.StatFs;
import android.system.Os;
import android.system.OsConstants;
import org.json.JSONObject;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.Iterator;
import java.util.Locale;

/**
 * Safe read-only diagnostic of the actual phone and CI-compiled Wine PE assets.
 * This class NEVER loads a PE DLL, starts Wine, creates a prefix or installs a runner.
 */
public final class CharoiteNextDiagnostics {
    private static final String EVIDENCE = "charoite-next/wine-ci/wine-ci-evidence.json";
    private static final String NEXT_PACKAGE = "com.charoitx";
    private static final int PE_ARM64_CARRIER = 0xAA64;

    private CharoiteNextDiagnostics() {}

    private static String hex(byte[] data) {
        StringBuilder out = new StringBuilder(data.length * 2);
        for (byte b : data) out.append(String.format(Locale.US, "%02x", b & 0xff));
        return out.toString();
    }

    private static String verifyAsset(Context context, String asset, String expectedHash,
                                      long expectedSize) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] first = new byte[128];
        int collected = 0;
        long size = 0;
        try (InputStream in = context.getAssets().open(asset)) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = in.read(buffer)) != -1) {
                digest.update(buffer, 0, count);
                if (collected < first.length) {
                    int take = Math.min(count, first.length - collected);
                    System.arraycopy(buffer, 0, first, collected, take);
                    collected += take;
                }
                size += count;
            }
        }
        if (size != expectedSize || !hex(digest.digest()).equals(expectedHash))
            throw new IllegalStateException("File size or SHA-256 mismatch");
        if (collected < 64 || first[0] != 'M' || first[1] != 'Z')
            throw new IllegalStateException("PE DOS signature missing");
        int offset = (first[0x3c] & 255) | ((first[0x3d] & 255) << 8)
                | ((first[0x3e] & 255) << 16) | ((first[0x3f] & 255) << 24);
        // Most PE files have a header offset beyond 128 bytes; read the header separately.
        try (InputStream in = context.getAssets().open(asset)) {
            long skipped = 0;
            while (skipped < offset) {
                long delta = in.skip(offset - skipped);
                if (delta <= 0) throw new IllegalStateException("Invalid PE header offset");
                skipped += delta;
            }
            byte[] header = new byte[6];
            int done = 0;
            while (done < 6) {
                int n = in.read(header, done, 6 - done);
                if (n < 0) throw new IllegalStateException("Missing PE header");
                done += n;
            }
            if (header[0] != 'P' || header[1] != 'E' || header[2] != 0 || header[3] != 0)
                throw new IllegalStateException("PE header invalid");
            int machine = (header[4] & 255) | ((header[5] & 255) << 8);
            if (machine != PE_ARM64_CARRIER)
                throw new IllegalStateException("PE carrier is not ARM64 (0xAA64)");
        }
        return "SHA-256 + ARM64 PE carrier verified";
    }

    public static String deviceReport(Context context) {
        StringBuilder report = new StringBuilder();
        report.append("CHAROITE NEXT — DEVICE SMOKE CHECK\n");
        report.append("Package: ").append(context.getPackageName()).append("\n");
        report.append("App isolation: ").append(NEXT_PACKAGE.equals(context.getPackageName())
                ? "PASS" : "FAIL (unexpected package)").append("\n");
        report.append("Android API: ").append(Build.VERSION.SDK_INT).append("\n");
        report.append("Device: ").append(Build.MANUFACTURER).append(" ")
                .append(Build.MODEL).append("\n");
        report.append("64-bit ABIs: ").append(java.util.Arrays.toString(Build.SUPPORTED_64_BIT_ABIS))
                .append("\n");
        try {
            long pageSize = Os.sysconf(OsConstants._SC_PAGESIZE);
            report.append("Kernel page size: ").append(pageSize).append(" bytes\n");
        } catch (Exception error) {
            report.append("Kernel page size: unknown (").append(error.getClass().getSimpleName())
                    .append(")\n");
        }
        PackageManager pm = context.getPackageManager();
        report.append("Vulkan exposed by Android: ")
                .append(pm.hasSystemFeature("android.hardware.vulkan.version") ? "YES" : "NO")
                .append(" (not a DXVK or Vulkan driver test)\n");
        report.append("Private data free: ")
                .append(context.getFilesDir().getUsableSpace() / (1024 * 1024))
                .append(" MiB\n");
        report.append("\nCI WINE PE ASSET INTEGRITY\n");
        try {
            StringBuilder evidenceText = new StringBuilder();
            try (InputStream in = context.getAssets().open(EVIDENCE)) {
                byte[] buf = new byte[4096];
                int n;
                while ((n = in.read(buf)) != -1)
                    evidenceText.append(new String(buf, 0, n, java.nio.charset.StandardCharsets.UTF_8));
            }
            JSONObject evidence = new JSONObject(evidenceText.toString());
            if (!NEXT_PACKAGE.equals(evidence.getString("android_package"))
                    || evidence.getBoolean("launch_ready")
                    || evidence.getBoolean("installable_as_runtime")
                    || evidence.getBoolean("prefix_created")
                    || evidence.getBoolean("device_tested")
                    || evidence.getBoolean("anti_cheat_supported")
                    || evidence.getInt("source_run") != 40791083178)
                throw new IllegalStateException("Unsupported runtime readiness or provenance claims");
            JSONObject components = evidence.getJSONObject("components");
            if (components.length() != 7) throw new IllegalStateException("Expected seven DLLs");
            int verified = 0;
            Iterator<String> keys = components.keys();
            while (keys.hasNext()) {
                String name = keys.next();
                JSONObject entry = components.getJSONObject(name);
                String path = entry.getString("asset");
                if (!path.startsWith("charoite-next/wine-ci/")
                        || path.indexOf("..") >= 0
                        || !entry.getBoolean("arm64ec_ci_verified"))
                    throw new IllegalStateException("Invalid asset path/provenance");
                verifyAsset(context, path, entry.getString("sha256"), entry.getLong("size"));
                report.append(name).append(": PASS\n");
                verified++;
            }
            report.append("Compiled PE DLLs checked: ").append(verified)
                    .append("/7 — PASS\n");
        } catch (Exception e) {
            report.append("PE assets: FAIL — ").append(e.getClass().getSimpleName())
                    .append(": ").append(e.getMessage()).append("\n");
        }
        report.append("\nMODERN ENGINE: NOT READY\n");
        report.append("This diagnostic does NOT load Wine, run Windows executables, "
                + "create a prefix, verify FEX, or prove Battle.net/Steam or anti-cheat support.\n");
        return report.toString();
    }
}

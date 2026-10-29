package com.charoitegames.core;

import android.content.Context;
import android.os.Build;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Read-only, user-initiated smoke test for a verified same-source Android
 * AArch64 wineserver ELF. Does NOT start a server session or any Wine prefix.
 * Only executes APK PackageManager-extracted native code with --version.
 */
public final class CharoiteWineServerProbe {
    private static final String PACKAGE = "com.charoitx";
    private static final String MANIFEST = "charoite-next/wine-native-probe.json";
    private static final String SERVER = "libcharoite_wineserver.so";
    private static final String SOURCE_SHA = "5d07e29fdba6552033d5f1a1a50ff1cc2fffe420";
    private static final long SOURCE_RUN = 40898982875L;
    private CharoiteWineServerProbe() {}

    private static String hash(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream input = new java.io.FileInputStream(file)) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = input.read(buf)) != -1) digest.update(buf, 0, n);
        }
        StringBuilder result = new StringBuilder();
        for (byte b : digest.digest())
            result.append(String.format(Locale.US, "%02x", b & 255));
        return result.toString();
    }

    private static String asset(Context context) throws Exception {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        try (InputStream input = context.getAssets().open(MANIFEST)) {
            byte[] chunk = new byte[2048];
            int n;
            while ((n = input.read(chunk)) != -1) {
                if (output.size() + n > 16384)
                    throw new SecurityException("Manifest exceeds permitted size");
                output.write(chunk, 0, n);
            }
        }
        return output.toString("UTF-8");
    }

    public static String run(Context context) {
        StringBuilder report = new StringBuilder();
        report.append("CHAROITE NEXT — SOURCE-BUILT WINESERVER VERSION PROBE\n");
        report.append("Scope: APK-installed Android AArch64 wineserver, --version only\n");
        report.append("Package: ").append(context.getPackageName()).append('\n');
        report.append("Wineserver session: NOT STARTED\n");
        report.append("Wine prefix/wineboot: NOT ATTEMPTED\n");
        report.append("Windows EXE, games, FEX and graphics: NOT TESTED\n");
        report.append("Existing game/save/prefix data: NOT ACCESSED\n\n");
        if (!PACKAGE.equals(context.getPackageName()) || Build.VERSION.SDK_INT < 26)
            return report.append("RESULT: BLOCKED — unsupported package/Android API\n").toString();

        Process process = null;
        try {
            JSONObject evidence = new JSONObject(asset(context));
            if (evidence.getInt("schema_version") != 1
                    || !PACKAGE.equals(evidence.getString("android_package"))
                    || evidence.getLong("source_run") != SOURCE_RUN
                    || !SOURCE_SHA.equals(evidence.getString("source_code_sha"))
                    || !SERVER.equals(evidence.getString("wineserver_native_library_filename"))
                    || !"--version".equals(evidence.getString("wineserver_version_arg"))
                    || evidence.getBoolean("wineserver_device_tested")
                    || evidence.getBoolean("launch_ready")
                    || evidence.getBoolean("installable_as_runtime")
                    || evidence.getBoolean("prefix_created")
                    || evidence.getBoolean("anti_cheat_supported")) {
                throw new SecurityException("Unexpected Wine server provenance/readiness");
            }
            File nativeDir = new File(context.getApplicationInfo().nativeLibraryDir)
                    .getCanonicalFile();
            File server = new File(nativeDir, SERVER).getCanonicalFile();
            if (!nativeDir.equals(server.getParentFile())
                    || !server.isFile()
                    || server.length() != evidence.getLong("wineserver_size")
                    || !hash(server).equals(evidence.getString("wineserver_sha256"))) {
                throw new SecurityException("APK native wineserver differs from audited build");
            }
            report.append("Wineserver native ELF hash: PASS\n");
            report.append("Wineserver source build: ").append(SOURCE_RUN).append('\n');
            report.append("Execution path: verified APK-owned native library directory\n");
            ProcessBuilder builder = new ProcessBuilder(server.getAbsolutePath(), "--version");
            builder.redirectErrorStream(true);
            Map<String, String> env = builder.environment();
            env.clear(); // never inherit game/home/prefix paths, credentials or overrides
            env.put("PATH", "/system/bin:/system/xbin");
            env.put("WINEDEBUG", "-all");
            process = builder.start();
            boolean ended = process.waitFor(7, TimeUnit.SECONDS);
            if (!ended) {
                process.destroyForcibly();
                process.waitFor(2, TimeUnit.SECONDS);
                report.append("RESULT: TIMEOUT — wineserver --version did not exit\n");
                return report.toString();
            }
            int exit = process.exitValue();
            ByteArrayOutputStream collected = new ByteArrayOutputStream();
            try (InputStream stream = process.getInputStream()) {
                byte[] chunk = new byte[512];
                int n;
                while ((n = stream.read(chunk)) != -1 && collected.size() < 4096)
                    collected.write(chunk, 0, Math.min(n, 4096-collected.size()));
            }
            String output = collected.toString("UTF-8").trim();
            report.append("Native exit code: ").append(exit).append('\n');
            report.append("Output: ").append(output.isEmpty() ? "(empty)" : output).append('\n');
            if (exit == 0 && output.toLowerCase(Locale.US).contains("wine"))
                report.append("RESULT: PASS — Android wineserver --version executed\n");
            else
                report.append("RESULT: FAIL — wineserver --version did not pass\n");
        } catch (Exception error) {
            report.append("RESULT: FAIL — ").append(error.getClass().getSimpleName())
                    .append(": ").append(error.getMessage()).append('\n');
        } finally {
            if (process != null && process.isAlive()) process.destroyForcibly();
        }
        report.append("Modern gaming engine: NOT READY; no prefix/session executed.\n");
        return report.toString();
    }
}

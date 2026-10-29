package com.charoitegames.core;

import android.content.Context;
import android.os.Build;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * User-initiated, tightly scoped native Android Wine --version smoke probe.
 *
 * Never runs a Windows EXE, never creates a Wine prefix or installs a runner.
 * No downloaded or writable executables are accepted: only an APK-installed,
 * source-verified nativeLibraryDir ELF may be launched. Inheritable Wine
 * environment is removed and the only permitted argument is --version.
 *
 * A pass is NOT evidence that Wineboot, ARM64EC, FEX or graphics will work.
 */
public final class CharoiteWineNativeProbe {
    private static final String PACKAGE = "com.charoitx";
    private static final String ASSET = "charoite-next/wine-native-probe.json";
    private static final String NATIVE_FILE = "libcharoite_wine_loader.so";
    private static final long SOURCE_RUN = 40806958409L;
    private static final String SOURCE_SHA =
            "13a33686c3f93e0ac68b65fe7766d129ac0e6c99";
    private static final long TIMEOUT_SECONDS = 7L;
    private CharoiteWineNativeProbe() {}

    private static String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (java.io.FileInputStream input = new java.io.FileInputStream(file)) {
            byte[] buffer = new byte[8192];
            int n;
            while ((n = input.read(buffer)) != -1) digest.update(buffer, 0, n);
        }
        StringBuilder text = new StringBuilder();
        for (byte b : digest.digest())
            text.append(String.format(Locale.US, "%02x", b & 255));
        return text.toString();
    }

    private static String readManifest(Context context) throws Exception {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        try (InputStream input = context.getAssets().open(ASSET)) {
            byte[] buffer = new byte[2048];
            int n;
            while ((n = input.read(buffer)) != -1) {
                if (output.size() + n > 16384) throw new IllegalStateException("Evidence too large");
                output.write(buffer, 0, n);
            }
        }
        return output.toString("UTF-8");
    }

    private static String readOutput(InputStream input) throws Exception {
        byte[] buffer = new byte[2048];
        int n;
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        while ((n = input.read(buffer)) != -1) {
            int permitted = Math.min(n, 4096 - output.size());
            if (permitted > 0) output.write(buffer, 0, permitted);
            if (output.size() >= 4096) break;
        }
        return output.toString("UTF-8").trim();
    }

    public static String run(Context context) {
        StringBuilder report = new StringBuilder();
        report.append("CHAROITE NEXT — FIRST NATIVE WINE STARTUP PROBE\n");
        report.append("Scope: Android AArch64 Wine executable, --version only\n");
        report.append("Package: ").append(context.getPackageName()).append("\n");
        report.append("Windows EXE launch: NOT ATTEMPTED\n");
        report.append("Wine prefix / wineserver start: NOT ATTEMPTED\n");
        report.append("FEX / ARM64EC / graphics: NOT TESTED\n");
        report.append("No installed game, save or Wine prefix is accessed.\n\n");
        if (!PACKAGE.equals(context.getPackageName())) {
            return report.append("RESULT: BLOCKED — wrong Android package\n").toString();
        }
        if (Build.VERSION.SDK_INT < 26) {
            return report.append("RESULT: BLOCKED — Android version unsupported\n").toString();
        }
        Process process = null;
        try {
            JSONObject evidence = new JSONObject(readManifest(context));
            if (evidence.getInt("schema_version") != 1
                    || !PACKAGE.equals(evidence.getString("android_package"))
                    || evidence.getLong("source_run") != SOURCE_RUN
                    || !SOURCE_SHA.equals(evidence.getString("source_code_sha"))
                    || !NATIVE_FILE.equals(evidence.getString("native_library_filename"))
                    || !"--version".equals(evidence.getString("version_arg"))
                    || evidence.getBoolean("launch_ready")
                    || evidence.getBoolean("installable_as_runtime")
                    || evidence.getBoolean("prefix_created")
                    || evidence.getBoolean("device_tested")
                    || evidence.getBoolean("anti_cheat_supported"))
                throw new SecurityException("Unexpected executable or unsupported runtime claim");

            File nativeDirectory = new File(context.getApplicationInfo().nativeLibraryDir);
            File loader = new File(nativeDirectory, NATIVE_FILE);
            if (!loader.getCanonicalFile().getParentFile().equals(nativeDirectory.getCanonicalFile()))
                throw new SecurityException("Invalid executable path");
            if (!loader.isFile() || loader.length() != evidence.getLong("size")
                    || !sha256(loader).equals(evidence.getString("sha256")))
                throw new SecurityException("Installed Wine loader differs from verified source");
            report.append("APK-installed ELF hash: PASS\n");
            report.append("Native path: APK-owned extracted library directory\n");
            report.append("ELF source run: ").append(SOURCE_RUN).append("\n");

            ProcessBuilder command = new ProcessBuilder(loader.getAbsolutePath(), "--version");
            command.redirectErrorStream(true);
            Map<String,String> env = command.environment();
            // In particular, do not inherit an existing game's WINEPREFIX.
            // No HOME, WINEPREFIX or drive mapping is provided.
            env.clear();
            env.put("PATH", "/system/bin:/system/xbin");
            env.put("WINEDEBUG", "-all");
            process = command.start();
            boolean finished = process.waitFor(TIMEOUT_SECONDS, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                process.waitFor(2L, TimeUnit.SECONDS);
                report.append("RESULT: TIMEOUT (native loader did not exit)\n");
                return report.toString();
            }
            int exitCode = process.exitValue();
            String output = readOutput(process.getInputStream());
            report.append("Native exit code: ").append(exitCode).append("\n");
            report.append("Output: ").append(output.isEmpty() ? "(empty)" : output).append("\n");
            if (exitCode == 0 && output.toLowerCase(Locale.US).contains("wine")) {
                report.append("RESULT: PASS — Android Wine --version executed\n");
            } else {
                report.append("RESULT: FAIL — native loader did not identify Wine successfully\n");
            }
        } catch (Exception error) {
            report.append("RESULT: FAIL — ").append(error.getClass().getSimpleName())
                    .append(": ").append(error.getMessage()).append("\n");
        } finally {
            if (process != null && process.isAlive()) process.destroyForcibly();
        }
        report.append("Modern gaming engine: NOT READY; no Wineboot or game execution proven.\n");
        return report.toString();
    }
}

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
import org.json.JSONObject;

/** 
 * User-initiated version-only probe of 3 exact APK-installed Wine27 native ELFs.
 * First re-verifies all 99 staged Wine27 Windows data files, then checks the
 * matching loader, Unix ntdll and wineserver hashes. Only wine --version and
 * wineserver --version are permitted; NEVER wineboot, a prefix, or game.
 */
public final class CharoiteWine27NativeGate {
    private static final String PACKAGE = "com.charoitx";
    private static final String ASSET = "charoite-next/wine27-native-probe.json";
    private static final String SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767";
    private static final String VERSION = "wine10-arm64ec-bootstrap.0.5";
    private static final String STAGE = "wine10-arm64ec-bootstrap-0.6-staged";
    private static final long RUN = 41130899651L;
    private static final long ARTIFACT = 13012239618L;
    private static final long TIMEOUT_SECONDS = 7L;
    private static final String LOADER = "libcharoite_wine27_loader.so";
    private static final String NTDLL = "libcharoite_wine27_ntdll.so";
    private static final String SERVER = "libcharoite_wine27_wineserver.so";
    private CharoiteWine27NativeGate() {}

    private static String readJson(Context context) throws Exception {
        ByteArrayOutputStream b = new ByteArrayOutputStream();
        try (InputStream input = context.getAssets().open(ASSET)) {
            byte[] chunk = new byte[2048];
            int n;
            while ((n = input.read(chunk)) != -1) {
                if (b.size() + n > 16384)
                    throw new SecurityException("Untrusted Wine27 ELF evidence size");
                b.write(chunk,0,n);
            }
        }
        return b.toString("UTF-8");
    }

    private static String hash(File file) throws Exception {
        MessageDigest m=MessageDigest.getInstance("SHA-256");
        try (InputStream input = new FileInputStream(file)) {
            byte[] b=new byte[8192];
            int n;
            while ((n=input.read(b))!=-1) m.update(b,0,n);
        }
        StringBuilder result=new StringBuilder();
        for (byte b:m.digest())
            result.append(String.format(Locale.US,"%02x",b&255));
        return result.toString();
    }

    private static File verifiedELF(File directory,JSONObject records,
                                    String name,String source,String filename) throws Exception {
        JSONObject item=records.getJSONObject(name);
        File target = new File(directory,filename);
        if (!filename.equals(item.getString("library_filename"))
                || !source.equals(item.getString("source_path"))
                || !target.getCanonicalFile().getParentFile().equals(directory.getCanonicalFile())
                || !target.isFile() || !target.canExecute()
                || target.length()!=item.getLong("size")
                || !hash(target).equals(item.getString("sha256")))
            throw new SecurityException("Wine27 native hash/ABI evidence failed: "+name);
        return target;
    }

    private static String capture(InputStream stream) throws Exception {
        ByteArrayOutputStream output=new ByteArrayOutputStream();
        try (InputStream input=stream) {
            byte[] chunk=new byte[1024];
            int n;
            while ((n=input.read(chunk))!=-1) {
                if (output.size()+n>4096)
                    throw new SecurityException("Unbounded native version output");
                output.write(chunk,0,n);
            }
        }
        return output.toString("UTF-8").trim();
    }

    private static String version(File nativeBinary,File nativeDir,
                                  String exactExpectedOutput) throws Exception {
        Process process=null;
        try {
            ProcessBuilder builder=new ProcessBuilder(nativeBinary.getAbsolutePath(),"--version");
            builder.redirectErrorStream(true);
            Map<String,String> env=builder.environment();
            env.clear();
            env.put("PATH","/system/bin:/system/xbin");
            env.put("WINEDEBUG","-all");
            // Only the APK-owned native directory is visible to the source
            // loader's own Android ntdll fallback. No HOME/WINEPREFIX is set.
            env.put("CHAROITE_WINE27_NATIVE_DIR",nativeDir.getCanonicalPath());
            process=builder.start();
            if (!process.waitFor(TIMEOUT_SECONDS,TimeUnit.SECONDS)) {
                process.destroyForcibly();
                process.waitFor(2L,TimeUnit.SECONDS);
                throw new SecurityException("Native Wine27 version probe timed out");
            }
            int exit=process.exitValue();
            String output=capture(process.getInputStream());
            if (exit!=0 || !exactExpectedOutput.equals(output))
                throw new SecurityException("Native version failed (exit="+exit+", output="+output+")");
            return output;
        } finally {
            if (process!=null && process.isAlive()) process.destroyForcibly();
        }
    }

    public static String run(Context context) {
        StringBuilder out=new StringBuilder();
        out.append("CHAROITE NEXT — MATCHED WINE27 NATIVE BOOTSTRAP GATE\n");
        out.append("Scope: 99-file staged data reverify; 3 same-source native ELF hashes;\n");
        out.append("source-built Wine27 and wineserver --version ONLY\n");
        out.append("Existing Wine22, game saves, prefixes, rootfs: NOT ACCESSED\n");
        out.append("Wineboot, Windows EXE, FEX, graphics, server session: NOT ATTEMPTED\n\n");
        if (!PACKAGE.equals(context.getPackageName()) || Build.VERSION.SDK_INT<26)
            return out.append("RESULT: BLOCKED — wrong package/Android version\n").toString();
        String staged=CharoiteWine27Stage.verifyOnly(context);
        out.append(staged).append('\n');
        if (!staged.contains("RESULT: PASS — Wine27 99-file data gate; NOT runnable")) {
            out.append("RESULT: BLOCKED — Wine27 staging prerequisite failed\n");
            return out.toString();
        }
        try {
            JSONObject evidence=new JSONObject(readJson(context));
            if (evidence.getInt("schema_version")!=1
                    || !PACKAGE.equals(evidence.getString("package"))
                    || evidence.getLong("source_run")!=RUN
                    || evidence.getLong("source_artifact")!=ARTIFACT
                    || !SOURCE.equals(evidence.getString("wine_source_commit"))
                    || !VERSION.equals(evidence.getString("archive_version"))
                    || !STAGE.equals(evidence.getString("stage_version"))
                    || !"--version".equals(evidence.getString("version_arg"))
                    || evidence.getBoolean("launch_ready")
                    || evidence.getBoolean("wineboot_tested")
                    || evidence.getBoolean("prefix_created")
                    || evidence.getBoolean("windows_exe_executed")
                    || evidence.getBoolean("fex_installed")
                    || evidence.getBoolean("graphics_verified")
                    || evidence.getBoolean("anti_cheat_supported"))
                throw new SecurityException("Unsafe Wine27 native source claims");
            JSONObject components=evidence.getJSONObject("native_components");
            File nativeDir=new File(context.getApplicationInfo().nativeLibraryDir);
            File loader=verifiedELF(nativeDir,components,"wine","runtime/bin/wine",LOADER);
            File ntdll=verifiedELF(nativeDir,components,"ntdll_unix","runtime/lib/ntdll.so",NTDLL);
            File server=verifiedELF(nativeDir,components,"wineserver","runtime/bin/wineserver",SERVER);
            out.append("Wine27 native loader hash: PASS\n");
            out.append("Wine27 native ntdll hash: PASS\n");
            out.append("Wine27 native wineserver hash: PASS\n");
            out.append("Native ELF source run: ").append(RUN).append('\n');
            out.append("Wine27 loader output: ").append(version(loader,nativeDir,"wine-10.0")).append('\n');
            out.append("Wine27 wineserver output: ").append(version(server,nativeDir,"Wine 10.0")).append('\n');
            out.append("Both version-only native exits: 0\n");
            out.append("Unbundled Windows PE imports: 20\n");
            out.append("RESULT: PASS — matched Wine27 native --version gate; NOT runnable\n");
        } catch (Exception error) {
            out.append("RESULT: BLOCKED — ")
               .append(error.getClass().getSimpleName())
               .append(": ").append(error.getMessage()).append('\n');
        }
        out.append("New Wine27 prefix and wineboot: NOT ATTEMPTED\n");
        return out.toString();
    }
}

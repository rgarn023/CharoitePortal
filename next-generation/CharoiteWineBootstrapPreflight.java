package com.charoitegames.core;

import android.content.Context;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;

/** Non-executing inventory of source-built Wine dependencies. Fail closed. */
public final class CharoiteWineBootstrapPreflight {
    private static final String PACKAGE="com.charoitx";
    private static final String ASSET="charoite-next/wine-bootstrap-preflight.json";
    private static final String SOURCE="c74acb09d51b447f5d5ac56c87608d3ec565a767";
    private CharoiteWineBootstrapPreflight() {}

    private static String load(Context context) throws Exception {
        ByteArrayOutputStream data=new ByteArrayOutputStream();
        try (InputStream input=context.getAssets().open(ASSET)) {
            byte[] buf=new byte[2048];
            int n;
            while ((n=input.read(buf))!=-1) {
                if (data.size()+n>32768) throw new SecurityException("Oversized audit");
                data.write(buf,0,n);
            }
        }
        return data.toString("UTF-8");
    }

    private static String describe(JSONArray values, int limit) throws Exception {
        if (values.length()>limit) throw new SecurityException("Excess audit entries");
        StringBuilder names=new StringBuilder();
        for (int i=0;i<values.length();i++) {
            String name=values.getString(i);
            if (!name.matches("[A-Za-z0-9._+-]{1,128}"))
                throw new SecurityException("Unsafe dependency name");
            if (i<12) {
                if (names.length()>0) names.append(", ");
                names.append(name);
            }
        }
        if (values.length()>12) names.append(", ...");
        return names.length()==0 ? "none" : names.toString();
    }

    public static String report(Context context) {
        StringBuilder out=new StringBuilder();
        out.append("CHAROITE NEXT — WINE BOOTSTRAP PREFLIGHT\n");
        out.append("Scope: audited source-built bundle, READ ONLY\n");
        out.append("Wine prefixes, games and saves: NOT ACCESSED\n");
        if (!PACKAGE.equals(context.getPackageName()))
            return out.append("RESULT: BLOCKED — wrong Android package\n").toString();
        try {
            JSONObject index=new JSONObject(load(context));
            if (index.getInt("schema_version")!=1
                    || !PACKAGE.equals(index.getString("android_package"))
                    || !SOURCE.equals(index.getString("wine_source_sha"))
                    || index.getLong("source_run")!=40898982875L
                    || index.getInt("component_count")!=22
                    || index.getInt("nls_count")!=76
                    || index.getBoolean("launch_ready")
                    || index.getBoolean("installable_as_runtime")
                    || index.getBoolean("prefix_created")
                    || index.getBoolean("fex_installed")
                    || index.getBoolean("graphics_verified")
                    || index.getBoolean("device_boot_tested")
                    || index.getBoolean("anti_cheat_supported")
                    || !index.getString("bundle_manifest_sha256").matches("[0-9a-f]{64}")
                    || !index.getString("dependency_review_sha256").matches("[0-9a-f]{64}"))
                throw new SecurityException("Unverified bootstrap provenance/readiness");
            JSONArray imports=index.getJSONArray("pe_imports_not_bundled");
            JSONArray nativeNeeded=index.getJSONArray("android_needed_libraries");
            String missing=describe(imports,512);
            String needed=describe(nativeNeeded,128);
            out.append("Source archive: 22 ELF/PE components, 76 NLS tables\n");
            out.append("Wine source: pinned and verified in CI\n");
            out.append("PE imports not bundled in archive: ")
                    .append(imports.length()).append("\n");
            out.append("Names: ").append(missing).append("\n");
            out.append("Android ELF DT_NEEDED entries: ")
                    .append(nativeNeeded.length()).append("\n");
            out.append("Names: ").append(needed).append("\n");
            out.append("FEX/ARM64EC bridge: NOT INSTALLED\n");
            out.append("GPU/display/input: NOT VERIFIED\n");
            out.append("Fresh Next Wine prefix: NOT CREATED\n");
            out.append("wineboot/Windows EXE: NOT EXECUTED\n");
            out.append("Battle.net/Steam/DX12: NOT VERIFIED\n");
            out.append("Modern runner: NOT READY; launch blocked\n");
            out.append("RESULT: PASS — source evidence verified; NOT launch-ready\n");
        } catch (Exception error) {
            out.append("RESULT: BLOCKED — ")
                    .append(error.getClass().getSimpleName()).append("\n");
        }
        return out.toString();
    }
}

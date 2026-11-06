package com.charoitegames.core;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.view.View;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.json.JSONObject;

/**
 * First in-app module management milestone. Display mode and APK inventory only:
 * no Wine, prefix, module installation, downloads, executable probes or cleanup.
 * Automatic mode retains the existing runner; advanced details cannot enable
 * Wine29, FEX, Proton, or any unverified graphics combination.
 */
public final class CharoiteCoreManager {
    private static final String PACKAGE = "com.charoitx";
    private static final String PREF = "charoite_core_manager_ui_v1";
    private static final String SHOW_ADVANCED = "show_advanced_details";
    private static final String WINE29_INDEX =
            "charoite-next/wine29-sealed012/wine29-sealed012-index.json";

    private CharoiteCoreManager() {}

    private static TextView text(Activity activity, String content, int size, boolean heading) {
        TextView view = new TextView(activity);
        view.setText(content);
        view.setTextSize(size);
        view.setTextColor(Color.rgb(heading ? 240 : 206,
                                   heading ? 230 : 196,
                                   heading ? 255 : 230));
        view.setPadding(0, 10, 0, 10);
        return view;
    }

    /**
     * Only inspect a capped metadata record inside this APK. The asset's mere
     * presence is not a SHA audit of extracted phone files or a runnable engine.
     */
    private static String wine29Packaged(Context context) {
        try (InputStream in = context.getAssets().open(WINE29_INDEX)) {
            ByteArrayOutputStream content = new ByteArrayOutputStream();
            byte[] chunk = new byte[2048];
            int count;
            while ((count = in.read(chunk)) != -1) {
                if (count + content.size() > 65536)
                    return "APK metadata too large; unavailable";
                content.write(chunk, 0, count);
            }
            JSONObject data = new JSONObject(
                    new String(content.toByteArray(), StandardCharsets.UTF_8));
            if (data.getInt("schema_version") != 1
                    || !PACKAGE.equals(data.getString("package"))
                    || data.getInt("module_count") != 111
                    || data.getInt("pe_count") != 35
                    || data.getInt("nls_count") != 76)
                return "APK metadata mismatch; not selectable";
            return "Packaged: 35 PE + 76 NLS (metadata only); NOT RUNNABLE";
        } catch (Exception e) {
            return "APK Wine29 module index unavailable; not selectable";
        }
    }

    private static String nativePresence(Context context) {
        File dir = new File(context.getApplicationInfo().nativeLibraryDir);
        String[] names = {
            "libcharoite_wine29_loader.so",
            "libcharoite_wine29_ntdll.so",
            "libcharoite_wine29_wineserver.so"
        };
        int present = 0;
        for (String name : names) {
            if (new File(dir, name).isFile()) present++;
        }
        return "APK native Wine29 ELF files: " + present + "/3 present; "
                + "presence only, NOT a hash or startup verification";
    }

    public static String inventory(Context context) {
        if (!PACKAGE.equals(context.getPackageName()))
            return "BLOCKED: unexpected Android package; no runtime selection";
        CharoiteNextRuntime.Engine legacy = CharoiteNextRuntime.inspect(
                context, CharoiteNextRuntime.WINE_BOX64);
        return "CHAROITE CORE — MODULE INVENTORY (READ ONLY)\n"
                + "Core Manager mode: Automatic. Existing runner retained.\n"
                + "Windows API / legacy: " + legacy.label
                + " — available as inherited runner; individual games not guaranteed.\n"
                + "Wine29 ARM64 / ARM64EC: " + wine29Packaged(context) + "\n"
                + nativePresence(context) + "\n"
                + "Wine29 v1 startup: FAILED at kernel32.dll c0000135; no initialized prefix.\n"
                + "CPU translation: legacy Box64 available; FEX NOT INTEGRATED.\n"
                + "Graphics: inherited renderer only; modern Wine29 Vulkan/DXVK/VKD3D NOT VERIFIED.\n"
                + "Audio/input: inherited Android integration; modern runtime NOT VERIFIED.\n"
                + "Environments: existing data kept unchanged; no migration.\n"
                + "Module installs, updates, rollback and runtime switching: NOT ENABLED.\n"
                + "No Wine, wineserver, Wineboot, shell, game or executable is run.\n"
                + "Do not confuse packaged files with launch readiness.";
    }

    public static void show(Activity activity) {
        if (!PACKAGE.equals(activity.getPackageName())) {
            new AlertDialog.Builder(activity)
                    .setTitle("Charoite Core Manager")
                    .setMessage("Unavailable for this Android package")
                    .setPositiveButton("Close", null).show();
            return;
        }
        SharedPreferences display = activity.getSharedPreferences(PREF, Context.MODE_PRIVATE);
        ScrollView scroll = new ScrollView(activity);
        LinearLayout body = new LinearLayout(activity);
        body.setOrientation(LinearLayout.VERTICAL);
        int padding = (int)(16 * activity.getResources().getDisplayMetrics().density + 0.5f);
        body.setPadding(padding, padding, padding, padding);
        scroll.addView(body);

        body.addView(text(activity, "AUTOMATIC — EXISTING ENGINE", 17, true));
        body.addView(text(activity,
            "The Core Manager will eventually choose compatible modules per environment. "
            + "For now, the existing Wine/Box64 engine stays selected. Modern Wine29 "
            + "and FEX cannot be activated until startup and compatibility tests pass.",
            13, false));
        body.addView(text(activity, "MODULE INVENTORY", 15, true));
        body.addView(text(activity,
            "Wine/Box64: existing runner\n"
            + "Wine29: packaged research modules; blocked at kernel32.dll\n"
            + "FEX/Proton: not integrated\n"
            + "Graphics: legacy integration; modern stack unverified\n"
            + "Audio/input: legacy integration; modern stack unverified",
            13, false));

        CheckBox advanced = new CheckBox(activity);
        advanced.setText("Show advanced module details");
        advanced.setTextColor(Color.rgb(234, 222, 250));
        advanced.setChecked(display.getBoolean(SHOW_ADVANCED, false));
        body.addView(advanced);
        final String report = inventory(activity);
        TextView details = text(activity, report, 12, false);
        details.setTextIsSelectable(true);
        details.setVisibility(advanced.isChecked() ? View.VISIBLE : View.GONE);
        body.addView(details);
        advanced.setOnCheckedChangeListener((button, checked) -> {
            display.edit().putBoolean(SHOW_ADVANCED, checked).apply();
            details.setVisibility(checked ? View.VISIBLE : View.GONE);
        });
        body.addView(text(activity,
            "This release manages inspection preferences only. Module installation, "
            + "version switching, per-game profiles and rollback remain gated "
            + "until verified compatibility and safe storage operations exist.",
            12, false));
        new AlertDialog.Builder(activity)
            .setTitle("Charoite Core Manager — Preview")
            .setView(scroll)
            .setNeutralButton("Copy inventory", (dialog, which) -> {
                ClipboardManager clipboard = (ClipboardManager)
                        activity.getSystemService(Context.CLIPBOARD_SERVICE);
                if (clipboard != null)
                    clipboard.setPrimaryClip(ClipData.newPlainText(
                            "Charoite Core module inventory", report));
            })
            .setPositiveButton("Close", null)
            .show();
    }
}

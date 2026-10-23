package com.charoitegames.core;

import org.json.JSONObject;
import org.json.JSONException;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Iterator;
import java.util.Locale;

/**
 * Portable, declarative Charoite Portal environment file format (.cenv).
 *
 * This exports a profile only: NO Wine binaries, game installations, personal
 * paths, saved games, credentials, executable code, URLs or file permissions.
 * A separate local Wine prefix is created when the profile is installed.
 */
public final class CharoiteEnvironmentFiles {
    public static final String EXTENSION = ".cenv";
    private static final String FORMAT = "com.charoitegames.portal.environment";
    private static final int MAX_BYTES = 16384;

    private CharoiteEnvironmentFiles() {}

    public static String normalizeName(String value) {
        String name = value == null ? "" : value.trim();
        if (name.length() < 1 || name.length() > 48 ||
                name.matches(".*[\\p{Cntrl}/\\\\].*"))
            throw new IllegalArgumentException("Environment name must be 1–48 characters, without slashes or control characters.");
        return name;
    }

    public static String normalizeTheme(String theme) {
        if (!"sakura".equals(theme) && !"cosmic".equals(theme))
            throw new IllegalArgumentException("Unrecognized environment theme.");
        return theme;
    }

    public static String fileNameFor(String name) {
        String safe = normalizeName(name).replaceAll("[^\\p{L}\\p{N}._-]+", "-");
        safe = safe.replaceAll("^[.-]+", "").replaceAll("[.-]+$", "");
        if (safe.length() > 40) safe = safe.substring(0, 40);
        if (safe.isEmpty()) safe = "Charoite-Environment";
        return safe + EXTENSION;
    }

    public static JSONObject create(String name, String theme, boolean compat,
                                    int displayMode, boolean pointerCapture) throws JSONException {
        return create(name, theme, compat, displayMode, pointerCapture, false, false);
    }

    /** The language flag is optional in v1 for backward-compatible downloads. */
    public static JSONObject create(String name, String theme, boolean compat,
                                    int displayMode, boolean pointerCapture,
                                    boolean japaneseText) throws JSONException {
        return create(name, theme, compat, displayMode, pointerCapture,
                japaneseText, false);
    }

    public static JSONObject create(String name, String theme, boolean compat,
                                    int displayMode, boolean pointerCapture,
                                    boolean japaneseText, boolean installerFontRepair)
            throws JSONException {
        JSONObject settings = new JSONObject();
        settings.put("japaneseText", japaneseText);
        settings.put("installerFontRepair", japaneseText && installerFontRepair);
        settings.put("compatibilityGraphics", compat);
        settings.put("displayMode", displayMode);
        settings.put("capturePointer", pointerCapture);
        JSONObject profile = new JSONObject();
        profile.put("format", FORMAT);
        profile.put("version", 1);
        profile.put("name", normalizeName(name));
        profile.put("theme", normalizeTheme(theme));
        profile.put("settings", settings);
        // Apply the same checks to exported manifests as imported manifests.
        validate(profile);
        return profile;
    }

    public static byte[] encode(JSONObject profile) throws JSONException {
        validate(profile);
        return (profile.toString(2) + "\n").getBytes(StandardCharsets.UTF_8);
    }

    /** Max 16 KiB, UTF-8 JSON, strict keys and primitive data types. */
    public static JSONObject read(InputStream source) throws IOException, JSONException {
        if (source == null) throw new IOException("Cannot open selected environment file.");
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        byte[] chunk = new byte[4096];
        int size = 0;
        for (int n; (n = source.read(chunk)) != -1;) {
            size += n;
            if (size > MAX_BYTES)
                throw new IOException("Environment file is too large (16 KB limit).");
            output.write(chunk, 0, n);
        }
        if (size == 0) throw new IOException("Environment file is empty.");
        JSONObject profile = new JSONObject(output.toString("UTF-8"));
        validate(profile);
        return profile;
    }

    private static void onlyKeys(JSONObject object, String... allowed) throws JSONException {
        Iterator<String> keys = object.keys();
        while (keys.hasNext()) {
            String key = keys.next();
            boolean accepted = false;
            for (String option : allowed) if (option.equals(key)) accepted = true;
            if (!accepted) throw new JSONException("Unsupported environment property: " + key);
        }
    }

    public static void validate(JSONObject profile) throws JSONException {
        if (profile == null) throw new JSONException("Missing environment profile.");
        onlyKeys(profile, "format", "version", "name", "theme", "settings");
        if (!FORMAT.equals(profile.optString("format", "")))
            throw new JSONException("This is not a Charoite Portal environment file.");
        Object version = profile.opt("version");
        if (!(version instanceof Integer) || ((Integer)version) != 1)
            throw new JSONException("Unsupported environment file version.");
        Object name = profile.opt("name");
        if (!(name instanceof String)) throw new JSONException("Invalid environment name.");
        normalizeName((String)name);
        Object theme = profile.opt("theme");
        if (!(theme instanceof String)) throw new JSONException("Invalid theme.");
        normalizeTheme((String)theme);
        JSONObject settings = profile.optJSONObject("settings");
        if (settings == null) throw new JSONException("Missing compatibility settings.");
        onlyKeys(settings, "compatibilityGraphics", "displayMode", "capturePointer",
                "japaneseText", "installerFontRepair");
        if (settings.has("installerFontRepair") &&
                !(settings.opt("installerFontRepair") instanceof Boolean))
            throw new JSONException("Invalid installer font repair setting.");
        if (settings.optBoolean("installerFontRepair", false) &&
                !settings.optBoolean("japaneseText", false))
            throw new JSONException("Installer font repair requires Japanese text support.");
        if (settings.has("japaneseText") && !(settings.opt("japaneseText") instanceof Boolean))
            throw new JSONException("Invalid Japanese compatibility setting.");
        if (!(settings.opt("compatibilityGraphics") instanceof Boolean) ||
                !(settings.opt("capturePointer") instanceof Boolean))
            throw new JSONException("Invalid compatibility options.");
        Object mode = settings.opt("displayMode");
        if (!(mode instanceof Integer) || ((Integer)mode) < 0 ||
                ((Integer)mode) >= CharoiteCore.DISPLAY_MODES.length)
            throw new JSONException("Invalid display mode.");
    }
}

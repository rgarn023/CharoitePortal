package com.charoitegames.core;

import android.content.SharedPreferences;
import androidx.appcompat.app.AppCompatActivity;
import com.winlator.container.Container;
import com.winlator.container.ContainerManager;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.UUID;

/**
 * Charoite Portal environment registry.
 * One entry = themed library + selected native Wine container.
 * NEVER deletes/recreates containers, files, prefixes or user game data.
 * Legacy Touhou preference/game_library remain in-place for app upgrades.
 */
public final class CharoiteEnvironments {
    public static final String TOUHOU = "touhou-realm";
    public static final String GENERAL = "general-gaming";
    private static final String KEY = "charoite_environments_v1";
    private static final String ACTIVE = "charoite_active_environment_v1";

    private CharoiteEnvironments() {}

    private static SharedPreferences prefs(AppCompatActivity host) {
        return host.getPreferences(AppCompatActivity.MODE_PRIVATE);
    }

    private static JSONObject make(String id, String name, String template, int containerId)
            throws Exception {
        JSONObject item = new JSONObject();
        item.put("id", id);
        item.put("name", name);
        item.put("template", template);
        item.put("containerId", Math.max(containerId, 0));
        return item;
    }

    /** Called before UI construction. Existing game library stays under game_library. */
    public static synchronized void initialize(AppCompatActivity host) {
        SharedPreferences p = prefs(host);
        if (p.contains(KEY)) return;
        try {
            int legacyId = p.getInt("touhou_container", 0);
            ContainerManager manager = new ContainerManager(host);
            Container legacy = legacyId > 0 ? manager.getContainerById(legacyId) : null;
            if (legacy == null && !manager.getContainers().isEmpty())
                legacy = manager.getContainers().get(0);
            JSONArray entries = new JSONArray();
            entries.put(make(TOUHOU, "Touhou Realm", "touhou",
                    legacy == null ? 0 : legacy.id));
            if (!p.edit().putString(KEY, entries.toString())
                    .putString(ACTIVE, TOUHOU).commit())
                throw new IllegalStateException("Cannot save environment registry");
        } catch (Exception failure) {
            throw new IllegalStateException("Cannot initialize game environments", failure);
        }
    }

    public static synchronized JSONArray list(AppCompatActivity host) {
        initialize(host);
        try {
            return new JSONArray(prefs(host).getString(KEY, "[]"));
        } catch (Exception ignored) {
            return new JSONArray();
        }
    }

    public static String activeId(AppCompatActivity host) {
        return prefs(host).getString(ACTIVE, TOUHOU);
    }

    public static String libraryKey(AppCompatActivity host) {
        String id = activeId(host);
        // Important: never move/delete existing Touhou list or reorder settings.
        return TOUHOU.equals(id) ? "game_library" : "charoite_library_" + id;
    }

    public static boolean isTouhou(AppCompatActivity host) {
        return TOUHOU.equals(activeId(host));
    }

    public static synchronized JSONObject active(AppCompatActivity host) {
        String id = activeId(host);
        JSONArray entries = list(host);
        for (int i=0; i<entries.length(); i++) {
            JSONObject item = entries.optJSONObject(i);
            if (item != null && id.equals(item.optString("id"))) return item;
        }
        JSONObject initial = entries.optJSONObject(0);
        return initial == null ? new JSONObject() : initial;
    }

    public static String activeName(AppCompatActivity host) {
        return active(host).optString("name", "Touhou Realm");
    }

    public static synchronized boolean switchTo(AppCompatActivity host, String id) {
        for (int i=0; i<list(host).length(); i++) {
            JSONObject item = list(host).optJSONObject(i);
            if (item != null && id.equals(item.optString("id")))
                return prefs(host).edit().putString(ACTIVE, id).commit();
        }
        return false;
    }

    public static synchronized JSONObject installPreset(AppCompatActivity host, String id)
            throws Exception {
        if (!GENERAL.equals(id) && !TOUHOU.equals(id))
            throw new IllegalArgumentException("Only verified built-in environment templates are supported");
        JSONArray entries = list(host);
        for (int i=0; i<entries.length(); i++) {
            JSONObject existing = entries.optJSONObject(i);
            if (existing != null && id.equals(existing.optString("id")))
                throw new IllegalArgumentException("Environment is already installed");
        }
        JSONObject result = make(id, GENERAL.equals(id) ? "General Gaming" : "Touhou Realm",
                GENERAL.equals(id) ? "general" : "touhou", 0);
        entries.put(result);
        if (!prefs(host).edit().putString(KEY, entries.toString()).commit())
            throw new IllegalStateException("Failed to save environment");
        return result;
    }

    public static synchronized JSONObject create(AppCompatActivity host, String rawName)
            throws Exception {
        String name = rawName == null ? "" : rawName.trim();
        if (name.isEmpty() || name.length() > 48)
            throw new IllegalArgumentException("Choose an environment name (1–48 characters)");
        JSONArray entries = list(host);
        if (entries.length() >= 20)
            throw new IllegalArgumentException("Maximum of 20 environments");
        for (int i=0; i<entries.length(); i++) {
            JSONObject existing = entries.optJSONObject(i);
            if (existing != null && name.equalsIgnoreCase(existing.optString("name")))
                throw new IllegalArgumentException("An environment already has that name");
        }
        JSONObject result = make("custom-" + UUID.randomUUID(), name, "custom", 0);
        entries.put(result);
        if (!prefs(host).edit().putString(KEY, entries.toString()).commit())
            throw new IllegalStateException("Failed to save environment");
        return result;
    }

    public static synchronized void attachContainer(AppCompatActivity host, String id, int containerId)
            throws Exception {
        if (containerId <= 0) throw new IllegalArgumentException("Invalid container ID");
        JSONArray entries = list(host);
        boolean found = false;
        for (int i=0; i<entries.length(); i++) {
            JSONObject item = entries.optJSONObject(i);
            if (item != null && id.equals(item.optString("id"))) {
                item.put("containerId", containerId);
                found = true;
                break;
            }
        }
        if (!found) throw new IllegalArgumentException("Unknown environment");
        SharedPreferences.Editor edit = prefs(host).edit().putString(KEY, entries.toString());
        if (TOUHOU.equals(id)) edit.putInt("touhou_container", containerId);
        if (!edit.commit()) throw new IllegalStateException("Could not save environment container");
    }

    public static int activeContainerId(AppCompatActivity host) {
        return active(host).optInt("containerId", 0);
    }

    public static String activeTheme(AppCompatActivity host) {
        return active(host).optString("template", "touhou");
    }
}

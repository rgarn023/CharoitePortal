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
    public static final String BATTLE_NET = "battle-net-gaming";
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

    /**
     * First installation: General Gaming is home and Touhou Realm is already
     * available in the switcher. They are independent Wine containers.
     *
     * In-place upgrades: preserve the exact current environment, its games,
     * theme, settings, and container. Only add missing built-in presets.
     * Do not overwrite the ACTIVE setting or attach a second realm to an
     * existing Windows container.
     */
    public static synchronized void initialize(AppCompatActivity host) {
        SharedPreferences p = prefs(host);
        try {
            if (p.contains(KEY)) {
                JSONArray existing = new JSONArray(p.getString(KEY, "[]"));
                boolean hasGeneral = false, hasTouhou = false, hasBattleNet = false;
                for (int i = 0; i < existing.length(); i++) {
                    JSONObject entry = existing.optJSONObject(i);
                    if (entry == null) continue;
                    hasGeneral |= GENERAL.equals(entry.optString("id"));
                    hasTouhou |= TOUHOU.equals(entry.optString("id"));
                    hasBattleNet |= BATTLE_NET.equals(entry.optString("id"));
                }
                if (hasGeneral && hasTouhou && hasBattleNet) return;
                if (!hasGeneral)
                    existing.put(make(GENERAL, "General Gaming", "general", 0));
                if (!hasTouhou)
                    existing.put(make(TOUHOU, "Touhou Realm", "touhou", 0));
                // Additive preset for upgrades: NEVER change active ID or
                // attach this realm to an older Touhou/General Wine container.
                if (!hasBattleNet)
                    existing.put(make(BATTLE_NET, "Battle.net Gaming", "battlenet", 0));
                if (!p.edit().putString(KEY, existing.toString()).commit())
                    throw new IllegalStateException("Cannot register built-in environments");
                // ACTIVE intentionally remains UNCHANGED on updates.
                return;
            }
            int legacyId = p.getInt("touhou_container", 0);
            ContainerManager manager = new ContainerManager(host);
            Container legacy = legacyId > 0 ? manager.getContainerById(legacyId) : null;
            if (legacy == null && !manager.getContainers().isEmpty())
                legacy = manager.getContainers().get(0);
            JSONArray entries = new JSONArray();
            entries.put(make(GENERAL, "General Gaming", "general", 0));
            entries.put(make(TOUHOU, "Touhou Realm", "touhou",
                    legacy == null ? 0 : legacy.id));
            entries.put(make(BATTLE_NET, "Battle.net Gaming", "battlenet", 0));
            // Existing prefixes created before the environment registry
            // belong to Touhou; a truly fresh Portal opens in General Gaming.
            String initial = legacy == null ? GENERAL : TOUHOU;
            if (!p.edit().putString(KEY, entries.toString())
                    .putString(ACTIVE, initial).commit())
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
        return prefs(host).getString(ACTIVE, GENERAL);
    }

    public static String libraryKey(AppCompatActivity host) {
        String id = activeId(host);
        // Important: never move/delete existing Touhou list or reorder settings.
        return TOUHOU.equals(id) ? "game_library" : "charoite_library_" + id;
    }

    public static boolean isTouhou(AppCompatActivity host) {
        return TOUHOU.equals(activeId(host));
    }

    public static boolean isBattleNet(AppCompatActivity host) {
        // Retain the Battle.net Setup helper after exporting/importing a
        // .cenv environment without reusing the original Wine container.
        return BATTLE_NET.equals(activeId(host)) ||
                "battlenet".equals(active(host).optString("template"));
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
        return active(host).optString("name", "General Gaming");
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
        if (!GENERAL.equals(id) && !TOUHOU.equals(id) && !BATTLE_NET.equals(id))
            throw new IllegalArgumentException("Only verified built-in environment templates are supported");
        JSONArray entries = list(host);
        for (int i=0; i<entries.length(); i++) {
            JSONObject existing = entries.optJSONObject(i);
            if (existing != null && id.equals(existing.optString("id")))
                throw new IllegalArgumentException("Environment is already installed");
        }
        JSONObject result = make(id,
                GENERAL.equals(id) ? "General Gaming" :
                        BATTLE_NET.equals(id) ? "Battle.net Gaming" : "Touhou Realm",
                GENERAL.equals(id) ? "general" :
                        BATTLE_NET.equals(id) ? "battlenet" : "touhou", 0);
        entries.put(result);
        if (!prefs(host).edit().putString(KEY, entries.toString()).commit())
            throw new IllegalStateException("Failed to save environment");
        return result;
    }

    public static synchronized JSONObject create(AppCompatActivity host, String rawName)
            throws Exception {
        return create(host, rawName, "cosmic");
    }

    public static synchronized JSONObject create(AppCompatActivity host, String rawName,
                                                  String theme) throws Exception {
        String name = CharoiteEnvironmentFiles.normalizeName(rawName);
        CharoiteEnvironmentFiles.normalizeTheme(theme);
        JSONArray entries = list(host);
        if (entries.length() >= 20)
            throw new IllegalArgumentException("Maximum of 20 environments");
        for (int i=0; i<entries.length(); i++) {
            JSONObject existing = entries.optJSONObject(i);
            if (existing != null && name.equalsIgnoreCase(existing.optString("name")))
                throw new IllegalArgumentException("An environment already has that name");
        }
        JSONObject result = make("custom-" + UUID.randomUUID(), name, theme, 0);
        entries.put(result);
        if (!prefs(host).edit().putString(KEY, entries.toString()).commit())
            throw new IllegalStateException("Failed to save environment");
        return result;
    }


    /** Re-importing an existing file produces an independent environment. */
    public static synchronized JSONObject installFromFile(AppCompatActivity host,
                                                           JSONObject profile) throws Exception {
        CharoiteEnvironmentFiles.validate(profile);
        String name = profile.getString("name");
        String theme = profile.getString("theme");
        JSONArray installed = list(host);
        String available = name;
        int number = 2;
        boolean collision;
        do {
            collision = false;
            for (int i = 0; i < installed.length(); i++) {
                JSONObject item = installed.optJSONObject(i);
                if (item != null && available.equalsIgnoreCase(item.optString("name"))) {
                    collision = true;
                    break;
                }
            }
            if (collision) {
                String suffix = " (" + number++ + ")";
                available = name.substring(0, Math.min(name.length(), 48 - suffix.length())) + suffix;
            }
        } while (collision && number <= 22);
        return create(host, available, theme);
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
        return active(host).optString("template", "general");
    }
}

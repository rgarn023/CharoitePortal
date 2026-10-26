package com.charoitegames.core;

import android.content.Context;
import android.content.SharedPreferences;
import androidx.appcompat.app.AppCompatActivity;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

/**
 * Persistent cross-realm game library; portal views never directly manipulate
 * the stored JSON. Reuses exact historical Touhou and other-realm preference
 * keys, preserving old game lists and existing Windows installations.
 */
public final class CharoiteGameLibrary {
    private CharoiteGameLibrary() {}

    private static SharedPreferences prefs(AppCompatActivity host) {
        return host.getPreferences(Context.MODE_PRIVATE);
    }
    private static String key(AppCompatActivity host) {
        return CharoiteEnvironments.libraryKey(host);
    }

    /** Canonicalize only metadata, never delete files or save data. */
    public static synchronized JSONArray load(AppCompatActivity host) {
        JSONArray source;
        try { source = new JSONArray(prefs(host).getString(key(host), "[]")); }
        catch (Exception ignored) { return new JSONArray(); }
        ArrayList<JSONObject> backward = new ArrayList<>();
        Set<String> paths = new HashSet<>();
        boolean keptInstaller = false;
        for (int i = source.length() - 1; i >= 0; i--) {
            JSONObject item = source.optJSONObject(i);
            if (item == null) continue;
            boolean installer = item.optBoolean("installer");
            if (installer && keptInstaller) continue;
            String path = item.optString("path", "");
            if (path.isEmpty() || !paths.add(path)) continue;
            if (installer) keptInstaller = true;
            backward.add(item);
        }
        JSONArray normalized = new JSONArray();
        for (int i = backward.size() - 1; i >= 0; i--)
            normalized.put(backward.get(i));
        if (normalized.length() != source.length())
            prefs(host).edit().putString(key(host), normalized.toString()).apply();
        return normalized;
    }

    private static void persist(AppCompatActivity host, JSONArray items) {
        if (!prefs(host).edit().putString(key(host), items.toString()).commit())
            throw new IllegalStateException("Unable to save game library");
    }

    /**
     * One visible installer slot, without deleting older imported folders.
     * Imported playable games retain their order; repeat paths are deduped.
     */
    public static synchronized void save(AppCompatActivity host, JSONObject item) {
        if (item == null || item.optString("path", "").isEmpty())
            throw new IllegalArgumentException("Game executable path missing");
        JSONArray existing = load(host), next = new JSONArray();
        boolean installer = item.optBoolean("installer");
        String path = item.optString("path");
        for (int i = 0; i < existing.length(); i++) {
            JSONObject old = existing.optJSONObject(i);
            if (old == null || path.equals(old.optString("path"))) continue;
            if (installer && old.optBoolean("installer")) continue;
            next.put(old);
        }
        next.put(item);
        persist(host, next);
    }

    public static synchronized int mergeInstalled(AppCompatActivity host,
                                                   java.util.List<JSONObject> newGames) {
        JSONArray entries = load(host);
        Set<String> existing = new HashSet<>();
        for (int i = 0; i < entries.length(); i++) {
            JSONObject item = entries.optJSONObject(i);
            if (item != null) existing.add(item.optString("path"));
        }
        int added = 0;
        for (JSONObject game : newGames) {
            if (game == null || game.optBoolean("installer")) continue;
            String path = game.optString("path");
            if (path.isEmpty() || !existing.add(path)) continue;
            entries.put(game);
            added++;
        }
        if (added > 0) persist(host, entries);
        return added;
    }

    /** Reorder only playable tile metadata. Installer stays in its slot. */
    public static synchronized boolean reorder(AppCompatActivity host,
                                                String fromPath, String targetPath) {
        if (fromPath == null || fromPath.equals(targetPath)) return false;
        JSONArray original = load(host);
        ArrayList<JSONObject> games = new ArrayList<>();
        for (int i = 0; i < original.length(); i++) {
            JSONObject item = original.optJSONObject(i);
            if (item != null && !item.optBoolean("installer")) games.add(item);
        }
        int from = -1, to = -1;
        for (int i = 0; i < games.size(); i++) {
            if (fromPath.equals(games.get(i).optString("path"))) from = i;
            if (targetPath.equals(games.get(i).optString("path"))) to = i;
        }
        if (from < 0 || to < 0) return false;
        JSONObject item = games.remove(from);
        games.add(to, item);
        JSONArray ordered = new JSONArray();
        int gameIndex = 0;
        for (int i = 0; i < original.length(); i++) {
            JSONObject old = original.optJSONObject(i);
            if (old == null) continue;
            ordered.put(old.optBoolean("installer") ? old : games.get(gameIndex++));
        }
        persist(host, ordered);
        return true;
    }

    /** Remove only the selected game shortcut. No Windows files are touched.
     * Returns false when the entry is missing; installer metadata is separate.
     */
    public static synchronized boolean remove(AppCompatActivity host, String executable) {
        if (executable == null || executable.isEmpty()) return false;
        JSONArray original = load(host), kept = new JSONArray();
        boolean found = false;
        for (int i = 0; i < original.length(); i++) {
            JSONObject item = original.optJSONObject(i);
            if (item == null) continue;
            if (!item.optBoolean("installer") &&
                    executable.equals(item.optString("path"))) {
                found = true;
            } else kept.put(item);
        }
        if (found) persist(host, kept);
        return found;
    }

    public static JSONObject newestInstaller(JSONArray library) {
        for (int i = library.length() - 1; i >= 0; i--) {
            JSONObject item = library.optJSONObject(i);
            if (item != null && item.optBoolean("installer")) return item;
        }
        return null;
    }
}

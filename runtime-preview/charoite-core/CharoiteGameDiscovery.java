package com.charoitegames.core;

import org.json.JSONObject;
import java.io.File;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Read-only, bounded Windows C: discovery for any environment. Game-specific
 * executable filtering and naming come from a pluggable Core profile.
 */
public final class CharoiteGameDiscovery {
    private CharoiteGameDiscovery() {}

    public static List<JSONObject> scan(File containerRoot,
                                        CharoiteGameProfiles.Profile profile) throws Exception {
        if (containerRoot == null || profile == null)
            throw new IllegalArgumentException("Missing Windows container or detection profile");
        File drive = new File(containerRoot, ".wine/drive_c");
        if (!drive.isDirectory()) throw new IllegalStateException("Windows C: is not ready");
        List<JSONObject> found = new ArrayList<>();
        int[] visited = {0};
        walk(drive, drive, profile, found, 0, visited);
        return found;
    }

    private static void walk(File drive, File dir, CharoiteGameProfiles.Profile profile,
                             List<JSONObject> found, int depth, int[] visited) throws Exception {
        if (depth > 14 || visited[0] >= 25000 || found.size() >= 100) return;
        File[] children = dir.listFiles();
        if (children == null) return;
        String rootPath = drive.getCanonicalPath() + File.separator;
        for (File child : children) {
            if (++visited[0] > 25000) break;
            if (Files.isSymbolicLink(child.toPath())) continue;
            if (!child.getCanonicalPath().startsWith(rootPath)) continue;
            String name = child.getName().toLowerCase(Locale.ROOT);
            if (child.isDirectory()) {
                if (name.equals("windows") || name.equals("programdata")
                        || name.equals("$recycle.bin")) continue;
                walk(drive, child, profile, found, depth + 1, visited);
            } else if (child.isFile() && profile.acceptsInstalledExecutable(child.getName())) {
                JSONObject entry = new JSONObject();
                entry.put("name", profile.displayName(child.getName()));
                entry.put("path", child.getAbsolutePath());
                // Recognize supported keyboard profiles as games are found.
                // Re-check at launch; never parse or modify arbitrary EXEs.
                entry.put("controlProfile",
                        CharoiteGameControlProfiles.idForExecutable(child.getAbsolutePath()));
                entry.put("installer", false);
                entry.put("files", 0);
                found.add(entry);
            }
            if (found.size() >= 100) break;
        }
    }
}

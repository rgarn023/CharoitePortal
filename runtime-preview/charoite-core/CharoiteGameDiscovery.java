package com.charoitegames.core;

import org.json.JSONObject;
import java.io.File;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Shared bounded Wine C: drive discovery with per-realm executable rules. */
public final class CharoiteGameDiscovery {
    public interface GameRule {
        /** Only match executable basenames; never modify a scanned file. */
        boolean accepts(String executableName);
        /** Display name independent from launcher UI. */
        String displayName(String executableName);
    }

    private static final GameRule TOUHOU = new GameRule() {
        @Override public boolean accepts(String executable) {
            String lower = executable.toLowerCase(Locale.ROOT);
            return lower.equals("gn_enbu.exe") || lower.equals("enbu_ap.exe")
                    || lower.matches("th(0[6-9]|1[0-9]|20)\\.exe");
        }
        @Override public String displayName(String executable) {
            String lower = executable.toLowerCase(Locale.ROOT);
            if (lower.equals("gn_enbu.exe")) return "Touhou Puppet Dance Performance";
            if (lower.equals("enbu_ap.exe"))
                return "Touhou Puppet Dance Performance: Shard of Dreams";
            return "Touhou game: " + executable;
        }
    };

    private static final GameRule GENERIC = new GameRule() {
        @Override public boolean accepts(String executable) {
            String n = executable.toLowerCase(Locale.ROOT);
            return n.endsWith(".exe") && !CharoiteGameImport.isLikelyInstaller(n)
                    && !n.equals("unins000.exe") && !n.equals("uninstall.exe")
                    && !n.equals("winecfg.exe") && !n.equals("explorer.exe")
                    && !n.equals("regedit.exe");
        }
        @Override public String displayName(String executable) {
            return executable.replaceFirst("(?i)\\.exe$", "");
        }
    };

    public static GameRule forEnvironment(boolean touhou) {
        return touhou ? TOUHOU : GENERIC;
    }

    public static String displayName(String filename, boolean touhou) {
        return forEnvironment(touhou).displayName(filename);
    }

    /** Allow future environment modules to inject other detectors. */
    public static List<JSONObject> scan(File containerRoot, GameRule rule) throws Exception {
        if (containerRoot == null || rule == null)
            throw new IllegalArgumentException("Missing Windows container or detection rule");
        File drive = new File(containerRoot, ".wine/drive_c");
        if (!drive.isDirectory()) throw new IllegalStateException("Windows C: is not ready");
        List<JSONObject> found = new ArrayList<>();
        int[] visited = {0};
        walk(drive, drive, rule, found, 0, visited);
        return found;
    }

    private static void walk(File drive, File dir, GameRule rule,
                             List<JSONObject> found, int depth, int[] visited) throws Exception {
        if (depth > 14 || visited[0] >= 25000 || found.size() >= 100) return;
        File[] children = dir.listFiles();
        if (children == null) return;
        for (File child : children) {
            if (++visited[0] > 25000) break;
            if (Files.isSymbolicLink(child.toPath())) continue;
            if (!child.getCanonicalPath().startsWith(drive.getCanonicalPath() + File.separator)) continue;
            String name = child.getName().toLowerCase(Locale.ROOT);
            if (child.isDirectory()) {
                if (name.equals("windows") || name.equals("programdata")
                        || name.equals("$recycle.bin")) continue;
                walk(drive, child, rule, found, depth + 1, visited);
            } else if (child.isFile() && rule.accepts(child.getName())) {
                JSONObject game = new JSONObject();
                game.put("name", rule.displayName(child.getName()));
                game.put("path", child.getAbsolutePath());
                game.put("installer", false);
                game.put("files", 0);
                found.add(game);
            }
            if (found.size() >= 100) break;
        }
    }

    private CharoiteGameDiscovery() {}
}

package com.charoitegames.core;

import android.content.Context;
import java.io.File;
import java.nio.file.Files;
import java.util.Locale;

/**
 * Shard of Dreams reads the base TPDP game's files via a directory named
 * "notkey" inside the expansion directory under older Wine builds.
 *
 * Correct only the verified installed pair, never downloaded installers,
 * other games, user files, or existing notkey entries. Wine 9.21+ might
 * not need the link; a valid preexisting link/file is left unchanged.
 */
public final class CharoiteShardOfDreamsSupport {
    private CharoiteShardOfDreamsSupport() {}

    /**
     * Read-only explanation for a Shard installer that appears to finish
     * without creating a playable Library tile. Missing notkey is a LAUNCH
     * issue and cannot explain a missing enbu_ap.exe.
     */
    public static String inspectInstalledExpansion(
            File containerRoot, java.util.List<org.json.JSONObject> installedGames) {
        File drive = new File(containerRoot, ".wine/drive_c");
        if (!drive.isDirectory())
            return "Shard scan: Windows C: drive is missing in this environment.";
        boolean shardFound = false;
        String shardPath = "";
        boolean baseFound = false;
        if (installedGames != null) {
            for (org.json.JSONObject item : installedGames) {
                if (item == null) continue;
                String path = item.optString("path", "");
                String name = new File(path).getName().toLowerCase(Locale.ROOT);
                if (name.equals("enbu_ap.exe")) {
                    shardFound = true;
                    shardPath = path;
                }
                if (name.equals("gn_enbu.exe")) baseFound = true;
            }
        }
        if (shardFound) {
            return "Shard executable found: " + shardPath +
                    "\nCore can register this separate game in Library. " +
                    "The notkey check applies only when launching enbu_ap.exe. " +
                    (baseFound ? "Original TPDP also found." :
                    "Original TPDP executable not found in this C: scan.");
        }
        // Bound the inspection to installed directory names. Never invent a
        // playable entry for a setup.exe or an incomplete install directory.
        java.util.ArrayList<String> candidates = new java.util.ArrayList<>();
        int[] visited = {0};
        inspectCandidateDirectories(drive, 0, visited, candidates);
        if (!candidates.isEmpty())
            return "Shard installation folder(s) detected, but enbu_ap.exe " +
                    "is missing: " + String.join("; ", candidates) +
                    "\nThe installer may not have completed, or its files " +
                    "may be in another environment. Re-open the installer " +
                    "and check for its Finish page. No files were changed.";
        return "Shard executable enbu_ap.exe was NOT found in this active " +
                "environment's Windows C:. " +
                (baseFound ? "Original TPDP is present. " : "") +
                "Check that the Shard installer completed and that it " +
                "installed to this same environment. This is not a " +
                "notkey failure. No files were changed.";
    }

    private static void inspectCandidateDirectories(File directory, int depth,
            int[] visited, java.util.List<String> output) {
        if (depth > 10 || visited[0] >= 15000 || output.size() >= 4) return;
        File[] children = directory.listFiles();
        if (children == null) return;
        for (File child : children) {
            if (++visited[0] >= 15000 || output.size() >= 4) return;
            if (!child.isDirectory() || Files.isSymbolicLink(child.toPath()))
                continue;
            String name = child.getName().toLowerCase(Locale.ROOT);
            if (name.equals("windows") || name.equals("programdata") ||
                    name.equals("$recycle.bin")) continue;
            if (name.contains("ユメノカケラ") || name.contains("shard of dreams") ||
                    name.contains("yume no kakera") ||
                    name.contains("enbu-ap")) output.add(child.getAbsolutePath());
            inspectCandidateDirectories(child, depth + 1, visited, output);
        }
    }

    public static boolean isExpansionGame(String path) {
        if (path == null) return false;
        String name = new File(path).getName().toLowerCase(Locale.ROOT);
        return name.equals("enbu_ap.exe");
    }

    private static boolean samePrefix(File expansion, File original) {
        try {
            File cDrive = expansion.getCanonicalFile();
            while (cDrive != null && !cDrive.getName().equalsIgnoreCase("drive_c"))
                cDrive = cDrive.getParentFile();
            if (cDrive == null || cDrive.getParentFile() == null ||
                    !cDrive.getParentFile().getName().equals(".wine")) return false;
            File baseDir = original.getCanonicalFile();
            return baseDir.toPath().startsWith(cDrive.toPath()) &&
                    new File(baseDir, "gn_enbu.exe").isFile();
        } catch (Exception e) {
            return false;
        }
    }

    /** Only walk the app's verified Wine drive. Bounded and read-only. */
    private static File findBase(File folder, File expansion, int depth,
                                 int[] scanned) {
        if (depth > 10 || scanned[0] > 10000) return null;
        File[] children = folder.listFiles();
        if (children == null) return null;
        for (File file : children) {
            if (++scanned[0] > 10000) return null;
            if (!file.isDirectory() || Files.isSymbolicLink(file.toPath()))
                continue;
            String name = file.getName().toLowerCase(Locale.ROOT);
            if (name.equals("windows") || name.equals("programdata") ||
                    name.equals("$recycle.bin")) continue;
            if (file.equals(expansion)) continue;
            if (new File(file, "gn_enbu.exe").isFile() &&
                    samePrefix(expansion, file)) return file;
            File match = findBase(file, expansion, depth + 1, scanned);
            if (match != null) return match;
        }
        return null;
    }

    public static String checkAndRepair(Context context, String executable) {
        if (!isExpansionGame(executable)) return "Not a Shard of Dreams launch.";
        try {
            File exe = new File(executable).getCanonicalFile();
            if (!exe.isFile()) return "Shard executable was not found: " + executable;
            File expansion = exe.getParentFile();
            File drive = expansion;
            while (drive != null && !drive.getName().equalsIgnoreCase("drive_c"))
                drive = drive.getParentFile();
            if (drive == null || drive.getParentFile() == null ||
                    !drive.getParentFile().getName().equals(".wine"))
                return "Shard is not in a verified Charoite Wine C: drive; no changes.";

            File existing = new File(expansion, "notkey");
            if (Files.exists(existing.toPath(), java.nio.file.LinkOption.NOFOLLOW_LINKS)) {
                if (Files.isSymbolicLink(existing.toPath())) {
                    File target = existing.getCanonicalFile();
                    return samePrefix(expansion, target)
                            ? "Shard notkey link already points to the base game."
                            : "An existing notkey link is not a verified TPDP base game; left untouched.";
                }
                return "Shard notkey entry already exists; left untouched.";
            }

            File base = null;
            File sibling = expansion.getParentFile();
            if (sibling != null) {
                File[] entries = sibling.listFiles();
                if (entries != null) for (File dir : entries) {
                    if (!dir.isDirectory() || dir.equals(expansion) ||
                            Files.isSymbolicLink(dir.toPath())) continue;
                    if (new File(dir, "gn_enbu.exe").isFile() &&
                            samePrefix(expansion, dir)) {
                        base = dir.getCanonicalFile();
                        break;
                    }
                }
            }
            if (base == null) base = findBase(drive, expansion, 0, new int[]{0});
            if (base == null)
                return "Shard installed, but the original gn_enbu.exe folder was not found " +
                        "inside the same Wine C: drive. Nothing was changed.";

            // One new directory symlink only, never overwrite/rename/copy
            // TPDP game content and never touch base or expansion saves.
            Files.createSymbolicLink(existing.toPath(), base.toPath());
            return "Shard compatibility: safely created the missing notkey " +
                    "reference to the existing base-game directory. No files were copied or removed.";
        } catch (Exception e) {
            return "Shard notkey compatibility check could not complete: " +
                    e.getClass().getSimpleName() + ": " + e.getMessage();
        }
    }
}

package com.charoitegames.core;

import android.content.Context;
import java.io.File;
import java.nio.file.Files;
import java.util.Locale;
import java.nio.charset.Charset;

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

    // The installed Japanese Shard release uses its original Japanese EXE,
    // rather than the historical enbu_ap.exe shorthand.
    public static final String JAPANESE_EXECUTABLE = "幻想人形演舞-ユメノカケラ-.exe";

    /** Exact Shard executable aliases, excluding updater and uninstaller. */
    public static boolean isExpansionGame(String path) {
        if (path == null) return false;
        String name = new File(path).getName().toLowerCase(Locale.ROOT);
        return name.equals("enbu_ap.exe") ||
                name.equals(JAPANESE_EXECUTABLE.toLowerCase(Locale.ROOT));
    }

    /** Find the real installed binary, never invent or rename an executable. */
    private static File installedExecutable(File directory) {
        if (directory == null || !directory.isDirectory() ||
                Files.isSymbolicLink(directory.toPath())) return null;
        for (String filename : new String[]{"enbu_ap.exe", JAPANESE_EXECUTABLE}) {
            File candidate = new File(directory, filename);
            if (candidate.isFile() && !Files.isSymbolicLink(candidate.toPath()))
                return candidate;
        }
        return null;
    }


    // FocasLens keeps its installed-game destination in an AppData
    // install.ini. The AppData folder is metadata, not the game itself.
    private static java.util.List<String> shardFolders(File drive) {
        java.util.ArrayList<String> folders = new java.util.ArrayList<>();
        inspectCandidateDirectories(drive, 0, new int[]{0}, folders);
        return folders;
    }

    /** Read only a small, validated Shift-JIS registration file. */
    private static String registeredPath(File folder) {
        File ini = new File(folder, "install.ini");
        if (!ini.isFile() || Files.isSymbolicLink(ini.toPath()) ||
                ini.length() < 1 || ini.length() > 8192) return null;
        try {
            String content = new String(Files.readAllBytes(ini.toPath()),
                    Charset.forName("windows-31j"));
            boolean inSettings = false;
            for (String raw : content.split("\\r?\\n")) {
                String line = raw.trim();
                if (line.startsWith("[") && line.endsWith("]")) {
                    inSettings = line.equalsIgnoreCase("[InstallSettings]");
                } else if (inSettings &&
                        line.regionMatches(true, 0, "InstallPath=", 0, 12)) {
                    String value = line.substring(12).trim();
                    if (value.length() >= 2 && value.startsWith("\"") &&
                            value.endsWith("\""))
                        value = value.substring(1, value.length() - 1);
                    return value.isEmpty() ? null : value;
                }
            }
        } catch (Exception ignored) { }
        return null;
    }

    /** Reject paths outside this exact Wine C: drive, including symlinks. */
    private static File verifiedDestination(File drive, String windowsPath) {
        if (windowsPath == null || windowsPath.length() < 4 ||
                !windowsPath.regionMatches(true, 0, "C:", 0, 2) ||
                (windowsPath.charAt(2) != '\\' && windowsPath.charAt(2) != '/'))
            return null;
        try {
            File root = drive.getCanonicalFile();
            File dest = new File(root,
                    windowsPath.substring(3).replace('\\', '/')).getCanonicalFile();
            return dest.toPath().startsWith(root.toPath()) ? dest : null;
        } catch (Exception ignored) { return null; }
    }

    /**
     * Recover a genuinely installed Shard EXE at the location recorded by
     * FocasLens when the bounded general scan happens to miss that location.
     * Never invent entries for registration-only or incomplete installs.
     */
    public static java.util.List<org.json.JSONObject> discoverRegisteredExpansion(
            File containerRoot) {
        java.util.ArrayList<org.json.JSONObject> found = new java.util.ArrayList<>();
        File drive = new File(containerRoot, ".wine/drive_c");
        if (!drive.isDirectory()) return found;
        for (String path : shardFolders(drive)) {
            String value = registeredPath(new File(path));
            File target = verifiedDestination(drive, value);
            if (target == null) continue;
            File executable = installedExecutable(target);
            if (executable == null) continue;
            try {
                org.json.JSONObject entry = new org.json.JSONObject();
                entry.put("name", "Touhou Puppet Dance Performance: Shard of Dreams");
                entry.put("path", executable.getCanonicalPath());
                entry.put("installer", false);
                entry.put("files", 0);
                found.add(entry);
                break;
            } catch (Exception ignored) { }
        }
        return found;
    }

    /** Bounded summary of a folder; never read, extract, or modify game data. */
    private static String contents(File dir) {
        if (!dir.isDirectory() || Files.isSymbolicLink(dir.toPath()))
            return "folder not readable";
        File[] entries = dir.listFiles();
        if (entries == null) return "folder not listable";
        java.util.Arrays.sort(entries,
                (a, b) -> a.getName().compareToIgnoreCase(b.getName()));
        if (entries.length == 0) return "EMPTY folder";
        java.util.ArrayList<String> sample = new java.util.ArrayList<>();
        int files = 0, folders = 0;
        for (File item : entries) {
            if (Files.isSymbolicLink(item.toPath())) continue;
            if (item.isDirectory()) folders++;
            if (item.isFile()) files++;
            if (sample.size() < 8) sample.add(item.getName() +
                    (item.isDirectory() ? "/" : " (" + item.length() / 1024 + " KB)"));
        }
        return files + " files, " + folders + " directories; sample: " +
                String.join(", ", sample) +
                (entries.length > sample.size() ? ", ..." : "");
    }

    private static String installationEvidence(File drive,
                                                java.util.List<String> folders) {
        StringBuilder report = new StringBuilder();
        for (String path : folders) {
            File dir = new File(path);
            boolean metadata = path.replace('\\', '/').toLowerCase(Locale.ROOT)
                    .contains("/appdata/roaming/");
            report.append("\n").append(metadata ? "AppData registration: " :
                    "Game directory: ").append(path)
                    .append("\n  Contents: ").append(contents(dir));
            if (metadata) {
                String registered = registeredPath(dir);
                report.append("\n  install.ini InstallPath: ")
                        .append(registered == null ? "(missing/unreadable)" : registered);
                File dest = verifiedDestination(drive, registered);
                if (registered != null && dest == null) {
                    report.append("\n  InstallPath does not resolve inside this Wine C:.");
                } else if (dest != null) {
                    report.append("\n  Registered folder exists: ")
                            .append(dest.isDirectory())
                            .append("; playable Shard executable: ")
                            .append(installedExecutable(dest) == null
                                    ? "not found" : installedExecutable(dest).getName());
                    if (dest.isDirectory() && !dest.equals(dir))
                        report.append("\n  Registered folder contents: ")
                                .append(contents(dest));
                }
            }
        }
        return report.toString();
    }

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
                if (isExpansionGame(name)) {
                    shardFound = true;
                    shardPath = path;
                }
                if (name.equals("gn_enbu.exe")) baseFound = true;
            }
        }
        if (shardFound) {
            return "Shard executable found: " + shardPath +
                    "\nCore can register this separate game in Library. " +
                    "The notkey check applies when launching either recognized Shard executable. " +
                    (baseFound ? "Original TPDP also found." :
                    "Original TPDP executable not found in this C: scan.");
        }
        // Bound the inspection to installed directory names. Never invent a
        // playable entry for a setup.exe or an incomplete install directory.
        java.util.List<String> candidates = shardFolders(drive);
        if (!candidates.isEmpty())
            return "Shard installation directories detected, but no recognized " +
                    "Shard executable was found: " + String.join("; ", candidates) +
                    "\nThe AppData folder is only registration metadata, not a second installation." +
                    installationEvidence(drive, candidates) +
                    "\nIf the registered destination contains neither " +
                    "enbu_ap.exe nor " + JAPANESE_EXECUTABLE + ", " +
                    "the installer has not produced a recognized game binary there. " +
                    "Check that all original setup media was imported and the " +
                    "installer reached Finish. No files were changed.";
        return "No recognized Shard executable (enbu_ap.exe or " +
                JAPANESE_EXECUTABLE + ") was found in this active " +
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

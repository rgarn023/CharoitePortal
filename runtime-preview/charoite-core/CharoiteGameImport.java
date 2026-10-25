package com.charoitegames.core;

import android.content.Context;
import android.net.Uri;
import androidx.documentfile.provider.DocumentFile;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Reusable Charoite Core Windows-game acquisition.
 *
 * The caller provides an app-private Wine container directory; Core handles
 * safe SAF copy, executable selection and classification, and explicit launch
 * policy. Touhou's established C:\TouhouPocket storage is preserved.
 *
 * IMPORTANT: no import method executes an .exe; the host may launch ONLY
 * when shouldLaunchAfterImport() returns true for an explicit installer action.
 */
public final class CharoiteGameImport {
    private static final long MAX_BYTES = 6L * 1024 * 1024 * 1024;
    private static final int MAX_FILES = 12000;
    private static final int MAX_DEPTH = 12;
    private static final int MAX_EXES = 150;
    private static final AtomicLong UNIQUE = new AtomicLong();

    public enum Selection {
        GAME_FOLDER, STANDALONE_INSTALLER, INSTALLER_FOLDER
    }

    public static final class Result {
        public final String executablePath;
        public final String executableName;
        public final boolean installer;
        public final int fileCount;
        public final Selection selection;

        private Result(String path, String name, boolean installer, int files, Selection selection) {
            this.executablePath = path;
            this.executableName = name;
            this.installer = installer;
            this.fileCount = files;
            this.selection = selection;
        }
    }

    private CharoiteGameImport() {}

    /**
     * Folder selection is **always import-only**, even if the only executable
     * found is setup.exe. Standalone installer selection is an explicit request
     * to launch an installer after successful import and registration.
     */
    public static boolean shouldLaunchAfterImport(Selection selection) {
        return selection == Selection.STANDALONE_INSTALLER;
    }

    public static boolean isLikelyInstaller(String path) {
        if (path == null) return false;
        String filename = new File(path).getName().toLowerCase(Locale.ROOT);
        return filename.equals("setup.exe") || filename.startsWith("setup_") ||
                filename.startsWith("install") || filename.contains("installer");
    }

    public static Result importSelected(Context host, Uri selectedUri, Selection selection,
                                        File containerRoot, boolean touhou) throws Exception {
        if (host == null || selectedUri == null || selection == null || containerRoot == null)
            throw new IllegalArgumentException("Invalid game import request");
        File directory = new File(containerRoot,
                touhou ? ".wine/drive_c/TouhouPocket" : ".wine/drive_c/CharoitePortal");
        if (!directory.isDirectory() && !directory.mkdirs())
            throw new IllegalStateException("Unable to create game storage directory");
        File target = new File(directory,
                "game-" + System.currentTimeMillis() + "-" + UNIQUE.incrementAndGet());
        if (!target.mkdir()) throw new IllegalStateException("Could not create a game import directory");
        try {
            Counter counter = new Counter();
            if (selection == Selection.GAME_FOLDER || selection == Selection.INSTALLER_FOLDER) {
                DocumentFile tree = DocumentFile.fromTreeUri(host, selectedUri);
                if (tree == null || !tree.isDirectory())
                    throw new IllegalArgumentException("Select a complete Windows game or installer folder");
                copyFolder(host, tree, target, counter, 0);
            } else {
                DocumentFile file = DocumentFile.fromSingleUri(host, selectedUri);
                String filename = file == null ? null : file.getName();
                if (filename == null || !filename.toLowerCase(Locale.ROOT).endsWith(".exe"))
                    throw new IllegalArgumentException("Select a Windows .exe installer");
                copyFile(host, selectedUri, new File(target, safeName(filename)), counter);
            }
            String executable = detectExe(target, selection, touhou);
            if (executable == null)
                throw new IllegalArgumentException("No Windows executable found in selected files");
            File exe = new File(target, executable);
            boolean installer = selection == Selection.STANDALONE_INSTALLER ||
                    selection == Selection.INSTALLER_FOLDER || isLikelyInstaller(executable);
            return new Result(exe.getAbsolutePath(), exe.getName(), installer,
                    counter.files, selection);
        } catch (Exception failure) {
            // Only the new, dedicated import directory may be discarded.
            // Never touch the user's previously imported games or saved data.
            deleteNewImport(target);
            throw failure;
        }
    }

    private static final class Counter {
        int files;
        long bytes;
    }

    private static void copyFolder(Context host, DocumentFile source, File target,
                                   Counter counter, int depth) throws Exception {
        if (depth > MAX_DEPTH) throw new IllegalArgumentException("Game folder is too deeply nested");
        for (DocumentFile child : source.listFiles()) {
            String name = safeName(child.getName());
            File next = new File(target, name);
            if (!next.getCanonicalPath().startsWith(target.getCanonicalPath() + File.separator))
                throw new IllegalArgumentException("Unsafe filename in game folder");
            if (child.isDirectory()) {
                if (!next.mkdir()) throw new IllegalStateException("Duplicate or inaccessible folder: " + name);
                copyFolder(host, child, next, counter, depth + 1);
            } else if (child.isFile()) {
                copyFile(host, child.getUri(), next, counter);
            }
        }
    }

    private static void copyFile(Context host, Uri uri, File target, Counter counter) throws Exception {
        if (++counter.files > MAX_FILES)
            throw new IllegalArgumentException("Game exceeds file count limit");
        try (InputStream in = host.getContentResolver().openInputStream(uri)) {
            if (in == null) throw new IllegalArgumentException("Cannot read selected file");
            try (FileOutputStream out = new FileOutputStream(target)) {
                byte[] buffer = new byte[65536];
                int count;
                while ((count = in.read(buffer)) != -1) {
                    counter.bytes += count;
                    if (counter.bytes > MAX_BYTES)
                        throw new IllegalArgumentException("Game exceeds 6 GB import limit");
                    out.write(buffer, 0, count);
                }
            }
        }
    }

    private static String safeName(String name) {
        if (name == null || name.length() == 0 || name.equals(".") || name.equals("..")
                || name.contains("/") || name.contains("\\") || name.indexOf('\0') >= 0)
            throw new IllegalArgumentException("Unsupported filename in imported game");
        return name;
    }

    private static String detectExe(File root, Selection selection, boolean touhou) {
        List<String> matches = new ArrayList<>();
        collectExecutables(root, root, matches, 0);
        if (matches.isEmpty()) return null;
        if (selection == Selection.STANDALONE_INSTALLER) return matches.get(0);
        if (selection == Selection.INSTALLER_FOLDER) {
            // Prioritize setup over playable binaries, while keeping all
            // companion installation archives and directories alongside it.
            for (String name : new String[]{"setup.exe", "install.exe", "installer.exe"}) {
                String preferred = null;
                for (String candidate : matches)
                    if (new File(candidate).getName().equalsIgnoreCase(name) &&
                            (preferred == null || candidate.length() < preferred.length()))
                        preferred = candidate;
                if (preferred != null) return preferred;
            }
            String preferred = null;
            for (String candidate : matches)
                if (isLikelyInstaller(candidate) &&
                        (preferred == null || candidate.length() < preferred.length()))
                    preferred = candidate;
            if (preferred == null) throw new IllegalArgumentException(
                    "No setup.exe or installer found in selected folder");
            return preferred;
        }
        if (touhou) {
            for (String priority : new String[]{
                    "enbu_ap.exe", "gn_enbu.exe", "th20.exe", "th19.exe"}) {
                for (String candidate : matches)
                    if (new File(candidate).getName().equalsIgnoreCase(priority))
                        return candidate;
            }
            for (String candidate : matches) {
                String filename = new File(candidate).getName().toLowerCase(Locale.ROOT);
                if (filename.matches("th(0[6-9]|1[0-9]|20)\\.exe"))
                    return candidate;
            }
        }
        // Mixed folders: take a playable executable rather than setup.exe.
        for (String candidate : matches)
            if (!isLikelyInstaller(candidate)) return candidate;
        return matches.get(0);
    }

    private static void collectExecutables(File root, File directory,
                                           List<String> matches, int depth) {
        if (depth > MAX_DEPTH || matches.size() >= MAX_EXES) return;
        File[] files = directory.listFiles();
        if (files == null) return;
        for (File file : files) {
            if (java.nio.file.Files.isSymbolicLink(file.toPath())) continue;
            if (file.isDirectory()) collectExecutables(root, file, matches, depth + 1);
            else if (file.getName().toLowerCase(Locale.ROOT).endsWith(".exe")) {
                String relative = file.getAbsolutePath().substring(root.getAbsolutePath().length() + 1);
                matches.add(relative);
            }
            if (matches.size() >= MAX_EXES) break;
        }
    }

    private static void deleteNewImport(File root) {
        File[] files = root.listFiles();
        if (files != null) for (File file : files) deleteNewImport(file);
        root.delete();
    }
}

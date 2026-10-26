package com.charoitegames.core;

import androidx.appcompat.app.AppCompatActivity;
import com.winlator.container.Container;
import com.winlator.container.ContainerManager;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.ArrayDeque;

/** Deliberately bounded game-folder deletion. Never resets Wine or user profiles. */
public final class CharoiteGameRemoval {
    private CharoiteGameRemoval() {}
    private static final int MAX_VISITED = 200000;

    /** Preview exact directory for a second destructive confirmation. */
    public static File safeGameFolder(AppCompatActivity host, int containerId,
                                      String executable) throws IOException {
        if (containerId <= 0 || executable == null || executable.isEmpty())
            throw new IOException("No active Windows game selected");
        Container container = new ContainerManager(host).getContainerById(containerId);
        if (container == null) throw new IOException("Selected Wine container not found");
        File drive = new File(container.getRootDir(), ".wine/drive_c").getCanonicalFile();
        File exe = new File(executable);
        if (!exe.isFile() || Files.isSymbolicLink(exe.toPath()))
            throw new IOException("Executable is missing or is a symbolic link");
        File folder = exe.getParentFile();
        if (folder == null || !folder.isDirectory() ||
                Files.isSymbolicLink(folder.toPath()))
            throw new IOException("Game installation folder missing");
        // Check every ancestor for symbolic links; do not follow links out of
        // the private Wine C: drive into rootfs or shared Android storage.
        for (File ancestor = folder; ancestor != null &&
                !ancestor.equals(drive); ancestor = ancestor.getParentFile())
            if (Files.isSymbolicLink(ancestor.toPath()))
                throw new IOException("Cannot delete through a symbolic link");
        File target = folder.getCanonicalFile();
        if (!target.toPath().startsWith(drive.toPath()))
            throw new IOException("Selected game is not inside this Wine C: drive");
        File relative = drive.toPath().relativize(target.toPath()).toFile();
        int depth = drive.toPath().relativize(target.toPath()).getNameCount();
        if (depth < 2) throw new IOException(
                "Refusing to delete a C: drive top-level/system folder");
        String first = drive.toPath().relativize(target.toPath())
                .getName(0).toString().toLowerCase(java.util.Locale.ROOT);
        if ("windows".equals(first) || "users".equals(first) ||
                "system32".equals(first) || "programdata".equals(first) ||
                "dosdevices".equals(first))
            throw new IOException("Windows system/user folders cannot be deleted");
        if (!new File(target, exe.getName()).isFile())
            throw new IOException("Executable is outside its installation folder");
        // Reject another registered game OR installer under the folder. Do
        // not remove shared assets of another Library item.
        JSONArray registered = CharoiteGameLibrary.load(host);
        for (int i = 0; i < registered.length(); i++) {
            JSONObject other = registered.optJSONObject(i);
            if (other == null) continue;
            String candidate = other.optString("path", "");
            if (candidate.isEmpty() || candidate.equals(executable)) continue;
            File another = new File(candidate).getCanonicalFile();
            if (another.toPath().startsWith(target.toPath()))
                throw new IOException("Another registered game or installer shares this folder. Remove only the Library entry.");
        }
        return target;
    }

    /** Delete only after explicit user confirmation. Caller removes metadata on success. */
    public static void deleteGameFolder(AppCompatActivity host, int containerId,
                                        String executable) throws IOException {
        File root = safeGameFolder(host, containerId, executable);
        ArrayDeque<File> pending = new ArrayDeque<>();
        ArrayDeque<File> ordered = new ArrayDeque<>();
        pending.add(root);
        int count = 0;
        while (!pending.isEmpty()) {
            File entry = pending.removeLast();
            if (++count > MAX_VISITED)
                throw new IOException("Game has too many files; use an installer or Windows uninstaller");
            if (Files.isSymbolicLink(entry.toPath())) {
                // A contained symlink itself may be removed safely; never
                // traverse it or follow it to the target.
                ordered.addLast(entry);
                continue;
            }
            if (!entry.getCanonicalFile().toPath().startsWith(root.toPath()))
                throw new IOException("Folder unexpectedly escaped the selected game");
            ordered.addLast(entry);
            if (entry.isDirectory()) {
                File[] children = entry.listFiles();
                if (children == null) throw new IOException("Cannot inspect game directory");
                for (File child : children) pending.add(child);
            }
        }
        while (!ordered.isEmpty()) {
            File item = ordered.removeLast();
            if (!item.delete())
                throw new IOException("Could not remove " + item.getName() +
                        ". The game remains in Library so deletion can be retried.");
        }
    }
}

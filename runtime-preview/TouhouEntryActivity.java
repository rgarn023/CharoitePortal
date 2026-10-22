package com.winlator;

import android.app.Activity;
import android.content.Intent;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.documentfile.provider.DocumentFile;

import com.winlator.container.Container;
import com.winlator.container.ContainerManager;
import com.winlator.container.GraphicsDrivers;
import com.winlator.container.DXWrappers;
import com.winlator.box64.Box64Preset;
import com.winlator.core.DefaultVersion;
import androidx.preference.PreferenceManager;
import com.winlator.core.TarCompressorUtils;
import com.winlator.xenvironment.RootFS;
import com.winlator.xenvironment.RootFSInstaller;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.Locale;
import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;

/**
 * Touhou-first Android entry point. All game operations happen through this
 * screen; the original Winlator settings/container manager isn't launched.
 *
 * The compatible XServerDisplayActivity remains the game rendering backend.
 */
public final class TouhouEntryActivity extends AppCompatActivity {
    private static final int FOLDER_REQUEST = 1001;
    private static final int EXE_REQUEST = 1002;
    private static final int BG = 0xff101322;
    private static final int PANEL = 0xff222841;
    private static final int SECONDARY = 0xffc7cde3;
    private static final int ACCENT = 0xff8d67d9;
    private static final long MAX_GAME_BYTES = 6L * 1024 * 1024 * 1024;
    private static final int MAX_FILES = 12000;

    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private TextView statusText;
    private LinearLayout libraryArea;
    private LinearLayout main;
    private Button initButton;
    private Button folderButton;
    private Button installerButton;
    private Button scanButton;
    private Button compatButton;
    private Button diagnosticButton;
    private boolean busy = false;
    private int containerId = 0;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        render();
        refreshReadyState();
    }

    @Override public void onDestroy() {
        super.onDestroy();
        worker.shutdown();
    }

    private void render() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);
        main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);
        main.setPadding(dp(20), dp(30), dp(20), dp(35));
        scroll.addView(main);
        setContentView(scroll);

        main.addView(label("CHAROITE GAMES", 12, 0xffc09cff, true));
        main.addView(label("Touhou Pocket", 29, Color.WHITE, true));
        main.addView(label("YOUR GAMES. ONE LIBRARY.", 12, SECONDARY, false));
        spacer(20);

        LinearLayout info = new LinearLayout(this);
        info.setOrientation(LinearLayout.VERTICAL);
        info.setPadding(dp(14), dp(15), dp(14), dp(15));
        info.setBackgroundColor(PANEL);
        info.addView(label("Game Engine", 18, Color.WHITE, true));
        statusText = label("Checking Windows compatibility engine…", 13, SECONDARY, false);
        info.addView(statusText);
        main.addView(info);
        spacer(12);

        initButton = button("SET UP GAME ENGINE", this::startSetup);
        main.addView(initButton);
        folderButton = button("IMPORT GAME FOLDER", () -> {
            Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
            picker.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            startActivityForResult(picker, FOLDER_REQUEST);
        });
        installerButton = button("IMPORT SINGLE-FILE INSTALLER (.EXE)", () -> {
            Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            picker.addCategory(Intent.CATEGORY_OPENABLE);
            picker.setType("*/*");
            startActivityForResult(picker, EXE_REQUEST);
        });
        main.addView(folderButton);
        main.addView(installerButton);
        scanButton = button("FIND INSTALLED TOUHOU GAMES", this::findInstalledGames);
        main.addView(scanButton);
        compatButton = button("SWITCH TO COMPATIBILITY GRAPHICS", this::toggleCompatibility);
        main.addView(compatButton);
        diagnosticButton = button("VIEW LAST LAUNCH DIAGNOSTICS", this::showDiagnostics);
        main.addView(diagnosticButton);
        spacer(20);

        main.addView(label("YOUR TOUHOU LIBRARY", 19, Color.WHITE, true));
        libraryArea = new LinearLayout(this);
        libraryArea.setOrientation(LinearLayout.VERTICAL);
        main.addView(libraryArea);
        spacer(18);
        main.addView(label("Puppet Dance Performance • Shard of Dreams • other Windows Touhou titles",
                12, SECONDARY, false));
        spacer(12);
        main.addView(label(
                "To install games that include data files alongside setup.exe, choose Import Game Folder (not Single-File Installer). " +
                "Shard of Dreams / Extended and automatic English patches are still under development. " +
                "Games and translations are not included; import files you own.",
                12, 0xffa3abc4, false));
        main.addView(label("Powered by licensed Wine/Box64 components. Runtime acknowledgments: github.com/brunodev85/winlator-app",
                11, 0xffa3abc4, false));
        refreshLibrary();
    }

    private void refreshReadyState() {
        RootFS root = RootFS.find(this);
        if (!root.isValid()) {
            containerId = 0;
            setStatus("Setup required: install the built-in game engine once.");
        } else if (root.getVersion() < RootFSInstaller.LATEST_VERSION) {
            containerId = 0;
            setStatus("Engine needs an update. Tap Set Up Game Engine.");
        } else {
            try {
                ContainerManager manager = new ContainerManager(this);
                Container selected = getActiveContainer(manager);
                containerId = selected != null ? selected.id : 0;
                setStatus(selected == null ?
                        "Engine installed. Tap Set Up Game Engine to prepare your game environment." :
                        "Engine ready. Import a game folder or EXE, then tap Play.");
            } catch (Exception ex) {
                containerId = 0;
                setStatus("Engine check failed: " + ex.getMessage());
            }
        }
        updateButtons();
    }

    private void updateButtons() {
        RootFS root = RootFS.find(this);
        boolean ready = root.isValid() && root.getVersion() >= RootFSInstaller.LATEST_VERSION && containerId > 0;
        initButton.setEnabled(!busy);
        folderButton.setEnabled(!busy && ready);
        installerButton.setEnabled(!busy && ready);
        scanButton.setEnabled(!busy && ready);
        compatButton.setEnabled(!busy && ready);
        compatButton.setText(getPreferences(MODE_PRIVATE).getBoolean("compat_graphics", false) ?
                "RESTORE NORMAL GRAPHICS" : "SWITCH TO COMPATIBILITY GRAPHICS");
        diagnosticButton.setEnabled(!busy);
        refreshLibrary();
    }

    private Container getActiveContainer(ContainerManager manager) {
        int saved = getPreferences(MODE_PRIVATE).getInt("touhou_container", 0);
        Container container = saved > 0 ? manager.getContainerById(saved) : null;
        if (container == null && !manager.getContainers().isEmpty())
            container = manager.getContainers().get(0);
        return container;
    }


    /** Preferences adjust only this app's private game environment. */
    private void toggleCompatibility() {
        if (busy || containerId <= 0) return;
        try {
            boolean compatible = !getPreferences(MODE_PRIVATE).getBoolean("compat_graphics", false);
            Container current = new ContainerManager(this).getContainerById(containerId);
            if (current == null) throw new IllegalStateException("Windows game environment missing");
            current.setGraphicsDriver(compatible ?
                GraphicsDrivers.VORTEK + "," + GraphicsDrivers.VIRGL :
                GraphicsDrivers.getDefaultDriver(this));
            current.setDXWrapper(compatible ? DXWrappers.WINED3D : Container.DEFAULT_DXWRAPPER);
            current.setBox64Preset(compatible ? Box64Preset.CONSERVATIVE : Box64Preset.STABILITY);
            current.setScreenSize(compatible ? "800x600" : "1280x720");
            current.saveData();
            getPreferences(MODE_PRIVATE).edit().putBoolean("compat_graphics", compatible).apply();
            updateButtons();
            setStatus(compatible ?
                "Compatibility graphics enabled (Vortek/VirGL, WineD3D, conservative Box64). Try Play again." :
                "Normal graphics restored. Try Play again.");
        } catch (Exception e) {
            setStatus("Could not change graphics mode: " + e.getMessage());
        }
    }

    /** Diagnostic details remain on-device until the user explicitly copies them. */
    private void showDiagnostics() {
        final String report = TouhouDiagnostics.getReport(this);
        new androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("Touhou startup diagnostics")
            .setMessage(report)
            .setPositiveButton("Copy report", (dialog, which) -> {
                ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                clipboard.setPrimaryClip(ClipData.newPlainText("Touhou startup report", report));
                setStatus("Startup report copied. Share the error text for troubleshooting.");
            })
            .setNegativeButton("Close", null)
            .show();
    }

    private void startSetup() {
        if (busy) return;
        busy = true;
        setStatus("Preparing private Windows game engine. This may use substantial storage.");
        updateButtons();
        worker.execute(() -> {
            try {
                RootFS root = RootFS.find(this);
                if (!root.isValid() || root.getVersion() < RootFSInstaller.LATEST_VERSION) {
                    SettingsFragment.resetPreferenceVersions(this);
                    PreferenceManager.getDefaultSharedPreferences(this).edit()
                        .putString("box64_version", DefaultVersion.BOX64)
                        .remove("current_box64_version").apply();
                    File rootDir = root.getRootDir();
                    if (!rootDir.isDirectory() && !rootDir.mkdirs())
                        throw new IllegalStateException("Cannot create private engine storage");
                    boolean ok = TarCompressorUtils.extract(TarCompressorUtils.Type.ZSTD, this,
                            "rootfs.tzst", rootDir);
                    if (!ok) throw new IllegalStateException("Could not extract Windows engine resources");
                    root.createRFSVersionFile(RootFSInstaller.LATEST_VERSION);
                    if (!root.isValid()) throw new IllegalStateException("Engine verification failed");
                }
                runOnUiThread(this::ensureGameEnvironment);
            } catch (Exception ex) {
                runOnUiThread(() -> finishOperation("Setup failed: " + ex.getMessage()));
            }
        });
    }

    private void ensureGameEnvironment() {
        setStatus("Creating game environment…");
        try {
            ContainerManager manager = new ContainerManager(this);
            Container existing = getActiveContainer(manager);
            if (existing != null) {
                containerId = existing.id;
                finishOperation("Touhou game engine ready. Import a game to play.");
                return;
            }
            JSONObject profile = new JSONObject();
            profile.put("name", "Touhou Games");
            boolean conservative = getPreferences(MODE_PRIVATE).getBoolean("compat_graphics", false);
            profile.put("screenSize", conservative ? "800x600" : "1280x720");
            profile.put("graphicsDriver", conservative ?
                GraphicsDrivers.VORTEK + "," + GraphicsDrivers.VIRGL :
                GraphicsDrivers.getDefaultDriver(this));
            profile.put("dxwrapper", conservative ? DXWrappers.WINED3D : Container.DEFAULT_DXWRAPPER);
            profile.put("box64Preset", conservative ? Box64Preset.CONSERVATIVE : Box64Preset.STABILITY);
            profile.put("audioDriver", Container.DEFAULT_AUDIO_DRIVER);
            manager.createContainerAsync(profile, container -> {
                if (isFinishing() || isDestroyed()) return;
                if (container == null) {
                    finishOperation("Game environment creation failed; retry setup.");
                } else {
                    containerId = container.id;
                    getPreferences(MODE_PRIVATE).edit().putInt("touhou_container", containerId).apply();
                    finishOperation("Game engine ready. Import a game to play.");
                }
            });
        } catch (Exception ex) {
            finishOperation("Game setup failed: " + ex.getMessage());
        }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != Activity.RESULT_OK || data == null || data.getData() == null) return;
        Uri uri = data.getData();
        if (requestCode == FOLDER_REQUEST) importGame(uri, true);
        else if (requestCode == EXE_REQUEST) importGame(uri, false);
    }


    /**
     * An imported Windows installer may install into Program Files, not our
     * import folder. Recognize installed game executables inside C: without
     * making users browse the Windows desktop or container manager.
     */
    private void findInstalledGames() {
        if (busy || containerId <= 0) return;
        busy = true;
        setStatus("Searching for installed Touhou games…");
        updateButtons();
        worker.execute(() -> {
            try {
                Container current = new ContainerManager(this).getContainerById(containerId);
                if (current == null) throw new IllegalStateException("Game environment missing");
                File drive = new File(current.getRootDir(), ".wine/drive_c");
                if (!drive.isDirectory()) throw new IllegalStateException("Windows game directory is not ready");
                List<File> matches = new ArrayList<>();
                int[] visited = {0};
                scanInstalled(drive, drive, matches, 0, visited);

                JSONArray library = loadLibrary();
                Set<String> existing = new HashSet<>();
                for (int i = 0; i < library.length(); i++) {
                    JSONObject entry = library.optJSONObject(i);
                    if (entry != null) existing.add(entry.optString("path"));
                }
                int added = 0;
                for (File game : matches) {
                    if (!existing.add(game.getAbsolutePath())) continue;
                    JSONObject entry = new JSONObject();
                    entry.put("name", gameName(game.getName()));
                    entry.put("path", game.getAbsolutePath());
                    entry.put("installer", false);
                    entry.put("files", 0);
                    library.put(entry);
                    added++;
                }
                getPreferences(MODE_PRIVATE).edit().putString("game_library", library.toString()).commit();
                final int newGames = added;
                runOnUiThread(() -> finishOperation(
                    newGames == 0 ? "No new supported games found. Import a complete game folder or run an installer." :
                    "Found " + newGames + " new game(s). Tap Play in your library."));
            } catch (Exception e) {
                runOnUiThread(() -> finishOperation("Game search failed: " + e.getMessage()));
            }
        });
    }

    private void scanInstalled(File driveRoot, File folder, List<File> matches, int depth, int[] visited) {
        if (depth > 14 || visited[0] >= 25000 || matches.size() >= 100) return;
        File[] children = folder.listFiles();
        if (children == null) return;
        for (File file : children) {
            if (++visited[0] > 25000) break;
            if (java.nio.file.Files.isSymbolicLink(file.toPath())) continue;
            if (!file.getAbsolutePath().startsWith(driveRoot.getAbsolutePath() + File.separator)) continue;
            String name = file.getName().toLowerCase(Locale.ROOT);
            if (file.isDirectory()) {
                if (name.equals("windows") || name.equals("programdata") || name.equals("$recycle.bin")) continue;
                scanInstalled(driveRoot, file, matches, depth + 1, visited);
            } else if (file.isFile()) {
                if (name.equals("gn_enbu.exe") || name.equals("enbu_ap.exe") ||
                    name.matches("th(0[6-9]|1[0-9]|20)\\.exe"))
                    matches.add(file);
            }
        }
    }

    private void importGame(Uri uri, boolean folder) {
        if (busy || containerId <= 0) return;
        busy = true;
        setStatus(folder ? "Copying game folder into Touhou library…" : "Importing EXE installer…");
        updateButtons();
        worker.execute(() -> {
            File destination = null;
            try {
                Container current = new ContainerManager(this).getContainerById(containerId);
                if (current == null) throw new IllegalStateException("Game environment missing");
                File gameBase = new File(current.getRootDir(), ".wine/drive_c/TouhouPocket");
                if (!gameBase.isDirectory() && !gameBase.mkdirs())
                    throw new IllegalStateException("Unable to create game library storage");
                destination = new File(gameBase, "game-" + System.currentTimeMillis());
                if (!destination.mkdir()) throw new IllegalStateException("Game directory already exists");
                int count;
                if (folder) {
                    DocumentFile source = DocumentFile.fromTreeUri(this, uri);
                    if (source == null || !source.isDirectory())
                        throw new IllegalArgumentException("Please select a game folder");
                    Counter counter = new Counter();
                    copyFolder(source, destination, counter, 0);
                    count = counter.files;
                } else {
                    DocumentFile file = DocumentFile.fromSingleUri(this, uri);
                    String name = file != null ? file.getName() : null;
                    if (name == null || !name.toLowerCase(Locale.ROOT).endsWith(".exe"))
                        throw new IllegalArgumentException("Select a Windows .exe installer");
                    writeFile(uri, new File(destination, safeName(name)), new Counter());
                    count = 1;
                }
                String executable = detectExe(destination, !folder);
                if (executable == null)
                    throw new IllegalArgumentException("No executable found in selected game files");
                File exe = new File(destination, executable);
                JSONObject entry = new JSONObject();
                boolean installer = !folder || isLikelyInstaller(executable);
                entry.put("name", installer ? "Windows installer: " + new File(executable).getName() : gameName(executable));
                entry.put("path", exe.getAbsolutePath());
                entry.put("installer", installer);
                entry.put("files", count);
                saveEntry(entry);
                runOnUiThread(() -> finishOperation("Imported successfully. Select Play from your library."));
            } catch (Exception ex) {
                if (destination != null) deleteTree(destination);
                runOnUiThread(() -> finishOperation("Import failed: " + ex.getMessage()));
            }
        });
    }

    private static final class Counter { long bytes; int files; }

    private void copyFolder(DocumentFile source, File target, Counter counter, int depth) throws Exception {
        if (depth > 12) throw new IllegalArgumentException("Game folder is too deeply nested");
        for (DocumentFile child : source.listFiles()) {
            String name = safeName(child.getName());
            File to = new File(target, name);
            if (!to.getCanonicalPath().startsWith(target.getCanonicalPath() + File.separator))
                throw new IllegalArgumentException("Unsafe filename in game folder");
            if (child.isDirectory()) {
                if (!to.mkdir()) throw new IllegalStateException("Duplicate or inaccessible game folder: " + name);
                copyFolder(child, to, counter, depth + 1);
            } else if (child.isFile()) {
                writeFile(child.getUri(), to, counter);
            }
        }
    }

    private void writeFile(Uri uri, File target, Counter counter) throws Exception {
        counter.files++;
        if (counter.files > MAX_FILES)
            throw new IllegalArgumentException("Game exceeds file count limit");
        try (InputStream input = getContentResolver().openInputStream(uri)) {
            if (input == null) throw new IllegalArgumentException("Cannot read selected file");
            try (FileOutputStream out = new FileOutputStream(target)) {
                byte[] buffer = new byte[65536];
                int n;
                while ((n = input.read(buffer)) != -1) {
                    counter.bytes += n;
                    if (counter.bytes > MAX_GAME_BYTES)
                        throw new IllegalArgumentException("Game exceeds 6 GB import limit");
                    out.write(buffer, 0, n);
                }
            }
        }
    }

    private String safeName(String original) {
        if (original == null || original.isEmpty() || original.equals(".") || original.equals("..")
                || original.contains("/") || original.contains("\\") || original.indexOf('\0') >= 0)
            throw new IllegalArgumentException("Unsupported filename in imported game");
        return original;
    }

    private String detectExe(File root, boolean installer) {
        List<String> candidates = new ArrayList<>();
        collectExecutables(root, root, candidates, 0);
        if (candidates.isEmpty()) return null;
        if (installer) return candidates.get(0);
        for (String priority : new String[]{"enbu_ap.exe", "gn_enbu.exe", "th20.exe", "th19.exe"}) {
            for (String value : candidates)
                if (new File(value).getName().equalsIgnoreCase(priority)) return value;
        }
        for (String value : candidates) {
            String n = new File(value).getName().toLowerCase(Locale.ROOT);
            if (n.matches("th(0[6-9]|1[0-9]|20)\\.exe")) return value;
        }
        for (String value : candidates) {
            if (isLikelyInstaller(value)) return value;
        }
        return candidates.get(0);
    }

    private boolean isLikelyInstaller(String path) {
        String name = new File(path).getName().toLowerCase(Locale.ROOT);
        return name.equals("setup.exe") || name.startsWith("setup_") ||
            name.startsWith("install") || name.contains("installer");
    }

    private void collectExecutables(File root, File folder, List<String> matches, int depth) {
        if (depth > 12 || matches.size() > 150) return;
        File[] files = folder.listFiles();
        if (files == null) return;
        for (File file : files) {
            if (file.isDirectory()) collectExecutables(root, file, matches, depth + 1);
            else if (file.getName().toLowerCase(Locale.ROOT).endsWith(".exe")) {
                String rel = file.getAbsolutePath().substring(root.getAbsolutePath().length() + 1);
                matches.add(rel);
            }
        }
    }

    private String gameName(String executable) {
        String value = new File(executable).getName().toLowerCase(Locale.ROOT);
        if (value.equals("enbu_ap.exe")) return "Touhou Puppet Dance Performance: Shard of Dreams";
        if (value.equals("gn_enbu.exe")) return "Touhou Puppet Dance Performance";
        return "Touhou game: " + new File(executable).getName();
    }

    private synchronized void saveEntry(JSONObject entry) throws Exception {
        JSONArray library = loadLibrary();
        library.put(entry);
        getPreferences(MODE_PRIVATE).edit().putString("game_library", library.toString()).commit();
    }

    private JSONArray loadLibrary() {
        try {
            return new JSONArray(getPreferences(MODE_PRIVATE).getString("game_library", "[]"));
        } catch (Exception badLibrary) {
            return new JSONArray();
        }
    }

    private void refreshLibrary() {
        if (libraryArea == null) return;
        libraryArea.removeAllViews();
        JSONArray library = loadLibrary();
        if (library.length() == 0) {
            libraryArea.addView(label("No games imported yet. Use Import Game Folder to add one.", 13, SECONDARY, false));
            return;
        }
        for (int i = 0; i < library.length(); i++) {
            JSONObject game = library.optJSONObject(i);
            if (game == null) continue;
            LinearLayout item = new LinearLayout(this);
            item.setOrientation(LinearLayout.VERTICAL);
            item.setPadding(dp(12), dp(12), dp(12), dp(12));
            item.setBackgroundColor(PANEL);
            String path = game.optString("path", "");
            String name = game.optString("name", "Imported game");
            item.addView(label(name, 16, Color.WHITE, true));
            item.addView(label(game.optInt("files", 0) + " files · " +
                    (game.optBoolean("installer") ? "Windows installer" : "Game folder"), 12, SECONDARY, false));
            Button play = button(game.optBoolean("installer") ? "RUN INSTALLER" : "PLAY",
                    () -> launchGame(path));
            play.setEnabled(!busy && containerId > 0);
            item.addView(play);
            libraryArea.addView(item);
            spacerIn(libraryArea, 10);
        }
    }

    private void launchGame(String path) {
        if (busy || containerId <= 0) return;
        if (!new File(path).isFile()) {
            setStatus("Game file is missing. Re-import the game.");
            return;
        }
        Intent play = new Intent(this, XServerDisplayActivity.class);
        play.putExtra("container_id", containerId);
        play.putExtra("exec_path", path);
        startActivity(play);
    }

    private static void deleteTree(File path) {
        File[] children = path.listFiles();
        if (children != null) for (File child : children) deleteTree(child);
        path.delete();
    }

    private void finishOperation(String message) {
        busy = false;
        setStatus(message);
        refreshReadyState();
        // Preserve the meaningful operation result instead of overwriting with generic ready text.
        setStatus(message);
    }

    private void setStatus(String message) {
        if (statusText != null) statusText.setText(message);
    }

    private Button button(String name, Runnable action) {
        Button button = new Button(this);
        button.setText(name);
        button.setAllCaps(false);
        button.setTextColor(Color.WHITE);
        button.setBackgroundTintList(ColorStateList.valueOf(ACCENT));
        button.setOnClickListener(view -> action.run());
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.topMargin = dp(8);
        button.setLayoutParams(params);
        return button;
    }

    private TextView label(String value, int size, int color, boolean strong) {
        TextView text = new TextView(this);
        text.setText(value);
        text.setTextColor(color);
        text.setTextSize(size);
        text.setLineSpacing(dp(4), 1f);
        if (strong) text.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return text;
    }

    private void spacer(int height) { spacerIn(main, height); }
    private void spacerIn(LinearLayout parent, int height) {
        View view = new View(this);
        view.setLayoutParams(new LinearLayout.LayoutParams(1, dp(height)));
        parent.addView(view);
    }
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
}
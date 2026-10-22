package com.winlator;

import android.app.Activity;
import android.content.Intent;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.widget.ImageView;
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
    // Shrine-red, ink-purple and sakura. No external image or copyrighted art.
    private static final int BG = 0xff120F18;
    private static final int PANEL = 0xff241C2A;
    private static final int SECONDARY = 0xffCDBFC8;
    private static final int ACCENT = 0xffC93E62;
    private static final int GOLD = 0xffF4D9A9;
    private static final int SAKURA = 0xffF4ACC6;
    private static final int LINE = 0xff654153;
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
    private Button libraryTab;
    private Button importTab;
    private Button systemTab;
    private LinearLayout libraryScreen;
    private LinearLayout importScreen;
    private LinearLayout systemScreen;
    private ScrollView mainScroll;
    private TextView runtimeLabel;
    private boolean busy = false;
    private int containerId = 0;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        render();
        refreshReadyState();
        initializeEngineOnFirstLaunch();
    }

    @Override public void onDestroy() {
        super.onDestroy();
        worker.shutdown();
    }

    /** Touhou OS — mobile-first dashboard, distinct from the Wine runtime UI. */
    private void render() {
        mainScroll = new ScrollView(this);
        mainScroll.setFillViewport(true);
        mainScroll.setClipToPadding(false);
        mainScroll.setBackgroundColor(BG);
        main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);
        main.setPadding(dp(16), dp(18), dp(16), dp(30));
        mainScroll.addView(main);
        setContentView(mainScroll);

        TextView maker = label("C H A R O I T E   G A M E S", 11, GOLD, true);
        main.addView(maker);
        spacer(12);

        LinearLayout hero = new LinearLayout(this);
        hero.setGravity(Gravity.CENTER_VERTICAL);
        hero.setOrientation(LinearLayout.HORIZONTAL);
        hero.setPadding(dp(17), dp(16), dp(15), dp(16));
        hero.setBackground(heroBackground());
        LinearLayout.LayoutParams heroParams = new LinearLayout.LayoutParams(-1, -2);
        hero.setLayoutParams(heroParams);

        LinearLayout headline = new LinearLayout(this);
        headline.setOrientation(LinearLayout.VERTICAL);
        headline.addView(label("東方  •  幻想郷", 12, GOLD, true));
        headline.addView(label("TOUHOU OS", 31, Color.WHITE, true));
        headline.addView(label("Your gateway to Gensokyo", 13, 0xffF9D4DF, false));
        hero.addView(headline, new LinearLayout.LayoutParams(0, -2, 1f));

        ImageView brand = new ImageView(this);
        brand.setImageResource(R.drawable.touhou_pocket_icon);
        brand.setContentDescription("Touhou OS shrine and sakura emblem");
        brand.setScaleType(ImageView.ScaleType.FIT_CENTER);
        LinearLayout.LayoutParams imageParams = new LinearLayout.LayoutParams(dp(78), dp(78));
        imageParams.leftMargin = dp(6);
        hero.addView(brand, imageParams);
        main.addView(hero);
        spacer(12);

        LinearLayout engineStrip = card();
        engineStrip.addView(label("SYSTEM STATUS  •  WINE / BOX64", 11, GOLD, true));
        statusText = label("Checking Touhou game environment…", 13, Color.WHITE, false);
        engineStrip.addView(statusText);
        main.addView(engineStrip);
        spacer(15);

        LinearLayout tabs = new LinearLayout(this);
        tabs.setOrientation(LinearLayout.HORIZONTAL);
        tabs.setPadding(dp(3), dp(3), dp(3), dp(3));
        tabs.setBackground(rounded(0xff2B2030, 18, 0xff523548));
        libraryTab = tabButton("Library", () -> showSection(0));
        importTab = tabButton("Import", () -> showSection(1));
        systemTab = tabButton("System", () -> showSection(2));
        tabs.addView(libraryTab, tabParams());
        tabs.addView(importTab, tabParams());
        tabs.addView(systemTab, tabParams());
        main.addView(tabs);
        spacer(19);

        libraryScreen = new LinearLayout(this);
        libraryScreen.setOrientation(LinearLayout.VERTICAL);
        main.addView(libraryScreen);
        sectionTitle(libraryScreen, "YOUR LIBRARY", "Choose a game to play or install.");
        libraryArea = new LinearLayout(this);
        libraryArea.setOrientation(LinearLayout.VERTICAL);
        libraryScreen.addView(libraryArea);
        Button add = outlinedButton("＋  ADD TOUHOU GAME", () -> showSection(1));
        libraryScreen.addView(add);
        spacerIn(libraryScreen, 12);
        libraryScreen.addView(label("Games and installers are stored locally on your device.", 12, SECONDARY, false));

        importScreen = new LinearLayout(this);
        importScreen.setOrientation(LinearLayout.VERTICAL);
        main.addView(importScreen);
        sectionTitle(importScreen, "ADD A GAME", "Bring your existing Touhou games into your library.");

        LinearLayout folderCard = card();
        folderCard.addView(label("01   COMPLETE GAME FOLDER", 12, GOLD, true));
        folderCard.addView(label("Recommended for setups containing an EXE plus data files.", 13, SECONDARY, false));
        folderButton = button("IMPORT GAME FOLDER", () -> {
            Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
            picker.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            startActivityForResult(picker, FOLDER_REQUEST);
        });
        folderCard.addView(folderButton);
        importScreen.addView(folderCard);
        spacerIn(importScreen, 12);

        LinearLayout exeCard = card();
        exeCard.addView(label("02   SINGLE-FILE SETUP", 12, GOLD, true));
        exeCard.addView(label("For standalone Windows installers. The installer keeps its original destination.", 13, SECONDARY, false));
        installerButton = button("IMPORT SETUP.EXE", () -> {
            Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            picker.addCategory(Intent.CATEGORY_OPENABLE);
            picker.setType("*/*");
            startActivityForResult(picker, EXE_REQUEST);
        });
        exeCard.addView(installerButton);
        importScreen.addView(exeCard);
        spacerIn(importScreen, 12);

        LinearLayout scanCard = card();
        scanCard.addView(label("ALREADY INSTALLED?", 12, GOLD, true));
        scanCard.addView(label("Search the private Windows drive for supported Touhou games.", 13, SECONDARY, false));
        scanButton = outlinedButton("FIND INSTALLED GAMES", this::findInstalledGames);
        scanCard.addView(scanButton);
        importScreen.addView(scanCard);
        spacerIn(importScreen, 15);
        importScreen.addView(label("Games and translations are not included. Import copies you own.", 12, SECONDARY, false));

        systemScreen = new LinearLayout(this);
        systemScreen.setOrientation(LinearLayout.VERTICAL);
        main.addView(systemScreen);
        sectionTitle(systemScreen, "SYSTEM", "Runtime, graphics and troubleshooting.");

        LinearLayout runtimeCard = card();
        runtimeCard.addView(label("GAME ENGINE", 17, Color.WHITE, true));
        runtimeLabel = label("Checking your game environment…", 13, SECONDARY, false);
        runtimeCard.addView(runtimeLabel);
        initButton = button("SET UP GAME ENGINE", this::startSetup);
        runtimeCard.addView(initButton);
        runtimeCard.addView(outlinedButton("WHAT DOES GAME ENGINE SETUP DO?", this::showEngineInfo));
        systemScreen.addView(runtimeCard);
        spacerIn(systemScreen, 12);

        LinearLayout graphicsCard = card();
        graphicsCard.addView(label("DISPLAY & COMPATIBILITY", 16, Color.WHITE, true));
        graphicsCard.addView(label("Use compatibility graphics only when a game fails to display or launch correctly.", 12, SECONDARY, false));
        compatButton = outlinedButton("SWITCH TO COMPATIBILITY GRAPHICS", this::toggleCompatibility);
        graphicsCard.addView(compatButton);
        systemScreen.addView(graphicsCard);
        spacerIn(systemScreen, 12);

        LinearLayout debugCard = card();
        debugCard.addView(label("SUPPORT & DIAGNOSTICS", 16, Color.WHITE, true));
        debugCard.addView(label("Review local Windows launch information. Nothing is sent automatically.", 12, SECONDARY, false));
        diagnosticButton = outlinedButton("VIEW LAST LAUNCH DIAGNOSTICS", this::showDiagnostics);
        debugCard.addView(diagnosticButton);
        systemScreen.addView(debugCard);
        spacerIn(systemScreen, 18);
        systemScreen.addView(label("Touhou OS by Charoite Games. Uses Wine, Box64 and a modified, LGPL-licensed Winlator runtime. No games included.", 11, SECONDARY, false));

        refreshLibrary();
        showSection(RootFS.find(this).isValid() ? 0 : 2);
    }

    private void showEngineInfo() {
        new androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("What does Game Engine Setup do?")
            .setMessage("Touhou OS runs Windows Touhou games using Wine and Box64.\\n\\n" +
                "The engine sets up automatically on first launch. It unpacks the included compatibility runtime into private app storage, prepares its components, " +
                "and creates a local Windows environment with graphics, audio, and game settings.\\n\\n" +
                "This is normally a one-time operation and can require substantial storage. Future launches reuse existing game files. " +
                "It does not download or install Touhou games, translate them, or change their original installer destinations.\\n\\n" +
                "If automatic setup fails, use Retry Game Engine Setup under System.")
            .setPositiveButton("Got it", null)
            .show();
    }

    private void showSection(int section) {
        if (libraryScreen == null) return;
        libraryScreen.setVisibility(section == 0 ? View.VISIBLE : View.GONE);
        importScreen.setVisibility(section == 1 ? View.VISIBLE : View.GONE);
        systemScreen.setVisibility(section == 2 ? View.VISIBLE : View.GONE);
        styleTab(libraryTab, section == 0);
        styleTab(importTab, section == 1);
        styleTab(systemTab, section == 2);
        if (mainScroll != null) mainScroll.smoothScrollTo(0, 0);
    }

    private void sectionTitle(LinearLayout screen, String heading, String subtitle) {
        screen.addView(label(heading, 20, Color.WHITE, true));
        screen.addView(label(subtitle, 13, SECONDARY, false));
        spacerIn(screen, 13);
    }

    private LinearLayout.LayoutParams tabParams() {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, dp(48), 1f);
        params.setMargins(dp(2), 0, dp(2), 0);
        return params;
    }

    private Button tabButton(String title, Runnable action) {
        Button view = new Button(this);
        view.setText(title);
        view.setAllCaps(false);
        view.setTextSize(13);
        view.setMinHeight(0);
        view.setMinimumHeight(0);
        view.setPadding(dp(3), 0, dp(3), 0);
        view.setOnClickListener(v -> action.run());
        return view;
    }

    private void styleTab(Button tab, boolean selected) {
        if (tab == null) return;
        tab.setBackgroundTintList(null);
        tab.setTextColor(selected ? Color.WHITE : 0xffDBC4CE);
        tab.setTypeface(Typeface.DEFAULT, selected ? Typeface.BOLD : Typeface.NORMAL);
        tab.setBackground(rounded(selected ? ACCENT : 0xff2B2030, 14, selected ? ACCENT : 0xff2B2030));
    }

    private LinearLayout card() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(dp(16), dp(15), dp(16), dp(15));
        layout.setBackground(rounded(PANEL, 18, LINE));
        return layout;
    }

    private GradientDrawable rounded(int fill, int radius, int lineColor) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(fill);
        drawable.setCornerRadius(dp(radius));
        drawable.setStroke(dp(1), lineColor);
        return drawable;
    }

    private GradientDrawable heroBackground() {
        GradientDrawable drawable = new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{0xff70263E, 0xff3C1A3B, 0xff251631});
        drawable.setCornerRadius(dp(22));
        drawable.setStroke(dp(1), 0xffA05979);
        return drawable;
    }

    private Button outlinedButton(String name, Runnable action) {
        Button view = button(name, action);
        view.setBackground(rounded(0xff3C293B, 14, 0xff8E526B));
        view.setTextColor(0xffFFE9F0);
        return view;
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
        // Automatic setup on first launch; expose only a manual retry on failure.
        initButton.setVisibility(ready || busy ? View.GONE : View.VISIBLE);
        initButton.setText("RETRY GAME ENGINE SETUP");
        if (runtimeLabel != null) runtimeLabel.setText(ready ?
                "Ready to play. Your existing Windows game environment is preserved." :
                busy ? "Setting up Touhou OS automatically. Preparing Wine, Box64 and game storage…" :
                "Engine not ready. Retry initialization here if necessary.");
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

    /**
     * Touhou OS prepares its bundled engine automatically only when needed.
     * Never erase an existing Wine prefix or recreate an existing container.
     */
    private void initializeEngineOnFirstLaunch() {
        if (busy) return;
        RootFS root = RootFS.find(this);
        boolean runtimeMissing = !root.isValid() ||
                root.getVersion() < RootFSInstaller.LATEST_VERSION;
        if (!runtimeMissing && containerId > 0) return;
        showSection(2);
        startSetup();
    }

    private void startSetup() {
        if (busy) return;
        busy = true;
        setStatus("Touhou OS is preparing your game environment. First launch may require substantial storage.");
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

    /**
     * One current installer slot, not a growing history of setup.exe imports.
     * Reimporting an installer replaces the *library entry* only: previously
     * imported folders are not deleted, because game data may be present.
     */
    private synchronized void saveEntry(JSONObject entry) throws Exception {
        JSONArray existing = loadLibrary();
        JSONArray updated = new JSONArray();
        boolean newInstaller = entry.optBoolean("installer");
        String newPath = entry.optString("path", "");
        for (int i = 0; i < existing.length(); i++) {
            JSONObject item = existing.optJSONObject(i);
            if (item == null) continue;
            if (item.optString("path").equals(newPath)) continue;
            if (newInstaller && item.optBoolean("installer")) continue;
            updated.put(item);
        }
        updated.put(entry);
        if (!getPreferences(MODE_PRIVATE).edit()
                .putString("game_library", updated.toString()).commit())
            throw new IllegalStateException("Cannot save the selected installer");
    }

    /**
     * Migrate already-imported libraries: only the newest setup.exe is shown,
     * while previously indexed *games* are preserved. Avoid deleting files.
     */
    private synchronized JSONArray loadLibrary() {
        JSONArray original;
        try {
            original = new JSONArray(getPreferences(MODE_PRIVATE).getString("game_library", "[]"));
        } catch (Exception ignored) {
            return new JSONArray();
        }
        java.util.ArrayList<JSONObject> reverse = new java.util.ArrayList<>();
        java.util.Set<String> paths = new java.util.HashSet<>();
        boolean keptInstaller = false;
        for (int i = original.length() - 1; i >= 0; i--) {
            JSONObject game = original.optJSONObject(i);
            if (game == null) continue;
            boolean installer = game.optBoolean("installer");
            if (installer && keptInstaller) continue;
            String path = game.optString("path", "");
            if (path.isEmpty() || !paths.add(path)) continue;
            if (installer) keptInstaller = true;
            reverse.add(game);
        }
        JSONArray canonical = new JSONArray();
        for (int i = reverse.size() - 1; i >= 0; i--) canonical.put(reverse.get(i));
        if (canonical.length() != original.length()) {
            getPreferences(MODE_PRIVATE).edit()
                .putString("game_library", canonical.toString()).apply();
        }
        return canonical;
    }

    private void refreshLibrary() {
        if (libraryArea == null) return;
        libraryArea.removeAllViews();
        JSONArray library = loadLibrary();
        if (library.length() == 0) {
            LinearLayout empty = card();
            empty.setGravity(Gravity.CENTER_HORIZONTAL);
            empty.addView(label("✦", 35, SAKURA, true));
            TextView title = label("Your Gensokyo library awaits", 17, Color.WHITE, true);
            title.setGravity(Gravity.CENTER_HORIZONTAL);
            empty.addView(title);
            TextView hint = label("Import a game folder or installer to begin.", 13, SECONDARY, false);
            hint.setGravity(Gravity.CENTER_HORIZONTAL);
            empty.addView(hint);
            libraryArea.addView(empty);
            spacerIn(libraryArea, 12);
            return;
        }
        for (int i = 0; i < library.length(); i++) {
            JSONObject game = library.optJSONObject(i);
            if (game == null) continue;
            LinearLayout item = card();
            String path = game.optString("path", "");
            String name = game.optString("name", "Imported game");
            boolean installer = game.optBoolean("installer");
            item.addView(label(installer ? "WINDOWS INSTALLER" : "TOUHOU GAME", 11, GOLD, true));
            item.addView(label(name, 17, Color.WHITE, true));
            item.addView(label(installer ?
                    "Run the original Windows installer" :
                    "Ready to launch from your game library", 12, SECONDARY, false));
            Button play = button(installer ? "INSTALL GAME" : "▶  PLAY GAME", () -> launchGame(path));
            play.setEnabled(!busy && containerId > 0);
            item.addView(play);
            libraryArea.addView(item);
            spacerIn(libraryArea, 12);
        }
    }


    /**
     * Launch the selected original Windows installer without adding /DIR or
     * any destination override. The Windows installer chooses its own path.
     */
    private void launchGame(String path) {
        if (busy || containerId <= 0) return;
        if (!new File(path).isFile()) {
            setStatus("Game file is missing. Re-import the game.");
            return;
        }
        Intent play = new Intent(this, XServerDisplayActivity.class);
        play.putExtra("container_id", containerId);
        play.putExtra("exec_path", path);
        try {
            if (path.toLowerCase(java.util.Locale.ROOT).endsWith("setup.exe")) {
                Container current = new ContainerManager(this).getContainerById(containerId);
                if (current != null) {
                    File log = new File(current.getRootDir(), ".wine/drive_c/touhou_probe.log");
                    TouhouDiagnostics.setProbePath(this, log.getAbsolutePath());
                }
            } else TouhouDiagnostics.setProbePath(this, "");
        } catch (Exception error) {
            TouhouDiagnostics.recordLine("Could not configure local Japanese path diagnostics: " + error);
        }
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
        if (runtimeLabel != null && (message.contains("failed") || message.contains("Could not")))
            runtimeLabel.setText(message + " You can retry here.");
    }

    private void setStatus(String message) {
        if (statusText != null) statusText.setText(message);
    }

    private Button button(String name, Runnable action) {
        Button button = new Button(this);
        button.setText(name);
        button.setAllCaps(false);
        button.setTextColor(Color.WHITE);
        button.setBackgroundTintList(null);
        button.setTextSize(13);
        button.setMinHeight(dp(48));
        button.setBackground(rounded(ACCENT, 14, ACCENT));
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
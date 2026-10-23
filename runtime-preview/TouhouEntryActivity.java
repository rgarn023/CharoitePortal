package com.winlator;

import android.app.Activity;
import android.content.Intent;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.res.ColorStateList;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Bitmap;
import android.graphics.Rect;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.Display;
import android.view.WindowMetrics;
import android.view.DragEvent;
import android.text.TextUtils;
import android.widget.ImageView;
import android.widget.GridLayout;
import android.widget.FrameLayout;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.os.Build;
import android.provider.OpenableColumns;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.EditText;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.documentfile.provider.DocumentFile;

import com.charoitegames.core.CharoiteCore;
import com.charoitegames.core.CharoiteEnvironments;
import com.charoitegames.core.CharoiteThemes;
import com.charoitegames.core.CharoitePageTabs;
import com.charoitegames.core.CharoiteWallpaper;
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
    private static final int WALLPAPER_REQUEST = 1003;

    // Samsung One UI-inspired spacing, surfaces and bottom navigation, with
    // an original Touhou/Charoite identity rather than copied Samsung assets.
    private int BG = 0xffF5F6FA;
    private int PANEL = 0xffffffff;
    private int SECONDARY = 0xff626877;
    private int ACCENT = 0xff5667D8;
    private int GOLD = 0xff8B4668;
    private int SAKURA = 0xffC95884;
    private int LINE = 0xffE7E9F0;
    private int FOREGROUND = 0xff1A1B22;
    private int SELECTED_BG = 0xffE8EBFD;
    private boolean darkMode = false;
    private static final long MAX_GAME_BYTES = 6L * 1024 * 1024 * 1024;
    private static final int MAX_FILES = 12000;

    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private TextView statusText;
    private LinearLayout libraryArea;
    private LinearLayout setupArea;
    private boolean pendingInstallerScan = false;
    private LinearLayout main;
    private Button initButton;
    private Button folderButton;
    private Button installerButton;
    private Button scanButton;
    private Button compatButton;
    private Button displayButton;
    private Button desktopPointerButton;
    private TextView displayDescription;
    private ImageView wallpaperBackground;
    private View wallpaperTint;
    private ImageView wallpaperPreview;
    private TextView wallpaperDescription;
    private Button wallpaperSelectButton;
    private Button wallpaperModeButton;
    private Button wallpaperRemoveButton;
    private Bitmap wallpaperBitmap;
    private boolean wallpaperBusy = false;
    private Button diagnosticButton;
    private CharoitePageTabs pageTabs;
    private LinearLayout libraryScreen;
    private LinearLayout importScreen;
    private LinearLayout systemScreen;
    private ScrollView mainScroll;
    private TextView runtimeLabel;
    private TextView environmentStatus;
    private Button environmentSwitchButton;
    private Button environmentInstallButton;
    private Button environmentCreateButton;
    private boolean busy = false;
    private int containerId = 0;
    private int selectedSection = 0;
    private static final String[] DISPLAY_MODES = CharoiteCore.DISPLAY_MODES;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        CharoiteEnvironments.initialize(this);
        applyGalaxyPalette();
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(PANEL);
        getWindow().getDecorView().setSystemUiVisibility(darkMode ? 0 :
                View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        pendingInstallerScan = getPreferences(MODE_PRIVATE).getBoolean("pending_installer_scan", false);
        render();
        refreshReadyState();
        initializeEngineOnFirstLaunch();
    }

    /** Scan the Windows C: drive after returning from a game installer. */
    @Override protected void onResume() {
        super.onResume();
        if (pendingInstallerScan && !busy && containerId > 0) {
            pendingInstallerScan = false;
            getPreferences(MODE_PRIVATE).edit().putBoolean("pending_installer_scan", false).apply();
            showSection(1);
            findInstalledGames(true);
        }
    }

    @Override public void onDestroy() {
        super.onDestroy();
        worker.shutdown();
    }

    /** Keep active import workers alive while resizing a DeX launcher window. */
    @Override public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        applyGalaxyPaletteForConfig(newConfig);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(PANEL);
        getWindow().getDecorView().setSystemUiVisibility(darkMode ? 0 :
                View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        render();
        refreshReadyState();
    }

    /** Follow the phone's light/dark preference for the One UI-inspired launcher. */
    private void applyGalaxyPalette() {
        applyGalaxyPaletteForConfig(getResources().getConfiguration());
    }

    private void applyGalaxyPaletteForConfig(Configuration config) {
        darkMode = (config.uiMode & Configuration.UI_MODE_NIGHT_MASK)
                == Configuration.UI_MODE_NIGHT_YES;
        BG = darkMode ? 0xff101116 : 0xffF5F6FA;
        PANEL = darkMode ? 0xff202127 : 0xffffffff;
        SECONDARY = darkMode ? 0xffB7B8C5 : 0xff626877;
        boolean touhouTheme = CharoiteEnvironments.isTouhou(this);
        ACCENT = touhouTheme ? (darkMode ? 0xffFFB0D3 : 0xffB34477)
                : (darkMode ? 0xffC4A9FF : 0xff7548C1);
        GOLD = touhouTheme ? (darkMode ? 0xffF2B5CD : 0xff8B4668)
                : (darkMode ? 0xffD2BAFF : 0xff6040A4);
        SAKURA = touhouTheme ? 0xffC95884 : 0xff9169D8;
        LINE = darkMode ? 0xff363840 : 0xffE7E9F0;
        FOREGROUND = darkMode ? 0xffF6F6FB : 0xff1A1B22;
        SELECTED_BG = CharoiteEnvironments.isTouhou(this)
                ? (darkMode ? 0xff533447 : 0xffFBE3EF)
                : (darkMode ? 0xff3A315D : 0xffECE3FF);
    }

    /** Large readable headers, soft surfaces and a thumb-reachable bottom bar. */
    private void render() {
        LinearLayout rootLayout = new LinearLayout(this);
        rootLayout.setOrientation(LinearLayout.VERTICAL);
        rootLayout.setBackgroundColor(Color.TRANSPARENT);

        mainScroll = new ScrollView(this);
        mainScroll.setFillViewport(true);
        mainScroll.setClipToPadding(false);
        mainScroll.setBackgroundColor(Color.TRANSPARENT);
        main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);
        main.setPadding(dp(22), dp(22), dp(22), dp(35));
        // On DeX-sized windows, center the content rather than stretching
        // every card across the entire monitor. Recomputed on window resize.
        FrameLayout contentHost = new FrameLayout(this);
        int hostWidthDp = Math.max(280, getResources().getConfiguration().screenWidthDp - 8);
        FrameLayout.LayoutParams mainParams = new FrameLayout.LayoutParams(
                dp(Math.min(hostWidthDp, 940)), -2, Gravity.TOP | Gravity.CENTER_HORIZONTAL);
        contentHost.addView(main, mainParams);
        mainScroll.addView(contentHost);
        rootLayout.addView(mainScroll, new LinearLayout.LayoutParams(-1, 0, 1f));

        // Touhou owns the pages; reusable Charoite Core owns tab appearance,
        // selection, input, and Samsung navigation-bar clearance.
        pageTabs = new CharoitePageTabs(this,
                new String[]{"Library", "Setup", "System"}, this::showSection);
        pageTabs.setPalette(PANEL, ACCENT, SECONDARY, SELECTED_BG, LINE, darkMode);
        rootLayout.addView(pageTabs, new LinearLayout.LayoutParams(
                -1, CharoitePageTabs.preferredHeight(this)));

        // Keep the wallpaper behind the scrollable content; the navigation
        // buttons remain solid for contrast and easy touch/DeX mouse access.
        FrameLayout wallpaperHost = new FrameLayout(this);
        wallpaperHost.setBackgroundColor(BG);
        wallpaperBackground = new ImageView(this);
        wallpaperBackground.setContentDescription("Wallpaper");
        wallpaperHost.addView(wallpaperBackground, new FrameLayout.LayoutParams(-1, -1));
        wallpaperTint = new View(this);
        wallpaperHost.addView(wallpaperTint, new FrameLayout.LayoutParams(-1, -1));
        wallpaperHost.addView(rootLayout, new FrameLayout.LayoutParams(-1, -1));
        setContentView(wallpaperHost);
        refreshWallpaperViews();

        // Portal identifies the whole app only once, quietly at the top.
        // Realm identity belongs in its own large themed banner below.
        main.addView(label("Charoite Portal", 17, FOREGROUND, true));
        TextView coreIdentity = label("Charoite Core", 12, SECONDARY, false);
        main.addView(coreIdentity);
        spacer(18);

        FrameLayout realmBanner = new FrameLayout(this);
        realmBanner.setBackground(CharoiteThemes.realmBanner(
                CharoiteEnvironments.activeTheme(this)));
        realmBanner.setContentDescription("Active environment: "
                + CharoiteEnvironments.activeName(this));
        realmBanner.setPadding(dp(22), dp(18), dp(18), dp(18));

        LinearLayout realmHeadings = new LinearLayout(this);
        realmHeadings.setOrientation(LinearLayout.VERTICAL);
        realmHeadings.setGravity(Gravity.CENTER_VERTICAL);
        TextView realmCaption = label("CURRENT REALM", 11, 0xffF7DEFA, true);
        realmHeadings.addView(realmCaption);
        TextView realmTitle = label(CharoiteEnvironments.activeName(this),
                34, Color.WHITE, true);
        realmTitle.setMaxLines(2);
        realmTitle.setEllipsize(TextUtils.TruncateAt.END);
        realmTitle.setShadowLayer(dp(3), 0, dp(1), 0x66000000);
        LinearLayout.LayoutParams realmTitleParams = new LinearLayout.LayoutParams(-1, -2);
        realmTitleParams.topMargin = dp(7);
        realmHeadings.addView(realmTitle, realmTitleParams);

        // The large artwork is the background of the *text*, not an icon beside it.
        FrameLayout.LayoutParams headingParams = new FrameLayout.LayoutParams(
                -1, -2, Gravity.CENTER_VERTICAL | Gravity.START);
        realmBanner.addView(realmHeadings, headingParams);
        main.addView(realmBanner, new LinearLayout.LayoutParams(-1, dp(164)));
        spacer(19);

        libraryScreen = new LinearLayout(this);
        libraryScreen.setOrientation(LinearLayout.VERTICAL);
        main.addView(libraryScreen);
        sectionTitle(libraryScreen, "Library", "Your games in " + CharoiteEnvironments.activeName(this) + ".");
        libraryArea = new LinearLayout(this);
        libraryArea.setOrientation(LinearLayout.VERTICAL);
        libraryScreen.addView(libraryArea);
        libraryScreen.addView(label("To install a game, open the Setup tab below.", 13, SECONDARY, false));
        spacerIn(libraryScreen, 12);

        importScreen = new LinearLayout(this);
        importScreen.setOrientation(LinearLayout.VERTICAL);
        main.addView(importScreen);
        sectionTitle(importScreen, "Setup", "Install games into " + CharoiteEnvironments.activeName(this) + ".");
        setupArea = new LinearLayout(this);
        setupArea.setOrientation(LinearLayout.VERTICAL);
        importScreen.addView(setupArea);

        LinearLayout folderCard = card();
        folderCard.addView(label("01   GAME OR INSTALLER FOLDER", 12, GOLD, true));
        folderCard.addView(label("Choose a complete Windows game or installer folder. Charoite Portal runs the installer or adds a playable game to this environment.", 13, SECONDARY, false));
        folderButton = button("SELECT GAME FOLDER", () -> {
            Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
            picker.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            startActivityForResult(picker, FOLDER_REQUEST);
        });
        folderCard.addView(folderButton);
        importScreen.addView(folderCard);
        spacerIn(importScreen, 12);

        LinearLayout exeCard = card();
        exeCard.addView(label("02   STANDALONE WINDOWS INSTALLER", 12, GOLD, true));
        exeCard.addView(label("For a self-contained .exe installer. The original Windows wizard opens without changing the installation directory.", 13, SECONDARY, false));
        installerButton = button("SELECT INSTALLER .EXE", () -> {
            Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            picker.addCategory(Intent.CATEGORY_OPENABLE);
            picker.setType("*/*");
            startActivityForResult(picker, EXE_REQUEST);
        });
        exeCard.addView(installerButton);
        importScreen.addView(exeCard);
        spacerIn(importScreen, 12);

        LinearLayout scanCard = card();
        scanCard.addView(label("03   FIND INSTALLED GAMES", 12, GOLD, true));
        scanCard.addView(label("Search this environment's Windows C: drive after installation or scan previously installed games.", 13, SECONDARY, false));
        scanButton = outlinedButton("FIND INSTALLED GAMES", () -> findInstalledGames(false));
        scanCard.addView(scanButton);
        importScreen.addView(scanCard);
        spacerIn(importScreen, 15);
        importScreen.addView(label("Each environment has its own private Windows container. Existing Touhou games remain in their original C:\\TouhouPocket\\ location. Installer-selected destinations are preserved; games are not bundled.", 12, SECONDARY, false));

        systemScreen = new LinearLayout(this);
        systemScreen.setOrientation(LinearLayout.VERTICAL);
        main.addView(systemScreen);
        sectionTitle(systemScreen, "System", "Manage environments, compatibility and appearance.");

        LinearLayout environmentCard = card();
        environmentCard.addView(label("Environments", 17, FOREGROUND, true));
        environmentStatus = label("", 13, SECONDARY, false);
        environmentCard.addView(environmentStatus);
        environmentSwitchButton = outlinedButton("SWITCH ENVIRONMENT", this::showEnvironmentSwitcher);
        environmentCard.addView(environmentSwitchButton);
        environmentInstallButton = outlinedButton("INSTALL ENVIRONMENT", this::showEnvironmentInstaller);
        environmentCard.addView(environmentInstallButton);
        environmentCreateButton = outlinedButton("CREATE ENVIRONMENT", this::showEnvironmentCreator);
        environmentCard.addView(environmentCreateButton);
        environmentCard.addView(label("Touhou Realm preserves your existing games. New environments get separate Windows containers, game libraries and wallpapers. Install uses built-in offline templates.", 12, SECONDARY, false));
        systemScreen.addView(environmentCard);
        spacerIn(systemScreen, 12);

        LinearLayout runtimeCard = card();
        runtimeCard.addView(label("Game engine", 17, FOREGROUND, true));
        runtimeLabel = label("Checking your game environment…", 13, SECONDARY, false);
        statusText = runtimeLabel;
        runtimeCard.addView(runtimeLabel);
        initButton = button("RETRY GAME ENGINE SETUP", this::startSetup);
        runtimeCard.addView(initButton);
        systemScreen.addView(runtimeCard);
        spacerIn(systemScreen, 12);

        LinearLayout graphicsCard = card();
        graphicsCard.addView(label("Display & compatibility", 17, FOREGROUND, true));
        graphicsCard.addView(label("Use compatibility graphics only when a game fails to display or launch correctly.", 12, SECONDARY, false));
        compatButton = outlinedButton("SWITCH TO COMPATIBILITY GRAPHICS", this::toggleCompatibility);
        graphicsCard.addView(compatButton);
        systemScreen.addView(graphicsCard);
        spacerIn(systemScreen, 12);

        LinearLayout desktopCard = card();
        desktopCard.addView(label("External display & DeX", 17, FOREGROUND, true));
        desktopCard.addView(label("Choose the virtual Windows screen resolution for new game sessions. Automatic adapts to the available DeX window or phone display.", 12, SECONDARY, false));
        displayDescription = label("", 12, SECONDARY, false);
        desktopCard.addView(displayDescription);
        displayButton = outlinedButton("GAME RESOLUTION: AUTOMATIC", this::chooseDisplayMode);
        desktopCard.addView(displayButton);
        desktopCard.addView(label("In DeX, leave the mouse free for the desktop, or capture it inside the game for relative mouse movement.", 12, SECONDARY, false));
        desktopPointerButton = outlinedButton("DEX MOUSE: FREE POINTER", this::toggleDesktopPointer);
        desktopCard.addView(desktopPointerButton);
        systemScreen.addView(desktopCard);
        spacerIn(systemScreen, 12);

        LinearLayout wallpaperCard = card();
        wallpaperCard.addView(label("Wallpaper", 17, FOREGROUND, true));
        wallpaperCard.addView(label("Choose an image saved on your phone. The wallpaper appears behind the Library, Setup and System screens; it does not change your Samsung home wallpaper.", 12, SECONDARY, false));
        wallpaperPreview = new ImageView(this);
        wallpaperPreview.setBackground(rounded(BG, 19, LINE));
        wallpaperPreview.setClipToOutline(true);
        wallpaperPreview.setContentDescription("Wallpaper preview");
        LinearLayout.LayoutParams previewParams = new LinearLayout.LayoutParams(-1, dp(160));
        previewParams.topMargin = dp(10);
        wallpaperCard.addView(wallpaperPreview, previewParams);
        wallpaperDescription = label("", 12, SECONDARY, false);
        wallpaperCard.addView(wallpaperDescription);
        wallpaperSelectButton = outlinedButton("CHOOSE IMAGE FROM PHONE", this::chooseLauncherWallpaper);
        wallpaperCard.addView(wallpaperSelectButton);
        wallpaperModeButton = outlinedButton("DISPLAY: CROP TO FILL", this::chooseWallpaperMode);
        wallpaperCard.addView(wallpaperModeButton);
        wallpaperRemoveButton = outlinedButton("REMOVE WALLPAPER", this::removeLauncherWallpaper);
        wallpaperCard.addView(wallpaperRemoveButton);
        systemScreen.addView(wallpaperCard);
        spacerIn(systemScreen, 12);

        LinearLayout debugCard = card();
        debugCard.addView(label("Support & diagnostics", 17, FOREGROUND, true));
        debugCard.addView(label("Review local Windows launch information. Nothing is sent automatically.", 12, SECONDARY, false));
        diagnosticButton = outlinedButton("VIEW LAST LAUNCH DIAGNOSTICS", this::showDiagnostics);
        debugCard.addView(diagnosticButton);
        systemScreen.addView(debugCard);
        spacerIn(systemScreen, 18);
        systemScreen.addView(label("Charoite Portal · Charoite Core " + CharoiteCore.VERSION + " · Charoite Games. Windows gaming environments use Wine, Box64 and LGPL-licensed Winlator-derived code. No games included.", 11, SECONDARY, false));

        refreshLibrary();
        refreshWallpaperViews();
        showSection(selectedSection);
    }

    /** Select a registered environment without moving or deleting its Wine prefix. */
    private void showEnvironmentSwitcher() {
        if (busy || wallpaperBusy) return;
        JSONArray items = CharoiteEnvironments.list(this);
        String[] names = new String[items.length()];
        String[] ids = new String[items.length()];
        int selected = 0;
        for (int i = 0; i < items.length(); i++) {
            JSONObject item = items.optJSONObject(i);
            ids[i] = item == null ? "" : item.optString("id");
            names[i] = item == null ? "Environment" : item.optString("name");
            if (CharoiteEnvironments.activeId(this).equals(ids[i])) selected = i;
        }
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Switch environment")
                .setSingleChoiceItems(names, selected, (dialog, which) -> {
                    dialog.dismiss();
                    activateEnvironment(ids[which]);
                })
                .setNegativeButton("Cancel", null).show();
    }

    /** Install a verified offline profile, never download untrusted code. */
    private void showEnvironmentInstaller() {
        if (busy || wallpaperBusy) return;
        JSONArray installed = CharoiteEnvironments.list(this);
        for (int i = 0; i < installed.length(); i++) {
            JSONObject env = installed.optJSONObject(i);
            if (env != null && CharoiteEnvironments.GENERAL.equals(env.optString("id"))) {
                new androidx.appcompat.app.AlertDialog.Builder(this)
                        .setTitle("Environment templates")
                        .setMessage("Touhou Realm and General Gaming are installed. Use Create Environment for additional isolated Windows gaming profiles.")
                        .setPositiveButton("OK", null).show();
                return;
            }
        }
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Install environment")
                .setItems(new String[]{"General Gaming — standard Windows games"}, (dialog, which) -> {
                    try {
                        CharoiteEnvironments.installPreset(this, CharoiteEnvironments.GENERAL);
                        activateEnvironment(CharoiteEnvironments.GENERAL);
                    } catch (Exception error) { showEnvironmentError(error); }
                })
                .setNegativeButton("Cancel", null).show();
    }

    private void showEnvironmentCreator() {
        if (busy || wallpaperBusy) return;
        EditText nameInput = new EditText(this);
        nameInput.setSingleLine(true);
        nameInput.setHint("e.g. Classic RPGs");
        nameInput.setPadding(dp(22), dp(12), dp(22), dp(12));
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Create Windows environment")
                .setMessage("Creates an isolated Wine container, private game library and customizable wallpaper. Existing environments and games are preserved.")
                .setView(nameInput)
                .setPositiveButton("Create", (dialog, which) -> {
                    try {
                        JSONObject added = CharoiteEnvironments.create(this,
                                nameInput.getText().toString());
                        activateEnvironment(added.optString("id"));
                    } catch (Exception error) { showEnvironmentError(error); }
                })
                .setNegativeButton("Cancel", null).show();
    }

    private void showEnvironmentError(Exception error) {
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Environment error")
                .setMessage(error.getMessage() == null ? "Could not save environment."
                        : error.getMessage())
                .setPositiveButton("OK", null).show();
    }

    private void activateEnvironment(String id) {
        if (busy || wallpaperBusy) return;
        if (!CharoiteEnvironments.switchTo(this, id)) {
            showEnvironmentError(new IllegalStateException("Could not select environment."));
            return;
        }
        containerId = 0;
        wallpaperBitmap = null;
        selectedSection = 2;
        applyGalaxyPalette();
        render();
        refreshReadyState();
        initializeEngineOnFirstLaunch();
    }

    private void showSection(int section) {
        if (libraryScreen == null) return;
        selectedSection = section;
        libraryScreen.setVisibility(section == 0 ? View.VISIBLE : View.GONE);
        importScreen.setVisibility(section == 1 ? View.VISIBLE : View.GONE);
        systemScreen.setVisibility(section == 2 ? View.VISIBLE : View.GONE);
        if (pageTabs != null) pageTabs.setSelectedIndex(section);
        if (mainScroll != null) mainScroll.smoothScrollTo(0, 0);
    }

    private void sectionTitle(LinearLayout screen, String heading, String subtitle) {
        screen.addView(label(heading, 29, FOREGROUND, true));
        screen.addView(label(subtitle, 13, SECONDARY, false));
        spacerIn(screen, 13);
    }

    private LinearLayout card() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(dp(19), dp(19), dp(19), dp(19));
        layout.setBackground(rounded(PANEL, 25, LINE));
        return layout;
    }

    private GradientDrawable rounded(int fill, int radius, int lineColor) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(fill);
        drawable.setCornerRadius(dp(radius));
        drawable.setStroke(dp(1), lineColor);
        return drawable;
    }

    /** Choose any accessible local image without needing storage permission. */
    private void chooseLauncherWallpaper() {
        if (wallpaperBusy) return;
        Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        picker.addCategory(Intent.CATEGORY_OPENABLE);
        picker.setType("image/*");
        picker.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        startActivityForResult(picker, WALLPAPER_REQUEST);
    }

    /** Copy privately: don't store a temporary gallery permission or move photos. */
    private void importLauncherWallpaper(Uri selected) {
        if (wallpaperBusy) return;
        wallpaperBusy = true;
        updateWallpaperControls();
        worker.execute(() -> {
            try {
                CharoiteWallpaper.importImage(this, selected, CharoiteEnvironments.activeId(this));
                runOnUiThread(() -> {
                    if (isFinishing() || isDestroyed()) return;
                    wallpaperBitmap = null;
                    wallpaperBusy = false;
                    refreshWallpaperViews();
                    Toast.makeText(this, "Wallpaper updated", Toast.LENGTH_SHORT).show();
                });
            } catch (Exception error) {
                runOnUiThread(() -> {
                    if (isFinishing() || isDestroyed()) return;
                    wallpaperBusy = false;
                    updateWallpaperControls();
                    new androidx.appcompat.app.AlertDialog.Builder(this)
                            .setTitle("Wallpaper wasn't changed")
                            .setMessage(error.getMessage() != null ? error.getMessage() : "Cannot read that image.")
                            .setPositiveButton("OK", null)
                            .show();
                });
            }
        });
    }

    private void chooseWallpaperMode() {
        String[] options = {
                "Crop to fill — cover the display",
                "Fit whole image — may leave empty borders"
        };
        int current = CharoiteWallpaper.getMode(getPreferences(MODE_PRIVATE), CharoiteEnvironments.activeId(this));
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("How should wallpaper fit?")
                .setSingleChoiceItems(options, current, (dialog, which) -> {
                    CharoiteWallpaper.setMode(getPreferences(MODE_PRIVATE), CharoiteEnvironments.activeId(this), which);
                    refreshWallpaperViews();
                    dialog.dismiss();
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void removeLauncherWallpaper() {
        if (wallpaperBusy) return;
        if (!CharoiteWallpaper.removeWallpaper(this, CharoiteEnvironments.activeId(this))) {
            Toast.makeText(this, "Cannot remove wallpaper", Toast.LENGTH_LONG).show();
            return;
        }
        wallpaperBitmap = null;
        refreshWallpaperViews();
        Toast.makeText(this, "Wallpaper removed", Toast.LENGTH_SHORT).show();
    }

    private void updateWallpaperControls() {
        boolean present = CharoiteWallpaper.hasWallpaper(this, CharoiteEnvironments.activeId(this));
        if (wallpaperSelectButton != null) wallpaperSelectButton.setEnabled(!wallpaperBusy);
        if (wallpaperModeButton != null) {
            wallpaperModeButton.setVisibility(present ? View.VISIBLE : View.GONE);
            wallpaperModeButton.setEnabled(!wallpaperBusy);
            wallpaperModeButton.setText(CharoiteWallpaper.getMode(getPreferences(MODE_PRIVATE), CharoiteEnvironments.activeId(this))
                    == CharoiteWallpaper.MODE_FIT ? "DISPLAY: FIT WHOLE IMAGE" : "DISPLAY: CROP TO FILL");
        }
        if (wallpaperRemoveButton != null) {
            wallpaperRemoveButton.setVisibility(present ? View.VISIBLE : View.GONE);
            wallpaperRemoveButton.setEnabled(!wallpaperBusy);
        }
        if (wallpaperPreview != null)
            wallpaperPreview.setVisibility(present ? View.VISIBLE : View.GONE);
        if (wallpaperDescription != null)
            wallpaperDescription.setText(wallpaperBusy ? "Copying your image privately…"
                    : present ? "Wallpaper saved for " + CharoiteEnvironments.activeName(this) + ". Original photo is unchanged."
                    : "No wallpaper selected. Your default theme is active.");
    }

    private void refreshWallpaperViews() {
        if (wallpaperBackground == null || wallpaperTint == null) return;
        boolean present = CharoiteWallpaper.hasWallpaper(this, CharoiteEnvironments.activeId(this));
        if (present && wallpaperBitmap == null)
            wallpaperBitmap = CharoiteWallpaper.loadBitmap(this, 2560, CharoiteEnvironments.activeId(this));
        present = present && wallpaperBitmap != null;
        if (present) {
            ImageView.ScaleType style = CharoiteWallpaper.getMode(getPreferences(MODE_PRIVATE), CharoiteEnvironments.activeId(this))
                    == CharoiteWallpaper.MODE_FIT
                    ? ImageView.ScaleType.FIT_CENTER : ImageView.ScaleType.CENTER_CROP;
            wallpaperBackground.setImageBitmap(wallpaperBitmap);
            wallpaperBackground.setScaleType(style);
            // Readable text/buttons even over vibrant backgrounds.
            wallpaperTint.setBackgroundColor(darkMode ? 0xA9101116 : 0xA8F5F6FA);
        } else {
            wallpaperBackground.setImageDrawable(CharoiteThemes.defaultWallpaper(
                    CharoiteEnvironments.activeTheme(this), darkMode));
            wallpaperBackground.setScaleType(ImageView.ScaleType.FIT_XY);
            wallpaperTint.setBackgroundColor(darkMode ? 0x40101116 : 0x55F5F6FA);
        }
        if (wallpaperPreview != null) {
            wallpaperPreview.setImageBitmap(present ? wallpaperBitmap : null);
            wallpaperPreview.setScaleType(CharoiteWallpaper.getMode(getPreferences(MODE_PRIVATE), CharoiteEnvironments.activeId(this))
                    == CharoiteWallpaper.MODE_FIT
                    ? ImageView.ScaleType.FIT_CENTER : ImageView.ScaleType.CENTER_CROP);
        }
        updateWallpaperControls();
    }

    private Button outlinedButton(String name, Runnable action) {
        Button view = button(name, action);
        view.setBackground(rounded(SELECTED_BG, 18, SELECTED_BG));
        view.setTextColor(ACCENT);
        return view;
    }

    private void refreshReadyState() {
        RootFS root = RootFS.find(this);
        if (!root.isValid()) {
            containerId = 0;
            setStatus("Preparing the bundled game engine…");
        } else if (root.getVersion() < RootFSInstaller.LATEST_VERSION) {
            containerId = 0;
            setStatus("Updating the bundled game engine…");
        } else {
            try {
                ContainerManager manager = new ContainerManager(this);
                Container selected = getActiveContainer(manager);
                containerId = selected != null ? selected.id : 0;
                setStatus(engineRefreshRequired()
                        ? "Charoite Portal was updated. Preparing the bundled engine…"
                        : selected == null
                            ? "Finishing your automatic Windows game environment setup…"
                            : "Game engine ready • Games are in the active environment Library.");
            } catch (Exception ex) {
                containerId = 0;
                setStatus("Engine check failed: " + ex.getMessage());
            }
        }
        updateButtons();
    }

    private void updateButtons() {
        RootFS root = RootFS.find(this);
        boolean ready = root.isValid() && root.getVersion() >= RootFSInstaller.LATEST_VERSION
                && containerId > 0 && !engineRefreshRequired();
        initButton.setEnabled(!busy);
        // Automatic setup on first launch; expose only a manual retry on failure.
        initButton.setVisibility(ready || busy ? View.GONE : View.VISIBLE);
        initButton.setText("RETRY GAME ENGINE SETUP");
        if (environmentStatus != null) environmentStatus.setText("Active: "
                + CharoiteEnvironments.activeName(this) + "  •  "
                + (containerId > 0 ? "Windows container ready" : "Preparing environment"));
        if (environmentSwitchButton != null) environmentSwitchButton.setEnabled(!busy && !wallpaperBusy);
        if (environmentInstallButton != null) environmentInstallButton.setEnabled(!busy && !wallpaperBusy);
        if (environmentCreateButton != null) environmentCreateButton.setEnabled(!busy && !wallpaperBusy);
        if (runtimeLabel != null) runtimeLabel.setText(ready ?
                "Up to date • Wine and Box64 are ready for your games." :
                busy ? "Preparing this APK's bundled Wine / Box64 runtime automatically…" :
                "Engine not ready. Retry automatic preparation here if necessary.");
        folderButton.setEnabled(!busy && ready);
        installerButton.setEnabled(!busy && ready);
        scanButton.setEnabled(!busy && ready);
        compatButton.setEnabled(!busy && ready);
        compatButton.setText(CharoiteCore.compatibleGraphics(this) ?
                "RESTORE NORMAL GRAPHICS" : "SWITCH TO COMPATIBILITY GRAPHICS");
        diagnosticButton.setEnabled(!busy);
        if (displayButton != null) {
            int mode = getDisplayModeIndex();
            displayButton.setText("GAME RESOLUTION: " + DISPLAY_MODES[mode]);
        }
        if (desktopPointerButton != null)
            desktopPointerButton.setText(CharoiteCore.isDesktopPointerCaptured(this)
                    ? "DEX MOUSE: CAPTURE IN GAME" : "DEX MOUSE: FREE POINTER");
        if (displayDescription != null)
            displayDescription.setText((isDesktopWindow() ? "Desktop/external window" : "Phone window")
                + " detected · Automatic: " + automaticGameResolution()
                + "\nChanges take effect when you next launch a game.");
        updateWallpaperControls();
        refreshLibrary();
    }

    private Container getActiveContainer(ContainerManager manager) {
        int saved = CharoiteEnvironments.activeContainerId(this);
        // Only Touhou Realm can inherit the old app's first Windows container.
        // Never reuse another environment's prefix for newly created worlds.
        Container container = saved > 0 ? manager.getContainerById(saved) : null;
        if (container == null && CharoiteEnvironments.isTouhou(this)
                && saved == 0 && !manager.getContainers().isEmpty())
            container = manager.getContainers().get(0);
        return container;
    }


    private boolean isDesktopWindow() {
        return CharoiteCore.isDesktopWindow(this);
    }

    private int getDisplayModeIndex() {
        return CharoiteCore.getDisplayModeIndex(this);
    }

    private String automaticGameResolution() {
        return CharoiteCore.automaticGameResolution(this);
    }

    private String chosenGameResolution() {
        return CharoiteCore.chosenGameResolution(this);
    }

    private void chooseDisplayMode() {
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Windows game display resolution")
                .setSingleChoiceItems(DISPLAY_MODES, getDisplayModeIndex(), (dialog, which) -> {
                    CharoiteCore.setDisplayMode(this, which);
                    updateButtons();
                    setStatus("Game display resolution set to " + chosenGameResolution()
                            + ". Relaunch the game to apply.");
                    dialog.dismiss();
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void toggleDesktopPointer() {
        boolean capture = !CharoiteCore.isDesktopPointerCaptured(this);
        CharoiteCore.setDesktopPointerCaptured(this, capture);
        updateButtons();
        setStatus(capture
                ? "DeX mouse capture enabled for the next game. Release it using Android's pointer capture controls."
                : "DeX mouse remains free when launching your next game.");
    }

    /** Preferences adjust only this app's private game environment. */
    private void toggleCompatibility() {
        if (busy || containerId <= 0) return;
        try {
            boolean compatible = !CharoiteCore.compatibleGraphics(this);
            Container current = new ContainerManager(this).getContainerById(containerId);
            if (current == null) throw new IllegalStateException("Windows game environment missing");
            CharoiteCore.applyGraphicsProfile(this, current, compatible);
            CharoiteCore.setCompatibleGraphics(this, compatible);
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
            .setTitle("Windows game startup diagnostics")
            .setMessage(report)
            .setPositiveButton("Copy report", (dialog, which) -> {
                ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                clipboard.setPrimaryClip(ClipData.newPlainText("Touhou startup report", report));
                setStatus("Startup report copied. Share the error text for troubleshooting.");
            })
            .setNegativeButton("Close", null)
            .show();
    }

    /** Preserve existing engine markers in this Activity's private preferences. */
    private boolean engineRefreshRequired() {
        return CharoiteCore.engineRefreshRequired(this);
    }

    private void markEnginePrepared() {
        CharoiteCore.markEnginePrepared(this);
    }

    /** Auto-refresh the bundled engine on every APK install or update. */
    private void initializeEngineOnFirstLaunch() {
        if (busy) return;
        RootFS root = RootFS.find(this);
        boolean runtimeMissing = !root.isValid() ||
                root.getVersion() < RootFSInstaller.LATEST_VERSION;
        if (!runtimeMissing && containerId > 0 && !engineRefreshRequired()) return;
        startSetup();
    }

    private void startSetup() {
        if (busy) return;
        busy = true;
        setStatus("Preparing the Charoite Core Windows runtime…");
        updateButtons();
        worker.execute(() -> {
            try {
                CharoiteCore.prepareBundledEngine(this);
                runOnUiThread(this::ensureGameEnvironment);
            } catch (Exception ex) {
                runOnUiThread(() -> finishOperation("Setup failed: " + ex.getMessage()));
            }
        });
    }

    private void ensureGameEnvironment() {
        setStatus("Checking your private Windows game container…");
        try {
            ContainerManager manager = new ContainerManager(this);
            Container existing = getActiveContainer(manager);
            if (existing != null) {
                containerId = existing.id;
                CharoiteEnvironments.attachContainer(this, CharoiteEnvironments.activeId(this), containerId);
                markEnginePrepared();
                finishOperation("Environment ready. Existing games and saves were preserved.");
                return;
            }
            boolean conservative = CharoiteCore.compatibleGraphics(this);
            final String environmentId = CharoiteEnvironments.activeId(this);
            JSONObject profile = CharoiteCore.createContainerProfile(
                    this, CharoiteEnvironments.activeName(this), conservative);
            manager.createContainerAsync(profile, container -> {
                if (isFinishing() || isDestroyed()) return;
                if (container == null) {
                    finishOperation("Game environment creation failed; retry setup.");
                } else {
                    try {
                        CharoiteEnvironments.attachContainer(this, environmentId, container.id);
                        containerId = container.id;
                        markEnginePrepared();
                        finishOperation(CharoiteEnvironments.activeName(this)
                                + " prepared. Open Setup to install Windows games.");
                    } catch (Exception saveError) {
                        finishOperation("Environment created but registration failed: " + saveError.getMessage());
                    }
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
        else if (requestCode == WALLPAPER_REQUEST) importLauncherWallpaper(uri);
    }


    /**
     * An imported Windows installer may install into Program Files, not our
     * import folder. Recognize installed game executables inside C: without
     * making users browse the Windows desktop or container manager.
     */
    private void findInstalledGames(boolean afterInstaller) {
        if (busy || containerId <= 0) return;
        busy = true;
        setStatus("Searching for installed games in " + CharoiteEnvironments.activeName(this) + "…");
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
                getPreferences(MODE_PRIVATE).edit().putString(CharoiteEnvironments.libraryKey(this), library.toString()).commit();
                final int newGames = added;
                runOnUiThread(() -> {
                    finishOperation(newGames == 0
                        ? (afterInstaller ? "Installer closed. No supported new game found yet; confirm installation completed and try scanning again." : "No new supported games found on C:.")
                        : "Found " + newGames + " game(s) on C:. Ready to play.");
                    if (newGames > 0) showSection(0);
                    else if (afterInstaller) showSection(1);
                });
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
                if (CharoiteEnvironments.isTouhou(this)) {
                    if (name.equals("gn_enbu.exe") || name.equals("enbu_ap.exe") ||
                            name.matches("th(0[6-9]|1[0-9]|20)\\.exe"))
                        matches.add(file);
                } else if (name.endsWith(".exe") && !isLikelyInstaller(name)
                        && !name.equals("unins000.exe") && !name.equals("uninstall.exe")
                        && !name.equals("winecfg.exe") && !name.equals("explorer.exe")
                        && !name.equals("regedit.exe")) {
                    matches.add(file);
                }
            }
        }
    }

    private void importGame(Uri uri, boolean folder) {
        if (busy || containerId <= 0) return;
        busy = true;
        setStatus(folder ? "Preparing game or installer folder…" : "Preparing standalone Windows installer…");
        updateButtons();
        worker.execute(() -> {
            File destination = null;
            try {
                Container current = new ContainerManager(this).getContainerById(containerId);
                if (current == null) throw new IllegalStateException("Game environment missing");
                File gameBase = new File(current.getRootDir(), CharoiteEnvironments.isTouhou(this)
                        ? ".wine/drive_c/TouhouPocket" : ".wine/drive_c/CharoitePortal");
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
                final String selectedPath = exe.getAbsolutePath();
                final boolean launchInstaller = installer;
                runOnUiThread(() -> {
                    finishOperation(launchInstaller
                        ? "Setup files are ready. Opening the original Windows installer…"
                        : "Game imported successfully and added to Library.");
                    showSection(launchInstaller ? 1 : 0);
                    if (launchInstaller) launchGame(selectedPath, true);
                });
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
        if (CharoiteEnvironments.isTouhou(this))
        for (String priority : new String[]{"enbu_ap.exe", "gn_enbu.exe", "th20.exe", "th19.exe"}) {
            for (String value : candidates)
                if (new File(value).getName().equalsIgnoreCase(priority)) return value;
        }
        if (CharoiteEnvironments.isTouhou(this))
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
        return CharoiteEnvironments.isTouhou(this)
                ? "Touhou game: " + new File(executable).getName()
                : new File(executable).getName().replaceFirst("(?i)\\.exe$", "");
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
                .putString(CharoiteEnvironments.libraryKey(this), updated.toString()).commit())
            throw new IllegalStateException("Cannot save the selected installer");
    }

    /**
     * Migrate already-imported libraries: only the newest setup.exe is shown,
     * while previously indexed *games* are preserved. Avoid deleting files.
     */
    private synchronized JSONArray loadLibrary() {
        JSONArray original;
        try {
            original = new JSONArray(getPreferences(MODE_PRIVATE).getString(CharoiteEnvironments.libraryKey(this), "[]"));
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
                .putString(CharoiteEnvironments.libraryKey(this), canonical.toString()).apply();
        }
        return canonical;
    }

    /**
     * Game icons work like home-screen tiles. A tap opens the game;
     * long-press and drag rearranges tile order without moving files.
     */
    private void refreshLibrary() {
        if (libraryArea == null) return;
        libraryArea.removeAllViews();
        JSONArray library = loadLibrary();
        ArrayList<JSONObject> games = new ArrayList<>();
        for (int i = 0; i < library.length(); i++) {
            JSONObject game = library.optJSONObject(i);
            if (game != null && !game.optBoolean("installer")) games.add(game);
        }

        if (games.isEmpty()) {
            LinearLayout empty = card();
            empty.setGravity(Gravity.CENTER_HORIZONTAL);
            empty.addView(label("✦", 35, SAKURA, true));
            TextView title = label("Your Gensokyo library awaits", 17, FOREGROUND, true);
            title.setGravity(Gravity.CENTER_HORIZONTAL);
            empty.addView(title);
            TextView hint = label("Use Setup to install a Windows game in this environment.", 13, SECONDARY, false);
            hint.setGravity(Gravity.CENTER_HORIZONTAL);
            empty.addView(hint);
            libraryArea.addView(empty);
        } else {
            libraryArea.addView(label("Tap an icon to play · Touch and hold to rearrange", 12, SECONDARY, false));
            spacerIn(libraryArea, 10);
            int columns = getResources().getConfiguration().screenWidthDp >= 600 ? 4 : 3;
            GridLayout grid = new GridLayout(this);
            grid.setColumnCount(columns);
            grid.setAlignmentMode(GridLayout.ALIGN_BOUNDS);
            grid.setUseDefaultMargins(false);
            for (int i = 0; i < games.size(); i++) {
                JSONObject game = games.get(i);
                String path = game.optString("path", "");
                String name = game.optString("name", "Windows game");
                boolean exists = new File(path).isFile();

                LinearLayout tile = new LinearLayout(this);
                tile.setOrientation(LinearLayout.VERTICAL);
                tile.setGravity(Gravity.TOP | Gravity.CENTER_HORIZONTAL);
                tile.setPadding(dp(5), dp(12), dp(5), dp(11));
                tile.setBackground(rounded(PANEL, 22, LINE));
                tile.setMinimumHeight(dp(138));
                tile.setContentDescription(name + (exists
                        ? ", tap to play, long press to move" : ", executable missing, long press to move"));

                TextView gameIcon = label(gameIconCharacter(path), 29, Color.WHITE, true);
                gameIcon.setGravity(Gravity.CENTER);
                GradientDrawable iconBack = new GradientDrawable(
                        GradientDrawable.Orientation.TL_BR, gameIconColors(path));
                iconBack.setCornerRadius(dp(22));
                gameIcon.setBackground(iconBack);
                tile.addView(gameIcon, new LinearLayout.LayoutParams(dp(69), dp(69)));

                TextView gameTitle = label(name, 12, FOREGROUND, true);
                gameTitle.setGravity(Gravity.TOP | Gravity.CENTER_HORIZONTAL);
                gameTitle.setMaxLines(2);
                gameTitle.setEllipsize(TextUtils.TruncateAt.END);
                LinearLayout.LayoutParams nameParams = new LinearLayout.LayoutParams(-1, -2);
                nameParams.topMargin = dp(9);
                tile.addView(gameTitle, nameParams);

                if (exists && !busy && containerId > 0)
                    tile.setOnClickListener(v -> launchGame(path, false));
                if (!busy) {
                    tile.setOnLongClickListener(v -> {
                        ClipData clip = ClipData.newPlainText("touhou-game", path);
                        return v.startDragAndDrop(clip, new View.DragShadowBuilder(v), path, 0);
                    });
                }
                tile.setOnDragListener((v, event) -> {
                    switch (event.getAction()) {
                        case DragEvent.ACTION_DRAG_STARTED:
                            return event.getLocalState() instanceof String;
                        case DragEvent.ACTION_DRAG_ENTERED:
                            v.setBackground(rounded(SELECTED_BG, 22, ACCENT));
                            return true;
                        case DragEvent.ACTION_DRAG_EXITED:
                        case DragEvent.ACTION_DRAG_ENDED:
                            v.setBackground(rounded(PANEL, 22, LINE));
                            return true;
                        case DragEvent.ACTION_DROP:
                            v.setBackground(rounded(PANEL, 22, LINE));
                            if (event.getLocalState() instanceof String)
                                reorderGame((String) event.getLocalState(), path);
                            return true;
                        default:
                            return true;
                    }
                });
                GridLayout.LayoutParams params = new GridLayout.LayoutParams(
                        GridLayout.spec(i / columns), GridLayout.spec(i % columns, 1f));
                params.width = 0;
                params.height = -2;
                params.setMargins(dp(3), dp(3), dp(3), dp(3));
                grid.addView(tile, params);
            }
            libraryArea.addView(grid);
            grid.setOnDragListener((v, event) -> {
                if (event.getAction() == DragEvent.ACTION_DRAG_STARTED)
                    return event.getLocalState() instanceof String;
                if (event.getAction() == DragEvent.ACTION_DROP &&
                        event.getLocalState() instanceof String) {
                    // Dropping between tiles moves the game to the end.
                    reorderGame((String) event.getLocalState(),
                            games.get(games.size() - 1).optString("path", ""));
                    return true;
                }
                return true;
            });
        }
        refreshSetup(library);
    }

    private String gameIconCharacter(String path) {
        String exe = new File(path).getName().toLowerCase(Locale.ROOT);
        if (exe.equals("gn_enbu.exe")) return "東";
        if (exe.equals("enbu_ap.exe")) return "夢";
        if (exe.matches("th\\d+\\.exe")) return "弾";
        return "✦";
    }

    private int[] gameIconColors(String path) {
        int[][] colors = {
            {0xffCD5077, 0xff8D3974}, {0xff8172CE, 0xff4A61BD},
            {0xffDD8659, 0xffB44F71}, {0xff568EAE, 0xff5461A6},
            {0xffA278B6, 0xff634E96}
        };
        return colors[(path.hashCode() & 0x7fffffff) % colors.length];
    }

    /** Save only visual ordering; the original installer entry stays intact. */
    private synchronized void reorderGame(String sourcePath, String targetPath) {
        if (busy || sourcePath.equals(targetPath)) return;
        JSONArray original = loadLibrary();
        ArrayList<JSONObject> games = new ArrayList<>();
        for (int i = 0; i < original.length(); i++) {
            JSONObject entry = original.optJSONObject(i);
            if (entry != null && !entry.optBoolean("installer")) games.add(entry);
        }
        int from = -1, to = -1;
        for (int i = 0; i < games.size(); i++) {
            if (sourcePath.equals(games.get(i).optString("path"))) from = i;
            if (targetPath.equals(games.get(i).optString("path"))) to = i;
        }
        if (from < 0 || to < 0) return;
        JSONObject moved = games.remove(from);
        games.add(to, moved);
        JSONArray updated = new JSONArray();
        int gameIndex = 0;
        for (int i = 0; i < original.length(); i++) {
            JSONObject entry = original.optJSONObject(i);
            if (entry == null) continue;
            updated.put(entry.optBoolean("installer") ? entry : games.get(gameIndex++));
        }
        if (getPreferences(MODE_PRIVATE).edit()
                .putString(CharoiteEnvironments.libraryKey(this), updated.toString()).commit()) {
            libraryArea.post(this::refreshLibrary);
            setStatus("Library icon order saved.");
        } else setStatus("Could not save your Library icon order.");
    }

    /** Preserve the existing imported installer for re-run, outside of Library. */
    private void refreshSetup(JSONArray library) {
        if (setupArea == null) return;
        setupArea.removeAllViews();
        JSONObject lastInstaller = null;
        for (int i = library.length() - 1; i >= 0; i--) {
            JSONObject entry = library.optJSONObject(i);
            if (entry != null && entry.optBoolean("installer")) {
                lastInstaller = entry;
                break;
            }
        }
        if (lastInstaller == null) return;
        String path = lastInstaller.optString("path", "");
        LinearLayout installerCard = card();
        installerCard.addView(label("CURRENT INSTALLER", 12, GOLD, true));
        installerCard.addView(label(new File(path).getName(), 16, FOREGROUND, true));
        installerCard.addView(label("If setup was interrupted, reopen the original installer here. Imported files are preserved.", 12, SECONDARY, false));
        Button rerun = outlinedButton("RUN INSTALLER AGAIN", () -> launchGame(path, true));
        rerun.setEnabled(!busy && containerId > 0 && new File(path).isFile());
        installerCard.addView(rerun);
        setupArea.addView(installerCard);
        spacerIn(setupArea, 12);
    }


    /**
     * Launch the selected original Windows installer without adding /DIR or
     * any destination override. The Windows installer chooses its own path.
     */
    private void launchGame(String path, boolean installer) {
        if (busy || containerId <= 0) return;
        if (!new File(path).isFile()) {
            setStatus("Game file is missing. Re-import the game.");
            return;
        }
        Intent play = new Intent(this, XServerDisplayActivity.class);
        play.putExtra("container_id", containerId);
        play.putExtra("exec_path", path);
        play.putExtra("touhou_desktop_window", CharoiteCore.isDesktopWindow(this));
        play.putExtra("touhou_display_size", CharoiteCore.chosenGameResolution(this));
        play.putExtra("touhou_pointer_capture", CharoiteCore.shouldCapturePointer(this));
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
        if (installer) {
            pendingInstallerScan = true;
            getPreferences(MODE_PRIVATE).edit().putBoolean("pending_installer_scan", true).apply();
        }
        try {
            startActivity(play);
        } catch (Exception error) {
            if (installer) {
                pendingInstallerScan = false;
                getPreferences(MODE_PRIVATE).edit().putBoolean("pending_installer_scan", false).apply();
            }
            setStatus("Unable to launch Windows program: " + error.getMessage());
        }
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
        button.setTextSize(14);
        button.setMinHeight(dp(54));
        button.setBackground(rounded(darkMode ? 0xff5968C7 : ACCENT, 19,
                darkMode ? 0xff5968C7 : ACCENT));
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
        text.setTypeface(Typeface.create("sans-serif", Typeface.NORMAL),
                strong ? Typeface.BOLD : Typeface.NORMAL);
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
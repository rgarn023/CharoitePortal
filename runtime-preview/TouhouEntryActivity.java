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
import com.charoitegames.core.CharoiteGameImport;
import com.charoitegames.core.CharoiteGameLibrary;
import com.charoitegames.core.CharoiteGameIcons;
import com.charoitegames.core.CharoiteGameRemoval;
import com.charoitegames.core.CharoiteGameDiscovery;
import com.charoitegames.core.CharoiteGameProfiles;
import com.charoitegames.core.CharoiteGameControlProfiles;
import com.charoitegames.core.CharoiteGameSessions;
import com.charoitegames.core.CharoiteDiagnostics;
import com.charoitegames.core.CharoiteRenderingDiagnostics;
import com.charoitegames.core.CharoiteEnvironments;
import com.charoitegames.core.CharoiteBattleNetSupport;
import com.charoitegames.core.CharoiteEnvironmentFiles;
import com.charoitegames.core.CharoiteFileManagerActivity;
import com.charoitegames.core.CharoiteThemes;
import com.charoitegames.core.CharoitePageTabs;
import com.charoitegames.core.CharoiteSwipePager;
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
    private static final int INSTALLER_FOLDER_REQUEST = 1007;
    private static final int WALLPAPER_REQUEST = 1003;
    private static final int ENVIRONMENT_OPEN_REQUEST = 1004;
    private static final int ENVIRONMENT_CREATE_REQUEST = 1005;
    private static final int ENVIRONMENT_EXPORT_REQUEST = 1006;

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

    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private TextView statusText;
    private LinearLayout libraryArea;
    private LinearLayout setupArea;
    private LinearLayout main;
    private Button initButton;
    private Button folderButton;
    private Button installerButton;
    private Button installerFolderButton;
    private Button battleNetDownloadButton;
    private Button battleNetInstallButton;
    private Button battleNetOpenButton;
    private Button battleNetOriginalButton;
    private Button battleNetDirectButton;
    private Button battleNetLaunchCompatButton;
    private Button battleNetGpuProcessButton;
    private Button battleNetRpcStartupButton;
    private Button battleNetWineProbeButton;
    private Button battleNetLiveMonitorButton;
    private Button battleNetBrowserSettingsButton;
    private Button battleNetBrowserCacheButton;
    private Button battleNetCefReportButton;
    private Button battleNetCompatButton;
    private Button battleNetDiagnoseButton;
    private TextView battleNetDownloadStatus;
    private Button scanButton;
    private Button compatButton;
    private Button japaneseButton;
    private Button installerFontButton;
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
    private CharoiteSwipePager mainScroll;
    private TextView runtimeLabel;
    private TextView environmentStatus;
    private Button environmentSwitchButton;
    private Button environmentInstallButton;
    private Button environmentCreateButton;
    private Button environmentExportButton;
    private String pendingEnvironmentName;
    private String pendingExportEnvironmentId;
    private boolean busy = false;
    // An installer may return while a background operation still owns the UI.
    // Queue its scan until that operation finishes, without resetting Wine.
    private boolean scanAfterInstallerReturn = false;
    private int containerId = 0;
    private int selectedSection = 0;
    private static final String[] DISPLAY_MODES = CharoiteCore.DISPLAY_MODES;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        CharoiteEnvironments.initialize(this);
        if (savedInstanceState != null) {
            pendingEnvironmentName = savedInstanceState.getString("pending_portal_environment_name");
            pendingExportEnvironmentId = savedInstanceState.getString("pending_portal_export_id");
        }
        applyGalaxyPalette();
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(PANEL);
        getWindow().getDecorView().setSystemUiVisibility(darkMode ? 0 :
                View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        render();
        refreshReadyState();
        initializeEngineOnFirstLaunch();
    }

    /** Register newly installed games after the Windows installer returns. */
    @Override protected void onResume() {
        super.onResume();
        if (CharoiteGameSessions.hasPendingInstallerScan(this)) {
            scanAfterInstallerReturn = true;
            if (!busy && containerId > 0) {
                scanAfterInstallerReturn = false;
                showSection(1);
                findInstalledGames(true);
            }
        }
    }

    @Override protected void onSaveInstanceState(Bundle state) {
        state.putString("pending_portal_environment_name", pendingEnvironmentName);
        state.putString("pending_portal_export_id", pendingExportEnvironmentId);
        super.onSaveInstanceState(state);
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

        // Core handles horizontal page swipes without stealing vertical scroll,
        // long-press game tile moves, buttons, or DeX mouse drags.
        mainScroll = new CharoiteSwipePager(this, direction -> {
            int next = selectedSection + direction;
            if (next >= 0 && next <= 2) showSection(next);
        });
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

        // Portal owns page content; reusable Charoite Core owns tab appearance,
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

        // Keep the Portal header compact and the active realm clearly named.
        main.addView(label("Charoite Portal", 17, FOREGROUND, true));
        TextView coreIdentity = label("Charoite Core", 12, SECONDARY, false);
        main.addView(coreIdentity);
        spacer(10);

        FrameLayout realmBanner = new FrameLayout(this);
        realmBanner.setBackground(CharoiteThemes.realmBanner(
                CharoiteEnvironments.activeTheme(this)));
        realmBanner.setContentDescription("Active environment: "
                + CharoiteEnvironments.activeName(this));
        realmBanner.setPadding(dp(18), dp(12), dp(15), dp(12));

        LinearLayout realmHeadings = new LinearLayout(this);
        realmHeadings.setOrientation(LinearLayout.VERTICAL);
        realmHeadings.setGravity(Gravity.CENTER_VERTICAL);
        TextView realmCaption = label("CURRENT REALM", 10, 0xffF7DEFA, true);
        realmHeadings.addView(realmCaption);
        TextView realmTitle = label(CharoiteEnvironments.activeName(this),
                30, Color.WHITE, true);
        realmTitle.setMaxLines(2);
        realmTitle.setEllipsize(TextUtils.TruncateAt.END);
        realmTitle.setShadowLayer(dp(3), 0, dp(1), 0x66000000);
        LinearLayout.LayoutParams realmTitleParams = new LinearLayout.LayoutParams(-1, -2);
        realmTitleParams.topMargin = dp(3);
        realmHeadings.addView(realmTitle, realmTitleParams);

        // The large artwork is the background of the *text*, not an icon beside it.
        FrameLayout.LayoutParams headingParams = new FrameLayout.LayoutParams(
                -1, -2, Gravity.CENTER_VERTICAL | Gravity.START);
        realmBanner.addView(realmHeadings, headingParams);
        main.addView(realmBanner, new LinearLayout.LayoutParams(-1, dp(120)));
        spacer(12);

        libraryScreen = new LinearLayout(this);
        libraryScreen.setOrientation(LinearLayout.VERTICAL);
        main.addView(libraryScreen);
        sectionTitle(libraryScreen, "Library", "Your games in " + CharoiteEnvironments.activeName(this) + ".");
        libraryArea = new LinearLayout(this);
        libraryArea.setOrientation(LinearLayout.VERTICAL);
        libraryScreen.addView(libraryArea);
        libraryScreen.addView(label("Only shortcuts you choose appear here. Removing a shortcut never uninstalls the game.", 13, SECONDARY, false));
        libraryScreen.addView(outlinedButton("ADD INSTALLED GAME SHORTCUT",
                () -> { showSection(1); findInstalledGames(false); }));
        libraryScreen.addView(outlinedButton("REMOVE ALL LIBRARY SHORTCUTS",
                this::confirmClearLibraryShortcuts));
        spacerIn(libraryScreen, 12);

        importScreen = new LinearLayout(this);
        importScreen.setOrientation(LinearLayout.VERTICAL);
        main.addView(importScreen);
        sectionTitle(importScreen, "Setup", "Install games into " + CharoiteEnvironments.activeName(this) + ".");
        setupArea = new LinearLayout(this);
        setupArea.setOrientation(LinearLayout.VERTICAL);
        importScreen.addView(setupArea);

        LinearLayout folderCard = card();
        folderCard.addView(label("01   IMPORT GAME OR INSTALLER FOLDER", 12, GOLD, true));
        folderCard.addView(label("Select a complete folder to copy into this environment. Importing never launches an .exe. Play imported games from Library, or start an installer explicitly from Setup.", 13, SECONDARY, false));
        folderButton = button("IMPORT GAME FOLDER", () -> {
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
        exeCard.addView(label("For installers with adjacent .bin/.cab/data files, import the complete folder instead of a lone EXE. If multiple setup programs are found, Charoite will ask which one you want to run.", 12, SECONDARY, false));
        installerFolderButton = outlinedButton("IMPORT COMPLETE INSTALLER FOLDER", () -> {
            Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
            picker.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION |
                    Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            startActivityForResult(picker, INSTALLER_FOLDER_REQUEST);
        });
        exeCard.addView(installerFolderButton);
        importScreen.addView(exeCard);
        spacerIn(importScreen, 12);

        // Battle.net is a separate installed environment, not an importer
        // panel shown in Touhou Realm or General Gaming.
        battleNetDownloadButton = null;
        battleNetInstallButton = null;
        battleNetOpenButton = null;
        battleNetOriginalButton = null;
        battleNetDirectButton = null;
        battleNetLaunchCompatButton = null;
        battleNetGpuProcessButton = null;
        battleNetRpcStartupButton = null;
        battleNetWineProbeButton = null;
        battleNetLiveMonitorButton = null;
        battleNetBrowserSettingsButton = null;
        battleNetBrowserCacheButton = null;
        battleNetCefReportButton = null;
        battleNetCompatButton = null;
        battleNetDiagnoseButton = null;
        battleNetDownloadStatus = null;
        if (CharoiteEnvironments.isBattleNet(this)) {
            LinearLayout battleCard = card();
            battleCard.addView(label("BATTLE.NET WINDOWS DESKTOP LAUNCHER",
                    16, FOREGROUND, true));
            battleCard.addView(label(
                    "Downloads Blizzard's latest official PC installer into this realm's C: drive. " +
                    "Downloading does not run the installer. Blizzard's installed launcher " +
                    "updates itself and its games through its own Windows client.",
                    13, SECONDARY, false));
            battleNetDownloadStatus = label("Checking local installer and launcher…",
                    12, SECONDARY, false);
            battleCard.addView(battleNetDownloadStatus);
            battleNetDownloadButton = button("DOWNLOAD LATEST BATTLE.NET INSTALLER",
                    this::downloadBattleNetInstaller);
            battleCard.addView(battleNetDownloadButton);
            battleNetInstallButton = outlinedButton("RUN DOWNLOADED WINDOWS INSTALLER",
                    this::installBattleNet);
            battleCard.addView(battleNetInstallButton);
            battleNetOpenButton = outlinedButton("OPEN BATTLE.NET (DIRECT SAFE BROWSER)",
                    this::openBattleNet);
            battleCard.addView(battleNetOpenButton);
            battleNetOriginalButton = outlinedButton("OPEN BATTLE.NET (ORIGINAL)",
                    this::openBattleNetOriginal);
            battleCard.addView(battleNetOriginalButton);
            battleNetDirectButton = outlinedButton("OPEN BATTLE.NET.EXE (DIRECT, SAFE GPU)",
                    this::openBattleNetDirect);
            battleCard.addView(battleNetDirectButton);
            battleNetLaunchCompatButton = outlinedButton(
                    "OPEN BATTLE.NET (COMPATIBILITY GRAPHICS)", this::openBattleNetCompatibility);
            battleCard.addView(battleNetLaunchCompatButton);
            battleNetGpuProcessButton = outlinedButton(
                    "TRY BATTLE.NET (CEF GPU PROCESS TEST)", this::openBattleNetGpuProcess);
            battleCard.addView(battleNetGpuProcessButton);
            battleNetRpcStartupButton = outlinedButton(
                    "TRY BATTLE.NET (START WINE RPC SERVICE)",
                    this::confirmBattleNetRpcStartup);
            battleCard.addView(battleNetRpcStartupButton);
            battleCard.addView(label(
                    "RpcSs before-client startup and restoration have been " +
                    "verified on the phone. The opt-in dialog now also offers " +
                    "a combined RPC + graphics experiment using WineD3D/VirGL. " +
                    "Both modes leave saved container settings and game data unchanged.",
                    12, SECONDARY, false));
            battleNetBrowserSettingsButton = outlinedButton(
                    "APPLY BROWSER ACCELERATION FIX (BACKUP)", this::applyBattleNetBrowserFix);
            battleCard.addView(battleNetBrowserSettingsButton);
            battleNetCefReportButton = outlinedButton("VIEW BATTLE.NET LOGIN / CEF REPORT",
                    this::showBattleNetCefReport);
            battleCard.addView(battleNetCefReportButton);
            battleNetBrowserCacheButton = outlinedButton(
                    "BACK UP + RESET BATTLE.NET BROWSER CACHE", this::confirmBattleNetBrowserCacheReset);
            battleCard.addView(battleNetBrowserCacheButton);
            battleCard.addView(label("CEF GPU Process Test uses --in-process-gpu for " +
                    "one launch instead of disabling the browser GPU. This is an " +
                    "experimental CEF startup option, not an established fix. " +
                    "It changes no saved settings or installed files.",
                    12, SECONDARY, false));
            battleCard.addView(label("Agent and Battle.net processes already run, " +
                    "so focus on why the Chromium login interface is stuck. " +
                    "The optional cache reset moves only launcher browser cache " +
                    "folders to timestamped backups. The Agent, installed games " +
                    "and saved settings are not deleted.",
                    12, SECONDARY, false));
            battleCard.addView(label("Safe Browser launches Battle.net.exe directly " +
                    "when it exists, bypassing the bootstrap window. It also passes " +
                    "--disable-gpu and the Wine CEF workarounds. ORIGINAL launches " +
                    "Battle.net Launcher.exe without overrides. Use the diagnostics " +
                    "to verify saved browser hardware-acceleration settings; " +
                    "a command-line GPU flag alone does not change those settings. " +
                    "Installed games, Agent data, accounts and the Wine prefix are preserved.",
                    12, SECONDARY, false));
            battleNetLiveMonitorButton = outlinedButton("VIEW LIVE AGENT MONITOR",
                    this::showBattleNetLiveMonitor);
            battleCard.addView(battleNetLiveMonitorButton);
            battleCard.addView(label("Live Agent Monitor runs automatically when you " +
                    "launch the installed Battle.net client. Open Battle.net, leave " +
                    "the spinner displayed briefly, return to Portal, then tap " +
                    "VIEW LIVE AGENT MONITOR here. If Wine never started the " +
                    "monitor, this view reports that explicitly.",
                    12, SECONDARY, false));
            battleNetDiagnoseButton = outlinedButton("CHECK LAUNCHER + AGENT DIAGNOSTICS",
                    this::showBattleNetAgentDiagnostics);
            battleCard.addView(battleNetDiagnoseButton);
            battleNetWineProbeButton = outlinedButton(
                    "TEST WINE DNS / HTTPS / AGENT", this::runBattleNetWineNetworkProbe);
            battleCard.addView(battleNetWineProbeButton);
            battleCard.addView(label("This optional test runs entirely inside the " +
                    "Battle.net Wine environment. It checks Windows DNS, HTTPS " +
                    "and whether Agent.exe is running; it never signs into Blizzard. " +
                    "Return to Setup and open diagnostics for the result.",
                    12, SECONDARY, false));
            battleNetCompatButton = outlinedButton("RETRY SETUP: COMPATIBILITY MODE",
                    this::retryBattleNetCompatibility);
            battleCard.addView(battleNetCompatButton);
            battleCard.addView(label(
                    "Update Agent error BLZBNTBTS0000005C can be a Windows process, DLL, " +
                    "network or Wine compatibility failure. Check diagnostics first. " +
                    "Compatibility Retry temporarily uses WineD3D/VirGL and disables Wine " +
                    "ESYNC/FSYNC for one attempt. Neither option deletes Agent files or games.",
                    12, SECONDARY, false));
            battleCard.addView(label(
                    "Blizzard account sign-in happens inside its Windows client, not Charoite. " +
                    "If its automatic updater fails, check diagnostics before trying the installer again. " +
                    "Diablo IV requires DirectX 12; this Android runtime does not yet have verified " +
                    "Diablo IV / VKD3D game compatibility. At least 90 GB of PC game storage is listed.",
                    12, SECONDARY, false));
            importScreen.addView(battleCard);
            spacerIn(importScreen, 12);
        }

        LinearLayout scanCard = card();
        scanCard.addView(label("03   FIND INSTALLED GAMES", 12, GOLD, true));
        scanCard.addView(label("Find Windows games in this environment, then choose exactly which ones receive Library shortcuts. Scanning never adds shortcuts automatically.", 13, SECONDARY, false));
        scanButton = outlinedButton("FIND GAMES / ADD SHORTCUTS", () -> findInstalledGames(false));
        scanCard.addView(scanButton);
        importScreen.addView(scanCard);
        spacerIn(importScreen, 15);
        importScreen.addView(label(CharoiteEnvironments.isTouhou(this)
                ? "Touhou Realm uses its original Windows storage. Existing installed games and saves remain in place, and installer-selected destinations are preserved."
                : "This environment has a separate Windows C: drive and game library. Installer-selected destinations are preserved; no games are bundled.", 12, SECONDARY, false));

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
        environmentExportButton = outlinedButton("EXPORT ENVIRONMENT (.CENV)", this::showEnvironmentExporter);
        environmentCard.addView(environmentExportButton);
        environmentCard.addView(label("Install opens a downloaded .cenv file from your phone. Create saves a reusable .cenv profile to a folder you choose. Export an existing realm to share its settings. These files contain no Windows games or saves.", 12, SECONDARY, false));
        systemScreen.addView(environmentCard);
        spacerIn(systemScreen, 12);

        LinearLayout fileCard = card();
        fileCard.addView(label("Windows C: file manager", 17, FOREGROUND, true));
        fileCard.addView(label("Browse all existing Charoite Wine containers, including older ones. Inspect games and save files, export copies to Samsung My Files, or import files without overwriting.", 12, SECONDARY, false));
        fileCard.addView(outlinedButton("OPEN WINDOWS FILE MANAGER", () ->
                startActivity(new Intent(this, CharoiteFileManagerActivity.class))));
        fileCard.addView(label("For an old separate Winlator installation, choose an exported/accessible backup. Android prevents Charoite from reading another app's private /data/user/0 files.", 12, SECONDARY, false));
        systemScreen.addView(fileCard);
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
        graphicsCard.addView(label(
                "Charoite Core automatically selects proven compatibility " +
                "profiles when a game starts. Puppet Dance Performance uses " +
                "DXVK 1.10.3 + Turnip without any manual selection. " +
                "Other games keep their own saved settings.", 12, SECONDARY, false));
        graphicsCard.addView(label("Japanese Windows text support uses Charoite Core's CP932 locale and licensed IPA Gothic/Noto fonts. Touhou Realm enables it automatically; other environments can opt in. Restart a Windows program to apply the language change.", 12, SECONDARY, false));
        japaneseButton = outlinedButton("JAPANESE TEXT SUPPORT: OFF", this::toggleJapaneseCompatibility);
        graphicsCard.addView(japaneseButton);
        graphicsCard.addView(label("Optional: repair Japanese text in Inno Setup installers that contain Japanese Unicode text. The helper checks the Wine charset and wizard before attaching. Leave disabled unless needed.", 12, SECONDARY, false));
        installerFontButton = outlinedButton("INSTALLER FONT REPAIR: OFF", this::toggleInstallerFontRepair);
        graphicsCard.addView(installerFontButton);
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
        debugCard.addView(label("Run a local Windows text-rendering test using Japanese fonts. Compare native Unicode and CP932 output to help diagnose other games. Does not modify installed games or Wine DLLs.", 12, SECONDARY, false));
        debugCard.addView(outlinedButton("RUN WINDOWS TEXT RENDERING TEST",
                this::runWindowsTextRenderingTest));
        debugCard.addView(label("If the standard Japanese text test passes, compare five Win32 owner-drawn GDI methods against the same Unicode characters.", 12, SECONDARY, false));
        debugCard.addView(outlinedButton("RUN OWNER-DRAW TEXT RENDERING TEST",
                this::runOwnerDrawTextRenderingTest));
        diagnosticButton = outlinedButton("VIEW LAST LAUNCH DIAGNOSTICS", this::showDiagnostics);
        debugCard.addView(diagnosticButton);
        systemScreen.addView(debugCard);
        spacerIn(systemScreen, 18);
        systemScreen.addView(label("Charoite Portal · Charoite Core " + CharoiteCore.VERSION + " · Charoite Games. Windows compatibility powered by Wine and Box64. Third-party source credits and license notices are included with the app. No games included.", 11, SECONDARY, false));

        refreshLibrary();
        refreshWallpaperViews();
        showSection(selectedSection);
    }

    /** Never install into Touhou or General Gaming, even if a late callback
     * returns after the user switches realms. */
    private File battleNetRoot() {
        if (!CharoiteEnvironments.isBattleNet(this) || containerId <= 0)
            throw new IllegalStateException("Switch to the Battle.net Gaming environment");
        Container current = new ContainerManager(this).getContainerById(containerId);
        if (current == null || current.id != CharoiteEnvironments.activeContainerId(this))
            throw new IllegalStateException("Battle.net container is not ready");
        return current.getRootDir();
    }

    private void downloadBattleNetInstaller() {
        if (busy) return;
        final File root;
        try { root = battleNetRoot(); }
        catch (Exception ex) { setStatus(ex.getMessage()); return; }
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Download latest Battle.net for Windows?")
                .setMessage("Charoite will fetch Blizzard's current Windows installer from its " +
                        "official live downloader into this environment only. It will not run " +
                        "any executable until you select Run Installer. " +
                        "The existing Blizzard installation and games will not be modified.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Download", (dialog, which) -> {
                    busy = true;
                    setStatus("Downloading current Battle.net Windows installer from Blizzard…");
                    updateButtons();
                    worker.execute(() -> {
                        try {
                            CharoiteBattleNetSupport.Download result =
                                    CharoiteBattleNetSupport.downloadLatestInstaller(root);
                            runOnUiThread(() -> {
                                busy = false;
                                updateButtons();
                                setStatus("Battle.net Windows installer saved (" +
                                        (result.bytes / 1024) + " KB, SHA-256 " +
                                        result.sha256.substring(0, 12) +
                                        "…). Select Run Installer to install it.");
                            });
                        } catch (Exception failure) {
                            runOnUiThread(() -> {
                                busy = false;
                                updateButtons();
                                setStatus("Blizzard installer download failed: " +
                                        failure.getMessage() +
                                        ". Your previously downloaded installer remains intact.");
                            });
                        }
                    });
                }).show();
    }

    private void installBattleNet() {
        if (busy) return;
        try {
            File exe = CharoiteBattleNetSupport.downloadedInstaller(battleNetRoot());
            if (exe == null)
                throw new IllegalStateException("Download a valid Blizzard Windows installer first");
            // Explicit installer action only: reuse ordinary Wine installer
            // lifecycle, preserving installed files and the selected path.
            CharoiteGameSessions.launch(this, XServerDisplayActivity.class,
                    containerId, exe.getAbsolutePath(), true, false);
        } catch (Exception error) {
            setStatus("Cannot start Battle.net setup: " + error.getMessage());
        }
    }

    private void openBattleNet() {
        if (busy) return;
        try {
            File root = battleNetRoot();
            // Battle.net client processes were found alive even while its
            // bootstrap splash remained spinning. Run the installed client
            // directly by default; ORIGINAL retains the normal bootstrap.
            File exe = CharoiteBattleNetSupport.installedDirectClient(root);
            if (exe == null) exe = CharoiteBattleNetSupport.installedLauncher(root);
            if (exe == null)
                throw new IllegalStateException("No installed Battle.net launcher/client");
            // Windows login needs pointer and keyboard, not gamepad controls.
            CharoiteGameSessions.launch(this, XServerDisplayActivity.class,
                    containerId, exe.getAbsolutePath(), false, false,
                    false, true);
        } catch (Exception error) {
            setStatus("Cannot open Battle.net: " + error.getMessage());
        }
    }

    private void openBattleNetOriginal() {
        if (busy) return;
        try {
            File exe = CharoiteBattleNetSupport.installedLauncher(battleNetRoot());
            if (exe == null)
                throw new IllegalStateException("Battle.net launcher not installed");
            CharoiteGameSessions.launch(this, XServerDisplayActivity.class,
                    containerId, exe.getAbsolutePath(), false, false);
        } catch (Exception error) {
            setStatus("Cannot open original Battle.net: " + error.getMessage());
        }
    }

    /** Launch installed Blizzard client directly to bypass stuck bootstrapper. */
    private void openBattleNetDirect() {
        if (busy) return;
        try {
            File exe = CharoiteBattleNetSupport.installedDirectClient(battleNetRoot());
            if (exe == null) {
                setStatus("Battle.net.exe is not installed; launcher-only install detected. " +
                        "Use Safe Browser or check Agent diagnostics.");
                return;
            }
            CharoiteGameSessions.launch(this, XServerDisplayActivity.class,
                    containerId, exe.getAbsolutePath(), false, false,
                    false, true);
        } catch (Exception error) {
            setStatus("Cannot open Battle.net client: " + error.getMessage());
        }
    }

    /**
     * A launcher-side compatibility attempt, not an installer retry.
     * Switches to WineD3D/VirGL, avoids ESYNC/FSYNC and requests the CEF
     * software renderer only for this one Battle.net launch.
     */
    private void openBattleNetCompatibility() {
        if (busy) return;
        try {
            File root = battleNetRoot();
            File exe = CharoiteBattleNetSupport.installedDirectClient(root);
            if (exe == null) exe = CharoiteBattleNetSupport.installedLauncher(root);
            if (exe == null)
                throw new IllegalStateException("No installed Battle.net launcher");
            CharoiteGameSessions.launch(this, XServerDisplayActivity.class,
                    containerId, exe.getAbsolutePath(), false, false, true, true);
        } catch (Exception error) {
            setStatus("Cannot open compatibility launcher: " + error.getMessage());
        }
    }

    /** Alternative single-launch Chromium GPU-process diagnostic. */
    private void openBattleNetGpuProcess() {
        if (busy) return;
        try {
            File root = battleNetRoot();
            File exe = CharoiteBattleNetSupport.installedDirectClient(root);
            if (exe == null) exe = CharoiteBattleNetSupport.installedLauncher(root);
            if (exe == null)
                throw new IllegalStateException("No installed Battle.net client or launcher");
            CharoiteGameSessions.launch(this, XServerDisplayActivity.class,
                    containerId, exe.getAbsolutePath(), false, false,
                    false, false, true);
        } catch (Exception error) {
            setStatus("Cannot test Battle.net CEF GPU process: " + error.getMessage());
        }
    }

    /** Only this explicitly consented Battle.net test initializes RpcSs
     * BEFORE the client. The optional graphics fallback changes per-launch
     * environment variables and renderer, never the saved Wine container. */
    private void launchBattleNetRpcTest(boolean compatibilityGraphics) {
        if (busy) return;
        try {
            File root = battleNetRoot();
            File exe = CharoiteBattleNetSupport.installedDirectClient(root);
            if (exe == null)
                exe = CharoiteBattleNetSupport.installedLauncher(root);
            if (exe == null)
                throw new IllegalStateException(
                        "Battle.net client or launcher not installed");
            CharoiteGameSessions.launch(this, XServerDisplayActivity.class,
                    containerId, exe.getAbsolutePath(), false, false,
                    compatibilityGraphics, true, false, true);
        } catch (Exception error) {
            setStatus("RpcSs launch test failed: " + error.getMessage());
        }
    }

    /** Explicitly selected service-start experiment. Service recovery marker
     * handles an interrupted startup-config rollback in this Wine prefix.
     * The separate graphics fallback is deliberately not automatic. */
    private void confirmBattleNetRpcStartup() {
        if (busy) return;
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Test Battle.net RPC + browser startup?")
                .setMessage("The Galaxy tests confirm that Wine RpcSs starts " +
                        "before Battle.net and its original Disabled startup " +
                        "configuration is restored afterward. The sign-in " +
                        "browser still needs investigation. " +
                        "TRY ONCE repeats the existing service and safe-browser " +
                        "test. RPC + GRAPHICS also selects temporary WineD3D/" +
                        "VirGL rendering and disables ESYNC/FSYNC for this " +
                        "Battle.net session, to isolate Chromium graphics " +
                        "and synchronization problems. Both tests use the " +
                        "same bounded RPC restoration check and "--" +
                        "disable-gpu browser option. No installed game, " +
                        "Blizzard data, Wine prefix or other environment is " +
                        "reset. Close older Battle.net sessions first. " +
                        "Neither mode guarantees login.")
                .setNegativeButton("Cancel", null)
                .setNeutralButton("RPC + graphics",
                        (dialog, which) -> launchBattleNetRpcTest(true))
                .setPositiveButton("Try once",
                        (dialog, which) -> launchBattleNetRpcTest(false))
                .show();
    }

    /** Explicitly requested browser preference change; creates rollback copy. */
    private void applyBattleNetBrowserFix() {
        if (busy) return;
        final File root;
        try { root = battleNetRoot(); }
        catch (Exception error) { setStatus(error.getMessage()); return; }
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Disable Battle.net browser acceleration?")
                .setMessage("Battle.net stores browser acceleration in " +
                        "its own settings file. Charoite will back up that " +
                        "existing file before setting HardwareAcceleration=false. " +
                        "No files, Agent installations, game content, or account " +
                        "data will be deleted. Close the running launcher first.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Apply with backup", (dialog, which) -> {
                    busy = true;
                    updateButtons();
                    worker.execute(() -> {
                        String status;
                        try {
                            status = CharoiteBattleNetSupport.applyBrowserSoftwareSetting(root);
                        } catch (Exception failure) {
                            status = "Battle.net setting unchanged: " +
                                    failure.getClass().getSimpleName();
                        }
                        final String result = status;
                        runOnUiThread(() -> {
                            busy = false;
                            updateButtons();
                            setStatus(result);
                        });
                    });
                }).show();
    }

    /** Read-only browser config and error-category report, isolated from Agent. */
    private void showBattleNetCefReport() {
        final File root;
        try { root = battleNetRoot(); }
        catch (Exception error) { setStatus(error.getMessage()); return; }
        String report = CharoiteBattleNetSupport.inspectInSessionAgentMonitor(root) +
                "\n\n" + CharoiteBattleNetSupport.inspectBrowserPreferences(root) +
                "\n\n" + CharoiteBattleNetSupport.inspectBrowserLogCategories(root);
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Battle.net login / CEF diagnostics")
                .setMessage(report)
                .setPositiveButton("Copy report", (dialog, which) -> {
                    ClipboardManager clipboard = (ClipboardManager)
                            getSystemService(Context.CLIPBOARD_SERVICE);
                    clipboard.setPrimaryClip(ClipData.newPlainText(
                            "Battle.net CEF diagnostic summary", report));
                })
                .setNegativeButton("Close", null)
                .show();
    }

    /** Consent required: rename cache directories without removing files. */
    private void confirmBattleNetBrowserCacheReset() {
        if (busy) return;
        final File root;
        try { root = battleNetRoot(); }
        catch (Exception error) { setStatus(error.getMessage()); return; }
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Back up Battle.net browser caches?")
                .setMessage("Close Battle.net completely first. Charoite will " +
                        "rename ONLY the browser cache folders in this Wine " +
                        "environment to timestamped backups. No cache data " +
                        "will be deleted, and Agent files, installed games, " +
                        "login settings and all other environments stay unchanged. " +
                        "The cache can be rebuilt when Battle.net restarts.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Back up and reset", (dialog, which) -> {
                    busy = true;
                    updateButtons();
                    worker.execute(() -> {
                        String result;
                        try {
                            result = CharoiteBattleNetSupport.backupAndResetBrowserCache(root);
                        } catch (Exception error) {
                            result = "Cache reset not completed: " +
                                    error.getClass().getSimpleName() +
                                    ". No cache backups or games were deleted.";
                        }
                        final String message = result;
                        runOnUiThread(() -> {
                            busy = false;
                            updateButtons();
                            new androidx.appcompat.app.AlertDialog.Builder(this)
                                    .setTitle("Battle.net browser cache result")
                                    .setMessage(message)
                                    .setPositiveButton("Close", null).show();
                        });
                    });
                }).show();
    }

    private void runBattleNetWineNetworkProbe() {
        if (busy) return;
        try {
            File probe = CharoiteBattleNetSupport.prepareGuestNetworkProbe(
                    this, battleNetRoot());
            // The normal Win32 runtime starts our stand-alone probe and
            // exits when the program terminates. No installer scan, no reset,
            // no game shortcuts or Blizzard account files touched.
            setStatus("Launching Battle.net network probe inside Wine. " +
                    "Return here and open Launcher + Agent Diagnostics for its report.");
            CharoiteGameSessions.launch(this, XServerDisplayActivity.class,
                    containerId, probe.getAbsolutePath(), false, false);
        } catch (Exception error) {
            setStatus("Wine probe cannot start: " + error.getClass().getSimpleName());
        }
    }

    /** Always keep the live Agent report on its own screen instead of at
     * the bottom of a long launcher+network AlertDialog scroll area.
     */
    private void showBattleNetLiveMonitor() {
        final File root;
        try { root = battleNetRoot(); }
        catch (Exception error) { setStatus(error.getMessage()); return; }
        String report = CharoiteBattleNetSupport.inspectInSessionAgentMonitor(root);
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Battle.net Live Agent Monitor")
                .setMessage(report)
                .setPositiveButton("Copy monitor", (dialog, which) -> {
                    ClipboardManager clipboard = (ClipboardManager)
                            getSystemService(Context.CLIPBOARD_SERVICE);
                    clipboard.setPrimaryClip(ClipData.newPlainText(
                            "Charoite Battle.net live Agent monitor", report));
                    setStatus("Live Agent monitor copied; no Blizzard files changed.");
                })
                .setNegativeButton("Close", null)
                .show();
    }

    /** Read only: inspect whether Blizzard actually downloaded Agent.exe
     * and whether agent logs exist. No automatic repairs or data removal. */
    private void showBattleNetAgentDiagnostics() {
        final File root;
        try { root = battleNetRoot(); }
        catch (Exception e) { setStatus(e.getMessage()); return; }
        String report = CharoiteBattleNetSupport.inspectInSessionAgentMonitor(root) +
                "\n\n" + CharoiteBattleNetSupport.inspectBrowserPreferences(root) +
                "\n\n" + CharoiteBattleNetSupport.inspectBrowserLogCategories(root) +
                "\n\n" + CharoiteBattleNetSupport.inspectLauncherStartup(root) +
                "\n\n" + CharoiteBattleNetSupport.inspectAgent(root) +
                "\n\n" + CharoiteBattleNetSupport.inspectGuestNetworkProbe(root);
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Battle.net launcher and Agent diagnostics")
                .setMessage(report)
                .setPositiveButton("Copy report", (dialog, which) -> {
                    ClipboardManager clipboard = (ClipboardManager)
                            getSystemService(Context.CLIPBOARD_SERVICE);
                    clipboard.setPrimaryClip(ClipData.newPlainText(
                            "Battle.net Update Agent diagnostic", report));
                    setStatus("Agent diagnostic copied. No game files changed.");
                })
                .setNegativeButton("Close", null)
                .show();
    }

    private void retryBattleNetCompatibility() {
        if (busy) return;
        try {
            File exe = CharoiteBattleNetSupport.downloadedInstaller(battleNetRoot());
            if (exe == null)
                throw new IllegalStateException("Download the official Windows installer first");
            new androidx.appcompat.app.AlertDialog.Builder(this)
                    .setTitle("Retry Battle.net setup?")
                    .setMessage("This experimental one-session fallback selects " +
                            "WineD3D/VirGL instead of DXVK and disables Wine " +
                            "ESYNC/FSYNC. It may help if the updater is failing in " +
                            "the current runtime, but success is not guaranteed. " +
                            "Existing Wine settings, games, saves and installer files remain intact.")
                    .setNegativeButton("Cancel", null)
                    .setPositiveButton("Try compatibility launch", (dialog, which) -> {
                        try {
                            CharoiteGameSessions.launch(this,
                                    XServerDisplayActivity.class,
                                    containerId, exe.getAbsolutePath(), true, false, true);
                        } catch (Exception e) {
                            setStatus("Compatibility retry failed: " + e.getMessage());
                        }
                    }).show();
        } catch (Exception error) {
            setStatus("Cannot retry Battle.net: " + error.getMessage());
        }
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

    /** Install only a user-selected, validated .cenv file from Android storage. */
    private void showEnvironmentInstaller() {
        if (busy || wallpaperBusy) return;
        Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        picker.addCategory(Intent.CATEGORY_OPENABLE);
        // Android's document providers do not have a universal MIME for .cenv.
        // Choose any type then STRICTLY validate .cenv extension and JSON data.
        picker.setType("*/*");
        picker.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        startActivityForResult(picker, ENVIRONMENT_OPEN_REQUEST);
    }

    /** Choose a name first, then the phone's Save As folder and .cenv file. */
    private void showEnvironmentCreator() {
        if (busy || wallpaperBusy) return;
        EditText nameInput = new EditText(this);
        nameInput.setSingleLine(true);
        nameInput.setHint("e.g. Classic RPGs");
        nameInput.setPadding(dp(22), dp(12), dp(22), dp(12));
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Create environment")
                .setMessage("Choose a name. Next, select where to save its .cenv profile on your phone. The environment is added only after the file saves successfully. Games and saves are never exported.")
                .setView(nameInput)
                .setPositiveButton("Choose save location", (dialog, which) -> {
                    try {
                        String name = CharoiteEnvironmentFiles.normalizeName(
                                nameInput.getText().toString());
                        JSONArray items = CharoiteEnvironments.list(this);
                        for (int i = 0; i < items.length(); i++) {
                            JSONObject item = items.optJSONObject(i);
                            if (item != null && name.equalsIgnoreCase(item.optString("name")))
                                throw new IllegalArgumentException("An environment already uses that name.");
                        }
                        pendingEnvironmentName = name;
                        startEnvironmentSavePicker(name, ENVIRONMENT_CREATE_REQUEST);
                    } catch (Exception error) {
                        showEnvironmentError(error);
                    }
                })
                .setNegativeButton("Cancel", null).show();
    }

    /** Export existing Touhou/General/custom profile; never exports its Wine C: or games. */
    private void showEnvironmentExporter() {
        if (busy || wallpaperBusy) return;
        pendingExportEnvironmentId = CharoiteEnvironments.activeId(this);
        startEnvironmentSavePicker(CharoiteEnvironments.activeName(this),
                ENVIRONMENT_EXPORT_REQUEST);
    }

    private void startEnvironmentSavePicker(String name, int requestCode) {
        Intent save = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        save.addCategory(Intent.CATEGORY_OPENABLE);
        save.setType("application/octet-stream");
        save.putExtra(Intent.EXTRA_TITLE, CharoiteEnvironmentFiles.fileNameFor(name));
        save.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        startActivityForResult(save, requestCode);
    }

    private JSONObject createEnvironmentManifest(String name, boolean fromCurrent)
            throws Exception {
        String theme = fromCurrent ? CharoiteEnvironments.activeTheme(this) : "cosmic";
        if ("touhou".equals(theme) || "sakura".equals(theme)) theme = "sakura";
        else if (!"battlenet".equals(theme)) theme = "cosmic";
        return CharoiteEnvironmentFiles.create(name, theme,
                fromCurrent && CharoiteCore.compatibleGraphics(this),
                fromCurrent ? CharoiteCore.getDisplayModeIndex(this) : 0,
                fromCurrent && CharoiteCore.isDesktopPointerCaptured(this),
                fromCurrent && CharoiteCore.japaneseCompatibilityEnabled(this),
                fromCurrent && CharoiteCore.installerFontRepairEnabled(this));
    }

    private void saveEnvironmentDocument(Uri uri, boolean creating) {
        String name = creating ? pendingEnvironmentName :
                CharoiteEnvironments.activeName(this);
        if (!creating && (pendingExportEnvironmentId == null ||
                !pendingExportEnvironmentId.equals(CharoiteEnvironments.activeId(this)))) {
            showEnvironmentError(new IllegalStateException("Active environment changed. Export again."));
            return;
        }
        if (name == null || name.isEmpty()) {
            showEnvironmentError(new IllegalStateException("Missing environment to save."));
            return;
        }
        try {
            final JSONObject manifest = createEnvironmentManifest(name, !creating);
            final byte[] data = CharoiteEnvironmentFiles.encode(manifest);
            busy = true;
            updateButtons();
            worker.execute(() -> {
                try (java.io.OutputStream out = getContentResolver().openOutputStream(uri, "w")) {
                    if (out == null) throw new java.io.IOException("Cannot write selected file.");
                    out.write(data);
                    out.flush();
                } catch (Exception error) {
                    runOnUiThread(() -> {
                        busy = false;
                        pendingEnvironmentName = null;
                        pendingExportEnvironmentId = null;
                        updateButtons();
                        showEnvironmentError(error);
                    });
                    return;
                }
                runOnUiThread(() -> {
                    busy = false;
                    pendingEnvironmentName = null;
                    pendingExportEnvironmentId = null;
                    try {
                        if (creating) {
                            JSONObject created = CharoiteEnvironments.create(this,
                                    manifest.getString("name"), manifest.getString("theme"));
                            activateEnvironment(created.getString("id"));
                            Toast.makeText(this, "Environment created and .cenv saved on your phone",
                                    Toast.LENGTH_LONG).show();
                        } else {
                            updateButtons();
                            Toast.makeText(this, "Environment .cenv saved on your phone",
                                    Toast.LENGTH_LONG).show();
                        }
                    } catch (Exception error) {
                        updateButtons();
                        showEnvironmentError(error);
                    }
                });
            });
        } catch (Exception error) {
            pendingEnvironmentName = null;
            pendingExportEnvironmentId = null;
            showEnvironmentError(error);
        }
    }

    private void openEnvironmentDocument(Uri uri) {
        DocumentFile document = DocumentFile.fromSingleUri(this, uri);
        String fileName = document == null ? null : document.getName();
        if (fileName == null || !fileName.toLowerCase(Locale.ROOT).endsWith(
                CharoiteEnvironmentFiles.EXTENSION)) {
            showEnvironmentError(new IllegalArgumentException(
                    "Select a Charoite Portal .cenv environment file."));
            return;
        }
        busy = true;
        updateButtons();
        worker.execute(() -> {
            final JSONObject manifest;
            try (InputStream input = getContentResolver().openInputStream(uri)) {
                manifest = CharoiteEnvironmentFiles.read(input);
            } catch (Exception error) {
                runOnUiThread(() -> {
                    busy = false;
                    updateButtons();
                    showEnvironmentError(error);
                });
                return;
            }
            runOnUiThread(() -> {
                busy = false;
                updateButtons();
                new androidx.appcompat.app.AlertDialog.Builder(this)
                        .setTitle("Install environment from file?")
                        .setMessage("Name: " + manifest.optString("name") +
                                "\nTheme: " + manifest.optString("theme") +
                                "\n\nA new isolated Windows container will be prepared. The .cenv profile contains settings, not games or saved data.")
                        .setPositiveButton("Install", (dialog, which) ->
                                installValidatedEnvironment(manifest))
                        .setNegativeButton("Cancel", null)
                        .show();
            });
        });
    }

    private void installValidatedEnvironment(JSONObject manifest) {
                try {
                    JSONObject installed = CharoiteEnvironments.installFromFile(this, manifest);
                    String id = installed.getString("id");
                    // Settings are scoped by active environment ID, not global
                    // graphics/display keys. Never overwrite Touhou settings.
                    if (!CharoiteEnvironments.switchTo(this, id))
                        throw new IllegalStateException("Could not activate imported environment.");
                    JSONObject settings = manifest.getJSONObject("settings");
                    CharoiteCore.setCompatibleGraphics(this,
                            settings.getBoolean("compatibilityGraphics"));
                    CharoiteCore.setDisplayMode(this, settings.getInt("displayMode"));
                    CharoiteCore.setDesktopPointerCaptured(this,
                            settings.getBoolean("capturePointer"));
                    CharoiteCore.setJapaneseCompatibilityEnabled(this,
                            settings.optBoolean("japaneseText", false));
                    CharoiteCore.setInstallerFontRepairEnabled(this,
                            settings.optBoolean("installerFontRepair", false));
                    activateEnvironment(id);
                    Toast.makeText(this, "Environment installed from .cenv",
                            Toast.LENGTH_LONG).show();
                } catch (Exception error) {
                    updateButtons();
                    showEnvironmentError(error);
                }
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
        if (environmentExportButton != null) environmentExportButton.setEnabled(!busy && !wallpaperBusy);
        if (runtimeLabel != null) runtimeLabel.setText(ready ?
                "Up to date • Wine and Box64 are ready for your games." :
                busy ? "Preparing this APK's bundled Wine / Box64 runtime automatically…" :
                "Engine not ready. Retry automatic preparation here if necessary.");
        folderButton.setEnabled(!busy && ready);
        installerButton.setEnabled(!busy && ready);
        if (installerFolderButton != null) installerFolderButton.setEnabled(!busy && ready);
        scanButton.setEnabled(!busy && ready);
        if (CharoiteEnvironments.isBattleNet(this)) {
            File battleRoot = null;
            try {
                Container current = new ContainerManager(this).getContainerById(containerId);
                if (current != null) battleRoot = current.getRootDir();
            } catch (Exception ignored) {}
            File setup = battleRoot == null ? null :
                    CharoiteBattleNetSupport.downloadedInstaller(battleRoot);
            File launcher = battleRoot == null ? null :
                    CharoiteBattleNetSupport.installedLauncher(battleRoot);
            if (battleNetDownloadButton != null)
                battleNetDownloadButton.setEnabled(!busy && ready);
            if (battleNetInstallButton != null)
                battleNetInstallButton.setEnabled(!busy && ready && setup != null);
            if (battleNetOpenButton != null)
                battleNetOpenButton.setEnabled(!busy && ready && launcher != null);
            if (battleNetOriginalButton != null)
                battleNetOriginalButton.setEnabled(!busy && ready && launcher != null);
            if (battleNetBrowserSettingsButton != null)
                battleNetBrowserSettingsButton.setEnabled(!busy && ready);
            if (battleNetBrowserCacheButton != null)
                battleNetBrowserCacheButton.setEnabled(!busy && ready);
            if (battleNetCefReportButton != null)
                battleNetCefReportButton.setEnabled(!busy && ready);
            if (battleNetLaunchCompatButton != null)
                battleNetLaunchCompatButton.setEnabled(!busy && ready && launcher != null);
            if (battleNetGpuProcessButton != null)
                battleNetGpuProcessButton.setEnabled(!busy && ready && launcher != null);
            if (battleNetRpcStartupButton != null)
                battleNetRpcStartupButton.setEnabled(!busy && ready && launcher != null);
            if (battleNetWineProbeButton != null)
                battleNetWineProbeButton.setEnabled(!busy && ready);
            if (battleNetLiveMonitorButton != null)
                battleNetLiveMonitorButton.setEnabled(!busy && ready);
            if (battleNetDirectButton != null) {
                File direct = null;
                if (ready) {
                    try { direct = CharoiteBattleNetSupport.installedDirectClient(battleNetRoot()); }
                    catch (Exception ignored) {}
                }
                battleNetDirectButton.setEnabled(!busy && ready && direct != null);
            }
            if (battleNetCompatButton != null)
                battleNetCompatButton.setEnabled(!busy && ready && setup != null);
            if (battleNetDiagnoseButton != null)
                battleNetDiagnoseButton.setEnabled(!busy && ready);
            if (battleNetDownloadStatus != null)
                battleNetDownloadStatus.setText(!ready ? "Preparing isolated Windows container…" :
                        (setup == null ? "Latest Windows installer not yet downloaded." :
                         "Windows installer downloaded: " + (setup.length() / 1024) + " KB.") +
                        (launcher == null ? "\nInstalled launcher not detected yet." :
                         "\nBattle.net Windows launcher detected. Open to update games."));
        }
        compatButton.setEnabled(!busy && ready);
        compatButton.setText(CharoiteCore.compatibleGraphics(this) ?
                "RESTORE NORMAL GRAPHICS" : "SWITCH TO COMPATIBILITY GRAPHICS");
        if (japaneseButton != null) {
            japaneseButton.setEnabled(!busy && ready);
            japaneseButton.setText(CharoiteCore.japaneseCompatibilityEnabled(this)
                    ? "JAPANESE TEXT SUPPORT: ON" : "JAPANESE TEXT SUPPORT: OFF");
        }
        if (installerFontButton != null) {
            installerFontButton.setEnabled(!busy && ready && CharoiteCore.japaneseCompatibilityEnabled(this));
            installerFontButton.setText(CharoiteCore.installerFontRepairEnabled(this)
                    ? "INSTALLER FONT REPAIR: ON" : "INSTALLER FONT REPAIR: OFF");
        }
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
    private void toggleJapaneseCompatibility() {
        if (busy || containerId <= 0) return;
        boolean enabled = !CharoiteCore.japaneseCompatibilityEnabled(this);
        CharoiteCore.setJapaneseCompatibilityEnabled(this, enabled);
        updateButtons();
        setStatus(enabled
                ? "Japanese support enabled for this realm. Restart Windows apps to apply."
                : "Japanese support disabled for this realm. Restart Windows apps to apply.");
    }

    private void toggleInstallerFontRepair() {
        if (busy || containerId <= 0 ||
                !CharoiteCore.japaneseCompatibilityEnabled(this)) return;
        boolean enabled = !CharoiteCore.installerFontRepairEnabled(this);
        CharoiteCore.setInstallerFontRepairEnabled(this, enabled);
        updateButtons();
        setStatus(enabled
                ? "Scoped Japanese installer font repair enabled for this environment."
                : "Installer font repair disabled. Standard Japanese fonts remain available.");
    }

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
        final String report = CharoiteDiagnostics.getReport(this);
        new androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("Windows game startup diagnostics")
            .setMessage(report)
            .setPositiveButton("Copy report", (dialog, which) -> {
                ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                clipboard.setPrimaryClip(ClipData.newPlainText("Charoite Portal startup report", report));
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
        if (resultCode != Activity.RESULT_OK || data == null || data.getData() == null) {
            if (requestCode == ENVIRONMENT_CREATE_REQUEST) pendingEnvironmentName = null;
            if (requestCode == ENVIRONMENT_EXPORT_REQUEST) pendingExportEnvironmentId = null;
            return;
        }
        Uri uri = data.getData();
        if (requestCode == FOLDER_REQUEST)
            importGame(uri, CharoiteGameImport.Selection.GAME_FOLDER);
        else if (requestCode == EXE_REQUEST)
            importGame(uri, CharoiteGameImport.Selection.STANDALONE_INSTALLER);
        else if (requestCode == INSTALLER_FOLDER_REQUEST)
            importGame(uri, CharoiteGameImport.Selection.INSTALLER_FOLDER);
        else if (requestCode == WALLPAPER_REQUEST) importLauncherWallpaper(uri);
        else if (requestCode == ENVIRONMENT_OPEN_REQUEST) openEnvironmentDocument(uri);
        else if (requestCode == ENVIRONMENT_CREATE_REQUEST) saveEnvironmentDocument(uri, true);
        else if (requestCode == ENVIRONMENT_EXPORT_REQUEST) saveEnvironmentDocument(uri, false);
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
        final boolean touhou = CharoiteEnvironments.isTouhou(this);
        worker.execute(() -> {
            try {
                Container current = new ContainerManager(this).getContainerById(containerId);
                if (current == null) throw new IllegalStateException("Game environment missing");
                java.util.List<JSONObject> discovered =
                        CharoiteGameDiscovery.scan(current.getRootDir(),
                                CharoiteGameProfiles.forEnvironment(
                                        CharoiteEnvironments.activeId(this)));
                if (touhou) {
                    // FocasLens install.ini may point at the real C: target
                    // even when bounded recursive discovery missed that EXE.
                    discovered.addAll(com.charoitegames.core.CharoiteShardOfDreamsSupport
                            .discoverRegisteredExpansion(current.getRootDir()));
                }
                // Discovery is read-only. Never register every EXE as a
                // shortcut: Wine tools and helper processes are not games.
                // Shortcuts are added only by explicit checked selection.
                int count = discovered.size();
                final String shardReport = touhou ?
                        com.charoitegames.core.CharoiteShardOfDreamsSupport
                            .inspectInstalledExpansion(current.getRootDir(), discovered)
                        : "";
                if (touhou)
                    CharoiteDiagnostics.recordShardInstallationScan(this, shardReport);
                final boolean shardFound = shardReport.startsWith("Shard executable found:");
                runOnUiThread(() -> {
                    // Critical: mergeInstalled persists the games, but the
                    // old UI never rebuilt its Library tiles. Do this before
                    // opening Library or reporting a successful installer.
                    CharoiteGameSessions.consumePendingInstallerScan(this);
                    scanAfterInstallerReturn = false;
                    finishOperation(count > 0
                            ? "Found " + count + " executable candidate(s). Select only your games."
                            : afterInstaller
                                ? "Installer finished. No game executable found; use Setup to scan again."
                                : "No installed game executables found.");
                    showSection(1);
                    if (count > 0) showShortcutPicker(discovered);
                });
            } catch (Exception error) {
                runOnUiThread(() -> finishOperation("Game search failed: " + error.getMessage()));
            }
        });
    }

    /**
     * Thin Portal UI adapter. All Windows file copying, executable detection,
     * cleanup and the no-autolaunch policy belong to shared Charoite Core.
     */
    private void importGame(Uri uri, CharoiteGameImport.Selection selection) {
        if (busy || containerId <= 0) return;
        busy = true;
        setStatus(selection == CharoiteGameImport.Selection.GAME_FOLDER
                ? "Importing selected game folder…" :
                selection == CharoiteGameImport.Selection.INSTALLER_FOLDER
                ? "Importing complete installer folder…" : "Importing Windows installer…");
        updateButtons();
        worker.execute(() -> {
            try {
                Container current = new ContainerManager(this).getContainerById(containerId);
                if (current == null) throw new IllegalStateException("Game environment missing");
                CharoiteGameImport.Result imported = CharoiteGameImport.importSelected(
                        this, uri, selection, current.getRootDir(),
                        CharoiteEnvironments.activeId(this),
                        CharoiteEnvironments.isTouhou(this));
                JSONObject entry = new JSONObject();
                entry.put("name", imported.installer
                        ? "Windows installer: " + imported.executableName
                        : CharoiteGameProfiles.forEnvironment(CharoiteEnvironments.activeId(this)).displayName(imported.executableName));
                entry.put("path", imported.executablePath);
                entry.put("installer", imported.installer);
                entry.put("files", imported.fileCount);
                if (imported.installer &&
                        selection != CharoiteGameImport.Selection.STANDALONE_INSTALLER) {
                    entry.put("importRoot", imported.importDirectory);
                    entry.put("installerCandidates",
                            new JSONArray(imported.installerCandidates));
                    entry.put("installerSelectionPending",
                            imported.installerCandidates.size() > 1);
                }
                // Installer metadata is retained for explicitly running
                // setup again. Imported game executables NEVER produce a
                // Library shortcut until the user confirms.
                if (imported.installer) saveEntry(entry);
                runOnUiThread(() -> {
                    if (imported.installer) {
                        boolean chooseInstaller = entry.optBoolean("installerSelectionPending", false);
                        finishOperation(CharoiteGameImport.shouldLaunchAfterImport(selection)
                                ? "Installer imported. Opening the Windows setup wizard…"
                                : chooseInstaller
                                    ? "Folder imported. Select the correct setup executable before running it."
                                    : "Installer folder imported. Open Setup and tap RUN INSTALLER when ready.");
                        showSection(1);
                        // Importing a folder NEVER launches an EXE, even
                        // when there are several plausible setup programs.
                        if (CharoiteGameImport.shouldLaunchAfterImport(selection))
                            launchGame(imported.executablePath, true);
                        else if (chooseInstaller)
                            showInstallerChooser(entry);
                    } else {
                        finishOperation("Game files imported. Choose whether to add a Library shortcut.");
                        showSection(1);
                        new androidx.appcompat.app.AlertDialog.Builder(this)
                                .setTitle("Create a Library shortcut?")
                                .setMessage("Game: " + entry.optString("name") +
                                        "\nThe imported game stays installed even if you decline. " +
                                        "You can add a shortcut later using Find Games / Add Shortcuts.")
                                .setPositiveButton("Add shortcut", (d, which) -> {
                                    try {
                                        CharoiteGameLibrary.save(this, entry);
                                        refreshLibrary();
                                        showSection(0);
                                        setStatus("Game shortcut added.");
                                    } catch (Exception e) {
                                        setStatus("Could not add shortcut: " + e.getMessage());
                                    }
                                })
                                .setNegativeButton("Not now", null)
                                .show();
                    }
                });
            } catch (Exception ex) {
                runOnUiThread(() -> finishOperation("Import failed: " + ex.getMessage()));
            }
        });
    }

    /** Show candidates without mutating the Library until Add Selected is tapped. */
    private void showShortcutPicker(java.util.List<JSONObject> discovered) {
        JSONArray library = CharoiteGameLibrary.load(this);
        java.util.Set<String> existing = new java.util.HashSet<>();
        for (int i = 0; i < library.length(); i++) {
            JSONObject saved = library.optJSONObject(i);
            if (saved != null && !saved.optBoolean("installer"))
                existing.add(saved.optString("path", ""));
        }
        java.util.ArrayList<JSONObject> available = new java.util.ArrayList<>();
        java.util.Set<String> found = new java.util.HashSet<>();
        for (JSONObject game : discovered) {
            if (game == null || game.optBoolean("installer")) continue;
            String path = game.optString("path", "");
            if (path.isEmpty() || !new File(path).isFile() ||
                    existing.contains(path) || !found.add(path)) continue;
            available.add(game);
        }
        if (available.isEmpty()) {
            new androidx.appcompat.app.AlertDialog.Builder(this)
                    .setTitle("No additional shortcuts")
                    .setMessage("All discovered games already have shortcuts, or no new executables were found. Removed shortcuts can be added here again after a scan.")
                    .setPositiveButton("OK", null).show();
            return;
        }
        available.sort((a, b) -> a.optString("name", "")
                .compareToIgnoreCase(b.optString("name", "")));
        final boolean[] selected = new boolean[available.size()];
        String[] labels = new String[available.size()];
        for (int i = 0; i < available.size(); i++) {
            JSONObject game = available.get(i);
            File exe = new File(game.optString("path", ""));
            labels[i] = game.optString("name", exe.getName()) + "\n" +
                    exe.getParentFile().getName() + "/" + exe.getName();
        }
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Add installed-game shortcuts")
                .setMultiChoiceItems(labels, selected, (dialog, which, checked) ->
                        selected[which] = checked)
                .setPositiveButton("Add selected", (dialog, which) -> {
                    java.util.ArrayList<JSONObject> chosen = new java.util.ArrayList<>();
                    for (int i = 0; i < selected.length; i++)
                        if (selected[i]) chosen.add(available.get(i));
                    if (chosen.isEmpty()) {
                        setStatus("No shortcuts added. Installed files were untouched.");
                        return;
                    }
                    try {
                        int added = CharoiteGameLibrary.mergeInstalled(this, chosen);
                        refreshLibrary();
                        if (added > 0) showSection(0);
                        setStatus(added + " Library shortcut(s) added. Installed files untouched.");
                    } catch (Exception error) {
                        setStatus("Unable to add shortcuts: " + error.getMessage());
                    }
                })
                .setNegativeButton("Not now", null)
                .show();
    }

    private void confirmClearLibraryShortcuts() {
        if (busy) return;
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Remove all Library shortcuts?")
                .setMessage("Only the shortcuts in this environment will be removed. " +
                        "All installed games, Wine files, installers and saves remain untouched. " +
                        "Find Games / Add Shortcuts can restore any shortcut without reinstalling.")
                .setNegativeButton("Keep shortcuts", null)
                .setPositiveButton("Remove shortcuts", (dialog, which) -> {
                    int count = CharoiteGameLibrary.clearGameShortcuts(this);
                    refreshLibrary();
                    setStatus(count + " shortcuts removed. No game files deleted.");
                })
                .show();
    }

    /** All library metadata persistence lives in Core. */
    private void saveEntry(JSONObject entry) {
        CharoiteGameLibrary.save(this, entry);
    }

    private JSONArray loadLibrary() {
        return CharoiteGameLibrary.load(this);
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
            TextView title = label(CharoiteEnvironments.isTouhou(this)
                    ? "Your Gensokyo library awaits"
                    : "Your " + CharoiteEnvironments.activeName(this) + " library awaits",
                    17, FOREGROUND, true);
            title.setMaxLines(2);
            title.setEllipsize(TextUtils.TruncateAt.END);
            title.setGravity(Gravity.CENTER_HORIZONTAL);
            empty.addView(title);
            TextView hint = label("Use Setup to install a Windows game in this environment.", 13, SECONDARY, false);
            hint.setGravity(Gravity.CENTER_HORIZONTAL);
            empty.addView(hint);
            libraryArea.addView(empty);
        } else {
            libraryArea.addView(label("Tap to play · Hold and drag to arrange · Manage to remove or delete", 12, SECONDARY, false));
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

                // Display the icon embedded in the installed Windows EXE.
                // The original glyph stays visible until a genuine bitmap
                // is extracted off the UI thread (or when none is available).
                FrameLayout iconHolder = new FrameLayout(this);
                GradientDrawable iconBack = new GradientDrawable(
                        GradientDrawable.Orientation.TL_BR, gameIconColors(path));
                iconBack.setCornerRadius(dp(22));
                iconHolder.setBackground(iconBack);
                TextView gameIcon = label(gameIconCharacter(path), 29, Color.WHITE, true);
                gameIcon.setGravity(Gravity.CENTER);
                iconHolder.addView(gameIcon,
                        new FrameLayout.LayoutParams(-1, -1));
                ImageView officialGameIcon = new ImageView(this);
                officialGameIcon.setScaleType(ImageView.ScaleType.FIT_CENTER);
                officialGameIcon.setVisibility(View.GONE);
                officialGameIcon.setPadding(dp(3), dp(3), dp(3), dp(3));
                officialGameIcon.setContentDescription(name + " official game icon");
                iconHolder.addView(officialGameIcon,
                        new FrameLayout.LayoutParams(-1, -1));
                tile.addView(iconHolder, new LinearLayout.LayoutParams(dp(69), dp(69)));
                if (exists) CharoiteGameIcons.bind(
                        this, path, officialGameIcon, gameIcon);

                TextView gameTitle = label(name, 12, FOREGROUND, true);
                gameTitle.setGravity(Gravity.TOP | Gravity.CENTER_HORIZONTAL);
                gameTitle.setMaxLines(2);
                gameTitle.setEllipsize(TextUtils.TruncateAt.END);
                LinearLayout.LayoutParams nameParams = new LinearLayout.LayoutParams(-1, -2);
                nameParams.topMargin = dp(9);
                tile.addView(gameTitle, nameParams);
                Button manage = outlinedButton("MANAGE", () ->
                        manageGame(name, path));
                manage.setTextSize(11);
                manage.setMinHeight(dp(34));
                manage.setMinimumHeight(dp(34));
                manage.setEnabled(!busy);
                tile.addView(manage);

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

    /** The user chooses metadata removal or confirmed deletion separately.
     * Windows installers may scatter game dependencies into shared locations;
     * never attempt to remove those automatically.
     */
    private void manageGame(String name, String executable) {
        if (busy || executable == null || executable.isEmpty()) return;
        String title = name == null || name.isEmpty() ? "Windows game" : name;
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Manage " + title)
                .setItems(new String[]{
                    "Controls: detected defaults and button mapping",
                    "Remove from Library only",
                    "Delete installation folder and remove from Library"
                }, (dialog, selected) -> {
                    if (selected == 0)
                        CharoiteGameControlProfiles.showEditor(this, executable);
                    else if (selected == 1) confirmLibraryRemoval(title, executable);
                    else confirmGameDeletion(title, executable);
                })
                .setNegativeButton("Cancel", null).show();
    }

    private void confirmLibraryRemoval(String name, String executable) {
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Remove Library shortcut?")
                .setMessage(name + " will disappear from this Library. The " +
                        "installed Windows game and save data stay on your phone. " +
                        "Use Setup → Find Games / Add Shortcuts to restore it manually.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Remove shortcut", (dialog, which) -> {
                    if (CharoiteGameLibrary.remove(this, executable)) {
                        refreshLibrary();
                        setStatus("Library shortcut removed. Game files retained.");
                    }
                }).show();
    }

    private void confirmGameDeletion(String name, String executable) {
        final java.io.File target;
        try {
            target = CharoiteGameRemoval.safeGameFolder(this, containerId, executable);
        } catch (Exception error) {
            new androidx.appcompat.app.AlertDialog.Builder(this)
                    .setTitle("Folder deletion unavailable")
                    .setMessage(error.getMessage() +
                            "\n\nYou can still remove the Library shortcut, " +
                            "or use the Windows file manager for manual inspection.")
                    .setPositiveButton("OK", null).show();
            return;
        }
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Permanently delete " + name + "?")
                .setMessage("This will permanently delete ALL files, including " +
                        "possible saves, in the following installation folder:\n\n" +
                        target.getAbsolutePath() +
                        "\n\nIt does not uninstall shared Wine components. " +
                        "There is no undo. Export any saves first.")
                .setNegativeButton("Keep game", null)
                .setPositiveButton("Delete installed game", (dialog, which) -> {
                    if (busy) return;
                    busy = true;
                    updateButtons();
                    worker.execute(() -> {
                        try {
                            CharoiteGameRemoval.deleteGameFolder(
                                    this, containerId, executable);
                            runOnUiThread(() -> {
                                CharoiteGameLibrary.remove(this, executable);
                                busy = false;
                                refreshLibrary();
                                updateButtons();
                                setStatus("Installed game folder deleted: " + name);
                            });
                        } catch (Exception failure) {
                            runOnUiThread(() -> {
                                busy = false;
                                refreshLibrary();
                                updateButtons();
                                new androidx.appcompat.app.AlertDialog.Builder(this)
                                        .setTitle("Could not delete game")
                                        .setMessage(failure.getMessage())
                                        .setPositiveButton("OK", null).show();
                            });
                        }
                    });
                }).show();
    }

    private String gameIconCharacter(String path) {
        String exe = new File(path).getName().toLowerCase(Locale.ROOT);
        if (exe.equals("gn_enbu.exe")) return "東";
        if (com.charoitegames.core.CharoiteShardOfDreamsSupport.isExpansionGame(exe))
            return "夢";
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

    /** UI-only tile drag handler; the reorder contract lives in Core. */
    private void reorderGame(String sourcePath, String targetPath) {
        if (busy || sourcePath.equals(targetPath)) return;
        if (CharoiteGameLibrary.reorder(this, sourcePath, targetPath)) {
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
        boolean selectionPending = lastInstaller.optBoolean("installerSelectionPending", false);
        JSONArray installerCandidates = lastInstaller.optJSONArray("installerCandidates");
        LinearLayout installerCard = card();
        installerCard.addView(label("CURRENT INSTALLER", 12, GOLD, true));
        installerCard.addView(label(new File(path).getName(), 16, FOREGROUND, true));
        if (installerCandidates != null && installerCandidates.length() > 1) {
            String importRoot = lastInstaller.optString("importRoot", "");
            if (!importRoot.isEmpty()) {
                String relative = new File(importRoot).toURI().relativize(
                        new File(path).toURI()).getPath();
                installerCard.addView(label("Selected file: " + relative,
                        12, SECONDARY, false));
            }
            installerCard.addView(label(selectionPending
                    ? "Multiple setup executables found. Choose the correct installer before running."
                    : "Installer selected. You can change it without re-importing the folder.",
                    12, SECONDARY, false));
            final JSONObject selectedEntry = lastInstaller;
            Button choose = outlinedButton(selectionPending ?
                    "CHOOSE INSTALLER" : "CHANGE INSTALLER",
                    () -> showInstallerChooser(selectedEntry));
            choose.setEnabled(!busy && containerId > 0);
            installerCard.addView(choose);
        }
        int mediaFiles = lastInstaller.optInt("files", 0);
        installerCard.addView(label("Imported installer files: " + mediaFiles +
                (mediaFiles == 1
                    ? ". If the original installer also requires .bin/.cab archives " +
                      "or supporting folders, import the complete setup folder instead."
                    : ". Keep the original media files together while running setup."),
                12, SECONDARY, false));
        installerCard.addView(label("The imported installer is saved here. Run it when you choose; imported files are preserved.", 12, SECONDARY, false));
        Button rerun = outlinedButton("RUN INSTALLER", () -> launchGame(path, true));
        rerun.setEnabled(!busy && containerId > 0 &&
                !selectionPending && new File(path).isFile());
        installerCard.addView(rerun);
        setupArea.addView(installerCard);
        spacerIn(setupArea, 12);
    }


    /** Explicitly select which setup EXE to use from a copied installer folder.
     * Identically named setup files in separate subfolders are shown with
     * their relative paths. Cancel leaves the folder intact and RUN disabled.
     */
    private void showInstallerChooser(JSONObject entry) {
        if (busy || entry == null) return;
        JSONArray candidates = entry.optJSONArray("installerCandidates");
        if (candidates == null || candidates.length() < 2) return;
        String rootPath = entry.optString("importRoot", "");
        if (rootPath.isEmpty()) {
            setStatus("Imported setup folder location is missing.");
            return;
        }
        String[] labels = new String[candidates.length()];
        try {
            String root = new File(rootPath).getCanonicalPath() + File.separator;
            for (int i = 0; i < candidates.length(); i++) {
                String path = candidates.optString(i, "");
                File executable = new File(path);
                String canonical = executable.getCanonicalPath();
                if (!canonical.startsWith(root) || !executable.isFile() ||
                        java.nio.file.Files.isSymbolicLink(executable.toPath()) ||
                        !CharoiteGameImport.isLikelyInstaller(executable.getName())) {
                    throw new java.io.IOException("Installer file is missing or outside the imported folder");
                }
                labels[i] = canonical.substring(root.length());
            }
        } catch (Exception error) {
            setStatus("Unable to list setup programs: " + error.getMessage());
            return;
        }
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Which installer should Charoite run?")
                // List dialogs must not setMessage(): Android otherwise
                // displays the text panel instead of its selectable list.
                .setItems(labels, (dialog, which) -> {
                    try {
                        String selected = candidates.getString(which);
                        entry.put("path", selected);
                        entry.put("name", "Windows installer: " +
                                new File(selected).getName());
                        entry.put("installerSelectionPending", false);
                        saveEntry(entry);
                        refreshLibrary();
                        setStatus("Installer selected: " + labels[which] +
                                ". Tap RUN INSTALLER when ready.");
                        showSection(1);
                    } catch (Exception error) {
                        setStatus("Cannot select installer: " + error.getMessage());
                    }
                })
                .setNegativeButton("Not now", null)
                .show();
    }

    /**
     * Launch the selected original Windows installer without adding /DIR or
     * any destination override. The Windows installer chooses its own path.
     */
    private void launchGame(String path, boolean installer) {
        if (busy || containerId <= 0) return;
        try {
            CharoiteGameSessions.launch(this, XServerDisplayActivity.class,
                    containerId, path, installer);
        } catch (Exception error) {
            setStatus("Unable to launch Windows program: " + error.getMessage());
        }
    }

    /** Opt-in, reusable Charoite Core GDI baseline. Never imports or scans games. */
    private void runWindowsTextRenderingTest() {
        if (busy || containerId <= 0) {
            setStatus("Prepare your Windows environment before starting a rendering test.");
            return;
        }
        try {
            String executable = CharoiteRenderingDiagnostics.prepare(this, containerId);
            CharoiteGameSessions.launch(this, XServerDisplayActivity.class,
                    containerId, executable, false, false);
        } catch (Exception error) {
            setStatus("Windows text-rendering test could not start: " + error.getMessage());
        }
    }

    /** Compare owner-drawn listbox GDI APIs without altering Wine or games. */
    private void runOwnerDrawTextRenderingTest() {
        if (busy || containerId <= 0) {
            setStatus("Prepare your Windows environment before starting a rendering test.");
            return;
        }
        try {
            String executable = CharoiteRenderingDiagnostics.prepareOwnerDraw(this, containerId);
            CharoiteGameSessions.launch(this, XServerDisplayActivity.class,
                    containerId, executable, false, false);
        } catch (Exception error) {
            setStatus("Owner-draw rendering test could not start: " + error.getMessage());
        }
    }

    private void finishOperation(String message) {
        busy = false;
        setStatus(message);
        refreshReadyState();
        // Preserve the meaningful operation result instead of overwriting with generic ready text.
        setStatus(message);
        if (runtimeLabel != null && (message.contains("failed") || message.contains("Could not")))
            runtimeLabel.setText(message + " You can retry here.");
        if (scanAfterInstallerReturn && containerId > 0 &&
                CharoiteGameSessions.hasPendingInstallerScan(this)) {
            scanAfterInstallerReturn = false;
            showSection(1);
            findInstalledGames(true);
        }
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
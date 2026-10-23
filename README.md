# Charoite Portal for Android

**Charoite Portal** is a Charoite Games Windows gaming environment manager running entirely inside Android / Samsung One UI, with **Charoite Core v0.6** and a pinned, appropriately attributed Winlator-derived Wine/Box64 runtime. It is **not** a custom Android OS, a Windows installation, or a proprietary Wine/Box64 replacement.

The application was previously **Touhou Launcher for Android**. Android package ID remains **`com.touhoudr`** intentionally, to protect access to existing Touhou game files and saves on upgrade. Do not uninstall an older installation just to rename the app.

## Features in this version

- **Environments — System tab:** Switch realms; select a downloaded **`.cenv`** profile with Android Files to install an environment; create a named realm and save its portable `.cenv` profile in a phone folder of your choice; or export an existing realm as `.cenv`. Installing or creating a realm provisions an independent Wine container through the bundled Charoite Core runtime, never a full Windows OS installation.
- **Touhou Realm:** Migrates the existing Touhou installation *in place*. Keeps its previous Wine container, `game_library` settings, imported `C:\TouhouPocket\` games, saved tile order, Japanese font installer compatibility hooks, and any existing custom wallpaper. It uses an original built-in sakura-themed wallpaper and Touhou-specific executable discovery.
- **General Gaming:** A second built-in template with an original purple/cosmic background, independent Wine container, and generic Windows executable discovery. Japanese guest locale/font hooks are scoped to Touhou Realm rather than applied globally.
- **Custom environments:** User-provided names, separate library preferences, separate `C:\CharoitePortal\` staging folders within each independent Wine container, separate graphics/display/DeX pointer preferences and wallpaper overrides.
- **Library, Setup, System:** Core-owned, connected page-tab UI plus swipe-left/right switching within the scrollable content, touch/DeX compatible. Library shows one environment at a time. Setup imports a complete Windows game or installer folder, or standalone installer; a Windows installer chooses its own installation destination. System provides Windows compatibility settings, diagnostics and launcher wallpaper selection.
- **Themes & wallpaper:** Environment-specific default artwork, plus independent phone-image wallpaper overrides with Fit / Crop to Fill and Remove. Selecting a wallpaper never alters Android/One UI or the source image. The new official Charoite Portal app icon is a purple crystal/cosmic gateway with no Touhou branding.
- **Branding:** The Android launcher, localized app labels, game notifications, foreground service, about dialog and return-to-home navigation all use Charoite Portal / Charoite Core—not Winlator-branded UI. The original upstream code and license attribution still reside privately in the APK's legal notices, as required.
- **Auto-rotate:** Charoite Portal, Windows installer windows and game windows accept device sensor rotations in portrait/landscape (including when rotating mid-session). The live XServer renderer fits the existing Wine image to the new Android surface without restarting games. New Wine sessions choose portrait-shaped or landscape-shaped virtual desktop dimensions using the phone's current orientation, including the selected compatibility resolution. **The internal Windows desktop resolution in an already-running game is not changed live** because this engine fixes the X11 root-screen size at startup; some fixed-resolution Windows games may letterbox when rotated.
- **Wine/Box64:** Reuses pinned upstream open-source runtime, graphics compatibility modes, Japanese text support where applicable, and per-launch DeX virtual resolution. New upstream Wine versions are **not** downloaded automatically; the included engine prepares/refreshed on APK install or update.

## Importing a game folder

**Setup → Import Game Folder → Use this folder** copies the selected folder into the active environment and registers the preferred playable Windows executable in **Library**, but never launches an EXE on import. When the folder contains an installer but no playable game, it appears in **Setup** with a **RUN INSTALLER** button; the wizard opens only when you press that button. A folder containing both setup.exe and a playable game executable prioritizes the game. The separate **SELECT INSTALLER .EXE** action is intentionally explicit and still opens the selected standalone installer wizard.

## Environment limitations and safety

**Portable `.cenv` files** hold only profile name, theme and graphics/display/pointer settings (not games, saves, credentials or Wine prefixes), use strict versioned JSON and are capped at 16 KiB. The user must choose a local file to install; nothing is automatically downloaded or installed. A sample [General Gaming profile](environment-profiles/General-Gaming.cenv) is available to download. **Create Environment** saves its `.cenv` file through Android Save As before registering the new local realm. **Export Environment** saves an existing profile the same way. Wine compatibility varies by title; auto-detection of optimal Wine/graphics settings remains future work.

The migration preserves game data paths but **real-device validation is still required** for UI behavior, per-title games, and Samsung DeX. Debug-signed CI APKs may have different signing certificates, preventing in-place updates; do not uninstall if your Wine prefix contains important saves. Future releases require a persistent release-signing key and appropriately incremented version codes.

## Development

Existing GitHub repository: `rgarn023/TouhouPocketLauncher` (historical name; avoid renaming it automatically). Development continues on `main`. The combined APK is built through the [Windows runtime workflow](https://github.com/rgarn023/TouhouPocketLauncher/actions/workflows/runtime-preview.yml). Select the newest **successful** run and extract `app-debug.apk` from `touhou-pocket-runtime-preview-apk`.

Source structure:
- `runtime-preview/TouhouEntryActivity.java`: Main Charoite Portal native Android shell, with Touhou game import logic retained in its environment.
- `runtime-preview/charoite-core/CharoiteEnvironments.java`: Registry and non-destructive Touhou migration.
- `runtime-preview/charoite-core/CharoiteEnvironmentFiles.java`: Validated portable `.cenv` profile format.
- `runtime-preview/charoite-core/CharoiteSwipePager.java`: Cross-page horizontal swipe gesture support.
- `runtime-preview/charoite-core/CharoiteCore.java`: Wine engine preparation, default container profiles, graphics and DeX policy.
- `runtime-preview/charoite-core/CharoiteWallpaper.java`: Per-environment image storage and Fit/Crop preferences.
- `runtime-preview/charoite-core/CharoiteThemes.java`: Original built-in Touhou sakura / general cosmic wallpaper artwork.
- `runtime-preview/charoite-core/CharoitePageTabs.java`: Shared connected page tab UI.
- `runtime-preview/overlay.py`: Packages the app and Core into the pinned upstream Android source, retains original `com.touhoudr` identity and license notices.

No proprietary Touhou or Windows game executables, translations or expansions are bundled. Respect all applicable Wine/Winlator/Box64/graphics/font licenses. See [runtime attribution](runtime-preview/NOTICE.md), [Core documentation](runtime-preview/charoite-core/README.md), and [development handoff](docs/HANDOFF.md).

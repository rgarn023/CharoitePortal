# Charoite Portal for Android

**Charoite Portal** is a Charoite Games Windows gaming environment manager running entirely inside Android / Samsung One UI, with **Charoite Core v0.3** and a pinned, appropriately attributed Winlator-derived Wine/Box64 runtime. It is **not** a custom Android OS, a Windows installation, or a proprietary Wine/Box64 replacement.

The application was previously **Touhou Launcher for Android**. Android package ID remains **`com.touhoudr`** intentionally, to protect access to existing Touhou game files and saves on upgrade. Do not uninstall an older installation just to rename the app.

## Features in this version

- **Environments — System tab:** Switch installed environments; install the built-in offline **General Gaming** environment; create up to 20 named custom Windows gaming environments. Environment creation provisions a separate Wine container asynchronously using the bundled Charoite Core runtime. These are isolated Windows *compatibility environments*, not complete Windows OS installations.
- **Touhou Realm:** Migrates the existing Touhou installation *in place*. Keeps its previous Wine container, `game_library` settings, imported `C:\TouhouPocket\` games, saved tile order, Japanese font installer compatibility hooks, and any existing custom wallpaper. It uses an original built-in sakura-themed wallpaper and Touhou-specific executable discovery.
- **General Gaming:** A second built-in template with an original purple/cosmic background, independent Wine container, and generic Windows executable discovery. Japanese guest locale/font hooks are scoped to Touhou Realm rather than applied globally.
- **Custom environments:** User-provided names, separate library preferences, separate `C:\CharoitePortal\` staging folders within each independent Wine container, separate graphics/display/DeX pointer preferences and wallpaper overrides.
- **Library, Setup, System:** Core-owned, connected page-tab UI, touch/DeX compatible. Library shows one environment at a time. Setup imports a complete Windows game or installer folder, or standalone installer; a Windows installer chooses its own installation destination. System provides Windows compatibility settings, diagnostics and launcher wallpaper selection.
- **Themes & wallpaper:** Environment-specific default artwork, plus independent phone-image wallpaper overrides with Fit / Crop to Fill and Remove. Selecting a wallpaper never alters Android/One UI or the source image. The new official Charoite Portal app icon is a purple crystal/cosmic gateway with no Touhou branding.
- **Wine/Box64:** Reuses pinned upstream open-source runtime, graphics compatibility modes, Japanese text support where applicable, and per-launch DeX virtual resolution. New upstream Wine versions are **not** downloaded automatically; the included engine prepares/refreshed on APK install or update.

## Environment limitations and safety

The **Install Environment** command currently offers **offline built-in templates only**. It does not download unreviewed executable packages or import arbitrary archives. **Create Environment** builds a new isolated Wine container using the bundled engine; Wine compatibility varies from title to title. Automatic detection of the best Wine/graphics profile for every Windows game is a future feature.

The migration preserves game data paths but **real-device validation is still required** for UI behavior, per-title games, and Samsung DeX. Debug-signed CI APKs may have different signing certificates, preventing in-place updates; do not uninstall if your Wine prefix contains important saves. Future releases require a persistent release-signing key and appropriately incremented version codes.

## Development

Existing GitHub repository: `rgarn023/TouhouPocketLauncher` (historical name; avoid renaming it automatically). Development continues on `main`. The combined APK is built through the [Windows runtime workflow](https://github.com/rgarn023/TouhouPocketLauncher/actions/workflows/runtime-preview.yml). Select the newest **successful** run and extract `app-debug.apk` from `touhou-pocket-runtime-preview-apk`.

Source structure:
- `runtime-preview/TouhouEntryActivity.java`: Main Charoite Portal native Android shell, with Touhou game import logic retained in its environment.
- `runtime-preview/charoite-core/CharoiteEnvironments.java`: Registry and non-destructive Touhou migration.
- `runtime-preview/charoite-core/CharoiteCore.java`: Wine engine preparation, default container profiles, graphics and DeX policy.
- `runtime-preview/charoite-core/CharoiteWallpaper.java`: Per-environment image storage and Fit/Crop preferences.
- `runtime-preview/charoite-core/CharoiteThemes.java`: Original built-in Touhou sakura / general cosmic wallpaper artwork.
- `runtime-preview/charoite-core/CharoitePageTabs.java`: Shared connected page tab UI.
- `runtime-preview/overlay.py`: Packages the app and Core into the pinned upstream Android source, retains original `com.touhoudr` identity and license notices.

No proprietary Touhou or Windows game executables, translations or expansions are bundled. Respect all applicable Wine/Winlator/Box64/graphics/font licenses. See [runtime attribution](runtime-preview/NOTICE.md), [Core documentation](runtime-preview/charoite-core/README.md), and [development handoff](docs/HANDOFF.md).

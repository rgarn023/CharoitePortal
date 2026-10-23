# Touhou Launcher for Android

**Touhou Launcher for Android** is an experimental Charoite Games application for installing, organizing, and launching user-owned Windows Touhou games on Android, including Samsung Galaxy devices and Samsung DeX. The launcher includes **Charoite Core v0.1**, a reusable runtime-coordination module built alongside the launcher. Neither product replaces Android or Samsung One UI.

Primary game targets: **Touhou Puppet Dance Performance**, **Shard of Dreams**, and **Extended**, followed by other Touhou titles. Standalone English patches may be added later; **thcrap is not a supported integration**.

## Architecture

- **Touhou Launcher:** Native Android, One UI-inspired library/setup/system UI, reorderable game tiles, imports, executable discovery, direct game launching, setup wizard support and diagnostics.
- **Charoite Core:** `runtime-preview/charoite-core/CharoiteCore.java` currently owns the bundled Wine/Box64 preparation policy, compatibility graphics/default container profiles, and phone/DeX display and pointer settings. It is compiled into this APK through `runtime-preview/overlay.py`. Read its [architecture and preservation contract](runtime-preview/charoite-core/README.md).
- **Compatibility backend:** Attributed, pinned LGPL Winlator-derived Android runtime, bundled Wine and Box64, upstream graphics/input systems, and Touhou-targeted Japanese locale and Windows font compatibility helpers.
- **Android:** All components run inside a normal Android application sandbox. App ID **`com.touhoudr`** is deliberately unchanged; no root or standalone OS is required. No Windows games are packaged.

**Charoite Core is not yet a separate downloadable SDK, AAR, installed app, game engine download service, Wine fork or Proton implementation.** It is source code actively used by the launcher and intended for gradual reuse by other Charoite Games projects.

## Current Android features

- **Library:** Shows playable Windows games, not installer executables. Tap to launch; touch and hold to rearrange game tiles. Tile positions persist locally. Setup instructions are in the Setup tab.
- **Setup:** Import a complete game or installer folder, or a standalone Windows installer. The original Windows wizard runs in Wine. Return to Setup to scan installed games in the private Wine C: drive.
- **System:** Retry game-engine preparation if required, compatibility graphics, diagnostic log, and **External display & DeX** resolution and mouse-capture settings.
- **Automatic runtime preparation:** On the first launch after installing or updating the APK, the bundled root filesystem is prepared or refreshed. This does **not** download newer upstream Wine versions automatically and must not erase the existing private Wine prefixes.
- **DeX:** The launcher and game window are declared resizable; the launcher is centered on larger windows. Windows virtual display size can be chosen automatically or set to 1280x720, 1600x900, 1920x1080, or compatibility 800x600. Mouse and keyboard use the Winlator-derived event handling. Display changes apply at the next game launch rather than live-changing the guest X server resolution.
- **Japanese installers:** A pinned, licensed Japanese font/locale pack and thread-scoped Win32 font helper address legacy CP932 Japanese text. Installer destinations are not overridden.

The interface, drag-and-drop, DeX behavior, game rendering, and completeness of individual Touhou game compatibility still need physical Galaxy verification. Do not assume all expansions or installers work until tested.

## Building / APK

[Android GitHub Actions workflow](https://github.com/rgarn023/TouhouPocketLauncher/actions/workflows/runtime-preview.yml) builds the combined launcher plus Charoite Core from the pinned upstream source. Choose the latest **successful** run, download `touhou-pocket-runtime-preview-apk` and extract `app-debug.apk`.

**Signing warning:** This currently uses CI debug signing, which may change between builds and prevent updating an already-installed APK in place. Uninstalling the app deletes its private Windows game files and saves; do not uninstall without a backup. The long-term release pipeline needs a persistent, securely managed signing key and increasing version codes.

## Compatibility and legal notes

No proprietary Touhou games, translations, expansions, or unauthorized copyrighted game files are bundled. Winlator and other third-party open-source components retain their notices and applicable source license obligations. See [runtime attribution](runtime-preview/NOTICE.md) and [development handoff](docs/HANDOFF.md). The launcher currently builds on the existing branch and keeps its existing private storage mappings, including `C:\TouhouPocket\`, regardless of the visible rebranding.

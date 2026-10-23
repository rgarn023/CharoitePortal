# Charoite Core migration audit — October 23, 2026

Repository: `rgarn023/TouhouPocketLauncher`, existing branch `main`.
Core version: **0.9**.
Android package identifier: **`com.touhoudr`** (unchanged; never uninstall a version with unbacked-up Wine prefixes/saves).

## Implemented in reusable Charoite Core

| Capability | Core module | Migration |
|---|---|---|
| Windows Wine/Box64 engine provisioning, version checks, graphics mode, launch resolution, rotation-aware sizing, DeX pointer configuration | `CharoiteCore.java` | Core-owned |
| Per-environment identity, active environment registry, independent container IDs, preserved legacy Touhou paths and library keys | `CharoiteEnvironments.java` | Core-owned |
| Portable versioned `.cenv` profile validation and serialization | `CharoiteEnvironmentFiles.java` | Core-owned |
| File/folder SAF copies, storage limits, EXE discovery/selection and **folder import never auto-executes** | `CharoiteGameImport.java` | Core-owned |
| Library persistence, metadata deduplication, single installer slot, merging installed games, tile order | `CharoiteGameLibrary.java` | **Moved from Portal** |
| Read-only bounded Windows C: scan, symlink avoidance and candidate detection | `CharoiteGameDiscovery.java` | **Moved from Portal** |
| Touhou / generic game file acceptance and display-name policies | `CharoiteGameProfiles.java` | **Moved from Portal**; profile-driven |
| Explicit Wine/XServer session launching, per-launch options, installer-completion scan flag | `CharoiteGameSessions.java` | **Moved from Portal** |
| Launch state, native process errors, diagnostic history and Japanese probe log reading | `CharoiteDiagnostics.java` | **Moved from old TouhouDiagnostics**; old duplicate deleted |
| Licensed Japanese Noto/IPA font installation, CP932/Shift-JIS locale and per-prefix font registration | `CharoiteJapaneseSupport.java`, `charoite-core/japanese/` | Core-owned |
| Optional, bounded Inno Setup font-repair helper | `charoite-core/japanese/`, `CharoiteCore.installerFontRepairEnabled` | Generalized to per-environment opt-in; Touhou legacy defaults ON; not silently applied to unrelated games |
| Wallpaper image import/storage/display modes | `CharoiteWallpaper.java` | Core-owned |
| Sakura/cosmic realm banners/backgrounds | `CharoiteThemes.java` | Core-owned |
| Page tabs and horizontal swipe behavior | `CharoitePageTabs.java`, `CharoiteSwipePager.java` | Core-owned widgets |

## Portal UI responsibilities (deliberately remain)

`runtime-preview/TouhouEntryActivity.java` renders Charoite Portal's screen layout, header/banner, Library/Setup/System pages, game tiles, Android file and `.cenv` pickers, dialogs/notifications, game launch buttons, wallpaper previews and diagnostics display. It delegates game imports, library data, discovery, launch policy and diagnostics to Core. The historical Java class name remains to preserve runtime compatibility; it is the common Portal for **all** realms, not an independent Touhou app.

Portal still coordinates **Android lifecycle and async UI** (including new container creation through the upstream `ContainerManager`); it uses Core profiles, IDs, preferences and engine preparation. UI wiring itself has not been converted into a standalone reusable Core service, by design.

## Environments (data/profiles, not separate engines)

- Touhou Realm: original private Wine prefix and `C:\TouhouPocket` staging path, `game_library` preference key, Touhou-specific game discovery policy, sakura identity, Japanese text default ON, installer font repair default ON.
- General/custom realms: independent Wine container IDs, separate library keys, `C:\CharoitePortal` staging path inside each prefix, generic EXE discovery, cosmic/sakura theme, Japanese support/installer repair opt-in.
- A `.cenv` file stores only name/theme/display/graphics/pointer/Japanese settings. It is **not** a backup of executables, containers, user files or saves. Importing a downloaded `.cenv` does not run code.

## Underlying Windows runtime

`runtime-preview/overlay.py` integrates the pinned Winlator-derived Wine/Box64/XServer backend. Source-license and attribution notices remain. This underlying third-party engine is **not** replaced by a from-scratch Core implementation; Charoite Core provides reusable management and compatibility services around it.

## Current limits / remaining work

1. **Actual game-save backup/restore:** no dedicated save manager or fully portable Wine-prefix backup has been implemented. Existing game saves are preserved in their local Wine containers, not exported to `.cenv`.
2. **Live Windows-native resolution switching:** Android display reflows on rotation, but active Windows X11 desktop mode is chosen at session launch. Some fixed-resolution Windows games may letterbox on rotation.
3. **Japanese text corruption:** fonts and CP932 plus optional Inno font repair are available; if an installer's Unicode strings were already incorrectly decoded, changing font alone won't reverse mojibake. On-device diagnostic probes are the way to isolate those cases.
4. **Testing:** GitHub Actions compiles the APK and checks source/asset contracts. Device-level tests on Samsung Galaxy S26 Ultra/DeX, including file pickers, swipe gestures, Japanese checklists and post-install scans, remain necessary.
5. **Independent Core library distribution:** Core is currently an **in-app source module** packaged into Charoite Portal. It has not been extracted into an independently versioned Maven/Gradle Android AAR or separate SDK.

Every migration listed above was based on verified `main` source files; a GitHub Actions green build confirms compilation but not physical device behavior.

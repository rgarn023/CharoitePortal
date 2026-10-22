# Touhou Pocket Launcher — ChatGPT development handoff

Updated: 2026-10-22. **Check latest main commit and GitHub Actions status before stating an APK is ready.**

## Critical development workflow
- **ChatGPT develops directly in connected GitHub.** Do not recommend Cursor or another coding agent. Discover `mcp__GitHub__` via `functions.exec` / `ALL_TOOLS` if needed.
- Repo: https://github.com/rgarn023/TouhouPocketLauncher; branch: **main**; repository public and confirmed writable.
- User requests that ChatGPT proactively prepare handoffs when chat becomes lengthy. This markdown is the durable handoff.
- User's Galaxy S26 Ultra is the test device.
- Do not ask user to upload repo files already accessible on GitHub; device testing still requires user to run the APK and report results.

## Product requirements
- One **standalone Android APK with a Touhou-first native interface**, NOT the Winlator app interface. Wine/Box64 stays completely underneath. The game renderer may still use native Winlator-derived controls, but no container manager / Winlator menus as the main UI.
- Touhou Puppet Dance Performance (TPDP), Shard of Dreams (SoD), Extended first. Later other Touhou Windows games.
- Import legally owned Windows game EXEs/installed folders; English patches installed independently with backups and rollback, **no thcrap**.
- Automatically handle unusual installation paths, Japanese filenames, and `notkey` workaround for SoD if needed.
- Touch/gamepad support, responsive Samsung screen layouts, saved game protection, proper graphics/audio, efficient native frame pacing.
- Respect Wine/Box64/Winlator and other third-party licenses. No copyrighted games/patches bundled.

## Source/build architecture
There are **two build variants**, presently installed as different Android packages:
1. Old **Kotlin file-import-only alpha**, `app/`, workflow `.github/workflows/android-debug.yml`. Build passed; cannot run EXEs; retain as reference.
2. **Integrated Wine runtime / Touhou launcher** `runtime-preview/`, workflow `.github/workflows/runtime-preview.yml`. Builds pinned upstream `brunodev85/winlator-app` at commit `8077f374ef2d54127b088de9e8cd7b4af14d9c8b`. Reproducible overlay patches app label, application ID `games.charoite.touhoupocket.runtime`, provider authority, theme, splash/activity, and documentfile dependency; bundles LGPL notice. Source and licensing in `runtime-preview/NOTICE.md`.

## Latest implementation (important: user specifically rejected Winlator interface)
Original runtime preview launched native `TouhouEntryActivity` but pressing its button entered the **Winlator container-manager UI**. User explicitly said they do not want that.
New `runtime-preview/TouhouEntryActivity.java` **removes Winlator UI navigation**:
- Touhou Pocket game library with native Android interface.
- `Set Up Game Engine` runs private `rootfs.tzst` extraction and creates a `Touhou Games` container automatically with Winlator's own `ContainerManager`.
- `Import Game Folder` uses Android SAF, copies complete owned game into the private C drive with path/size/file-count limits, detects `gn_enbu.exe`, `enbu_ap.exe` and numbered Touhou EXEs.
- `Import Windows Game Installer (.EXE)` imports selected installer to a private folder; `Run Installer` launches its EXE.
- `Find Installed Touhou Games` scans the Windows C drive for known EXEs, so after installer completes the user can play without browsing Wine UI.
- `Play` starts `XServerDisplayActivity` directly with `container_id` and `exec_path`, bypassing Winlator MainActivity.
- Native theme changed to `@style/AppThemeDark` because Touhou entry now inherits AppCompatActivity.
- Winlator's `MainActivity` launcher intent filter is removed and it is non-exported; the backend remains bundled for rendering and controls.

**CI:** New code was committed with SHA `61636c4270cd1bbc04975106f66e3e87a1141010`. Runtime workflow PASSED on 2026-10-22: run `39791004531` at commit `dc3a6e6d...`, including the Touhou library UI, direct Wine EXE launch, game folder import, and installed-game scan. Artifact `touhou-pocket-runtime-preview-apk` (ID `12430358682`) contains `app-debug.apk` (157,571,711 bytes). APK ZIP integrity verified. On-device behavior remains **UNTESTED**. Workflow: https://github.com/rgarn023/TouhouPocketLauncher/actions/workflows/runtime-preview.yml .

## What remains unverified
- On-device Android installation, first engine extraction, container creation, game imports, real Windows EXE startup, graphics/audio/input on Galaxy S26 Ultra. **A successful GitHub build only proves compilation.**
- Standalone English patches, Shard of Dreams Extended DLL override, and `notkey` adaptation for integrated runtime **not implemented**.
- UI is Touhou-specific, but the XServer in-game display still inherits some Winlator controls; replacing these while retaining debugging/accessibility should be a future step.
- Game folder copied into private app data; uninstalling app can delete files/saves. Must add backup/export.

## SoD `notkey` workaround
- Documented Wine 9.21-era fix for Japanese path install bug may require symlink named `notkey` **inside SoD installation directory**, pointing at base TPDP folder.
- `app/src/main/java/games/charoite/touhoupocket/NotkeyLinkManager.kt` tested in original Kotlin alpha but not yet moved into integrated Java runtime. Only use it if actual Wine version requires. Reference: https://bugs.winehq.org/show_bug.cgi?id=54295

## Immediate next steps
1. Download the successful artifact `touhou-pocket-runtime-preview-apk` from GitHub Actions run `39791004531` containing `app-debug.apk`.
2. Have user test **Touhou Pocket** screen > **Set Up Game Engine** > **Import Game Folder** > **Play** with TPDP base game, or EXE installer > **Find Installed Touhou Games**. Troubleshoot with exact failures.
3. Make engine setup/import robust, profile TPDP base and SoD, Japanese locale/graphics. Keep Winlator container UI hidden.
4. After base game works, implement independent English patch management and SoD `notkey` compatibility, then Extended and touch controls.
5. Handoff to a new conversation only when context reaches limits; use this file and current main.

Documentation: `README.md` and `docs/RUNTIME-TEST.md` updated for direct Touhou UI.

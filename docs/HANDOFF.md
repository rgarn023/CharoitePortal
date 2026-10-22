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


## October 22 follow-up: user reports nothing launches, indefinite 'Starting up'
- User directly tested the Touhou UI build and reports game installers and Play hang on 'Starting up'. They are unhappy the APK uses Winlator's Windows environment. **Do not claim playable or compatible.**
- Windows x86 EXEs inherently require Wine/Box64 (or another Windows emulation/compatibility system); separate Winlator interface is avoidable. Our APK currently derives much of Winlator's runtime and XServerDisplayActivity; user wants it hidden behind Touhou game UI.
- Changes committed on main: `runtime-preview/TouhouDiagnostics.java` gathers bounded local process output; `runtime-preview/overlay.py` instruments upstream XServerDisplayActivity with 45-second launch watchdog, native error dialog, local diagnostics recording, and returns to TouhouEntryActivity rather than Winlator on game exit; also records ProcessHelper spawn errors.
- `runtime-preview/TouhouEntryActivity.java` now has a launch-diagnostics viewer with copy action, compatibility graphics toggle (Vortek/VirGL, WineD3D, conservative Box64, 800x600), stable normal preset, upstream first-run Box64 settings initialization, and fixed non-ASCII game path handling. Supports multi-file Windows game installers selected via Import Game Folder; single-file EXE imports only for self-contained installers.
- Latest code commit for this set: `3a3f0f6749beaf85258705b6df39750f98ed5dc2`. Workflow `39793531948` was **queued** at the time of this documentation. Inspect current Actions status and fix compilation issues before giving APK links: https://github.com/rgarn023/TouhouPocketLauncher/actions/workflows/runtime-preview.yml .
- The exact cause on Galaxy S26 Ultra remains unknown until its Windows runtime logs are supplied. Prefer real diagnostics over speculation. RootFS initialization and graphics are plausible failure areas, but not proven root cause.
- IMPORTANT: Existing imported games/saves inside app private data may be deleted on uninstall. APK debug signatures can change across CI builds; do not casually tell user to uninstall unless files/saves are backed up.
- Next: obtain successful APK, user install/update (protect app data), tap Play; if 45-second error, return to Library > View Last Launch Diagnostics > Copy report and share. Try compatibility graphics if needed. After identifying root cause, fix engine and verify TPDP base before patch/expansion work.


## Box64 execution blocker identified and packaging repair — October 22, 2026
Actual Galaxy report: setup.exe launch never reached Wine. ProcessBuilder could not execute files/rootfs/usr/local/bin/box64 (EACCES / error 13).
Inspected compiled Box64 from the APK with readelf and strings: its ELF interpreter is hardcoded to /data/data/com.winlator/files/rootfs/lib/ld-linux-aarch64.so.1, but original Touhou package was games.charoite.touhoupocket.runtime. This targets another app's private loader path and can produce EACCES. Several rootfs / graphics .tzst archives and JNI .so binaries also embed /data/data/com.winlator.
Fix now on main: runtime-preview/rewrite_prefix.py unpacks and rewrites all pinned .tzst assets com.winlator -> com.touhoupk (identical 12-byte length preserving ELF offsets). overlay.py changes Android applicationId to com.touhoupk, modifies provider authority, and rewrites only absolute /data/data/com.winlator strings in C++ sources before compiling native libraries (not JNI class names).
CI .github/workflows/runtime-preview.yml verifies Box64 ELF loader path matches new package and no native .so has stale Winlator private data path. Runtime launch checks Box64 execute permission and the glibc loader and records preflight diagnostics.
Launcher label is Touhou Pocket Test to distinguish from prior package. IMPORTANT: Changing Android package ID means NEW APP SIDE BY SIDE, not an update. Old private game files and saves remain in previous app; do not instruct user to uninstall or clear the old app. Reimport legally owned originals to new test build.
New package com.touhoupk is a short *test* ID; user requested standalone Touhou app without Winlator interface. Backend Wine/Box64 remains. New APK not proven playable until user confirms on-device.
Actions status may be queued/in progress. Check https://github.com/rgarn023/TouhouPocketLauncher/actions/workflows/runtime-preview.yml and only distribute an APK after latest successful native rebuild. If new Android execution still fails, collect View Last Launch Diagnostics and inspect execute/loader flags and Android policy.

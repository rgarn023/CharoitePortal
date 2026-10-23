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

## 2026-10-22 verified corrected-runtime artifact
- **GitHub Actions build:** https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39797361259 (source commit `c4424e0bac8b3de5c4a8b8a81fac168700f8b7a3`). All workflow steps (including embedded runtime path verification and JNI library checks) passed; artifact `touhou-pocket-runtime-preview-apk`, artifact ID `12433458959`.
- **Local artifact:** `TouhouPocketLauncher-Box64-PathFix.apk`, 209,109,059 bytes, SHA256 `fe91992dd1177190e500a06fb660ad4d9e624f2af5e6d628871417a97ff338de`.
- Confirmed APK ZIP integrity, bundled Wine rootfs and LGPL notices, 35 native `.so` files none containing stale `/data/data/com.winlator`, and Box64 ELF PT_INTERP ` /data/data/com.touhoupk/files/rootfs/lib/ld-linux-aarch64.so.1`. Rootfs has `./lib -> usr/lib` symlink and `./usr/lib/ld-linux-aarch64.so.1` exists.
- **Not tested on Galaxy yet**. This is a separate Android package (`com.touhoupk`) labeled `Touhou Pocket Test`. Install it without uninstalling older `games.charoite.touhoupocket.runtime` package; saves/data don't auto-migrate. Import owned original game files to new app.
- Next user action: open Touhou Pocket Test, Set Up Game Engine, import full base TPDP game or full installer directory with data, run; if it fails, collect View Last Launch Diagnostics > Copy Report. Confirm Box64 no longer has EACCES before addressing game-specific compatibility.


## 2026-10-22 Japanese font and locale compatibility milestone

User reports **Box64 and the Touhou Windows installer now load** on the Galaxy S26 Ultra in **Touhou Pocket Test** (`com.touhoupk`), but installer and Wine display garbled Japanese text. This is progress: the previous native `EACCES` startup blocker is solved on actual hardware.

**Diagnosis (confirmed from unpacked APK):** Winlator's pinned Wine rootfs provides compiled locales only for `en_US.utf8`, `pt_BR.utf8` and `ru_RU.utf8`. Its guest environment defaults to `LC_ALL=en_US.UTF-8`. No Japanese CJK font was bundled/registered. Japanese Shift-JIS CP932 game installers generally need the Japanese locale **and** a font capable of drawing Japanese characters; supplying a font alone cannot fix mojibake.

**Changes on main:** 
- `runtime-preview/build_japanese_support.py` downloads *only during GitHub Actions* official `notofonts/noto-cjk` regular Japanese OpenType (pinned commit `f8d157532fbfaeda587e826d4cd5b21a49186f7c`, verified Git blob `f56224957fb13a81b4c14bac34f2f058a017f9fb`), checks SIL Open Font License and bundles full license. Compiles `ja_JP.utf8` with `localedef` from the **pinned Winlator rootfs i18n definitions** and packs `japanese/japanese-support.tzst`. No font binary is committed to repo; bundled only inside APK.
- `runtime-preview/TouhouJapaneseSupport.java` idempotently installs addon into *existing* private rootfs, copies Japanese font into each Wine `C:\\windows\\Fonts`, writes Win32 font registry and old MS Gothic/Meiryo alias substitutions, configures user locale ja-JP, and reuses markers to protect existing game files.
- `runtime-preview/overlay.py` sets Wine guest `LANG/LC_ALL/LC_CTYPE=ja_JP.UTF-8` for CP932 behavior and calls support installer from `XServerDisplayActivity.setupWineSystemFiles` **before guest execution**. The native Android Touhou interface stays English.
- `.github/workflows/runtime-preview.yml` generates and verifies the locale/font pack and OFL license, plus existing Box64 path integrity checks.
- Pinned source font and licensing: https://github.com/notofonts/noto-cjk/blob/main/Sans/LICENSE and https://github.com/notofonts/noto-cjk/blob/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf

**Important:** GitHub compilation alone does NOT establish fonts render correctly; need new APK test on Galaxy. When build succeeds: install updated Touhou Pocket Test (same app ID; watch for debug signature mismatch), run `setup.exe` and verify Japanese installer text and filenames. If failures, obtain new screenshot and `View Last Launch Diagnostics`; inspect addon extraction, font registry, locale `LC_CTYPE`.


## 2026-10-22 current Japanese language-build identity

Because previous `com.touhoupk` APKs were GitHub Actions debug-signed and reinstall/update may fail due to changing debug signatures, **the Japanese language test APK is intentionally a separate package**: `com.touhoujp` (label **Touhou Pocket JP Test**). The native Box64 ELF path rewrite and all package-path checks were also changed to `com.touhoujp`. KEEP earlier `com.touhoupk` installed and do not clear it; Japanese APK requires importing user-owned source game files again, and old private saves do not migrate. **Do not share font files individually**; the SIL-OFL Noto asset is incorporated only in the app with license notice.

Live build after locale+font+package modifications: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39806100268. Check success and artifact before providing APK or claiming compatibility. Need verify ja_JP.UTF-8 generated and font extracted at runtime, Japanese Shift-JIS installer text shown correctly on Galaxy before adding Shard of Dreams expansion.


## 2026-10-22 Japanese support APK build verified
- Successful GitHub Actions workflow: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39806100268 (source commit 06b447d0bf4ae38bc6b2b9e6f4506ebe27b50fb4). Artifacts: `touhou-pocket-runtime-preview-apk` ID 12437728576 and `touhou-pocket-runtime-legal` ID 12438311671.
- Android app ID com.touhoujp; launcher name Touhou Pocket JP Test. New separate Android package; older com.touhoupk remains installed with own files/saves. User should not uninstall old.
- Verified APK `TouhouPocketLauncher-Japanese-Support.apk`, size 223153363 bytes, SHA256 4766744eb792dda10b33c943044759f1dcec51f2ef53e71db5cc67de132e7197, archive integrity passes. Contains `assets/japanese/japanese-support.tzst` (14046021 bytes), `assets/licenses/NotoSansCJK-OFL.txt` (4301 bytes), 35 native `.so` libs, and has GitHub CI checks for Box64 loader and native path.
- Tested by GitHub: archive packing, compiled ja_JP locale assets, Japanese font source Git blob pin and OFL license, source compilation and packaging, Box64 native paths. NOT YET tested on Galaxy device for actual kana/kanji display, Shift-JIS decoding, setup UI, or game play.
- User Galaxy test: install new APK alongside old, tap Set Up Game Engine, reimport original complete Puppet Dance Performance installer folder, run setup.exe and verify Japanese text/folder names. If garbled, send screenshot plus View Last Launch Diagnostics. Font addon applies to any existing Wine prefix at first game launch.


## October 22, 2026 — Japanese path rendering and app icon (current work)

User supplied screenshot of Touhou Puppet Dance Performance installer. The Japanese body text renders normally after Noto Sans CJK JP / ja_JP locale support, but the **editable install folder path after `C:\game\FocasLens\` shows square glyphs**. This could cause a damaged/incorrect install folder; don't interpret it as just cosmetic. User separately requested a Touhou-themed home-screen icon.

Changes on **main**:
- `runtime-preview/TouhouJapaneseSupport.java`: moves font-registration marker to v2 so older prefixes receive upgrades; adds HKCU `Software\Wine\Fonts\Replacements` aliases (MS Gothic, MS PGothic, Japanese fullwidth MS fonts, Meiryo, Yu Gothic, MS Mincho) to cover Wine GDI editor controls in addition to previously registered HKLM Windows fonts; sets Japanese `ACP/OEMCP=932` under the Wine NLS CodePage key and continues using ja_JP.UTF-8.
- `runtime-preview/TouhouEntryActivity.java`: new `COPY SAFE ENGLISH INSTALL PATH` button copies `C:\Touhou\TPDP` to Android clipboard. User may paste/type it into old Japanese installers as an alternative to garbled Japanese destination names. This is a user-initiated workaround, not an automatic rewrite of game install files.
- `runtime-preview/touhou_pocket_icon.xml`: **original Android vector home-screen icon** with dark violet background, red shrine/torii ribbon, cherry blossoms and handheld-console yin-yang display, inspired by Touhou/Pocket theme, not official game art. `overlay.py` installs it as app icon and round icon. Detailed image concept also generated in chat, but vector is actual committed launcher icon.
- New Android package ID `com.touhouv2` (same byte length as old Winlator package for ELF relocations, **new app installed side-by-side**) with title Touhou Pocket Launcher to protect prior installed Japanese test package `com.touhoujp` and saves/imported games. `rewrite_prefix.py`, `overlay.py`, and CI native path checks all updated.
- Large Japanese asset archive triggered intermittent `:app:compressDebugAssets Java heap space`; bumped Gradle JVM heap to 4 GB and capped workers at 2 in workflow. Watch latest CI for success; do not claim APK exists until workflow passed.

Next: monitor [runtime workflow](https://github.com/rgarn023/TouhouPocketLauncher/actions/workflows/runtime-preview.yml), get successful APK artifact, inspect package name/icon and Noto locale pack, then ask user to test Japanese installation path in v2 app, preferably first with ASCII `C:\Touhou\TPDP` to prevent folder corruption. If square glyphs persist, obtain diagnostic report and targeted screenshot. Once base TPDP install works, continue Shard of Dreams/English patch development.

## Verified Japanese path / Touhou icon APK (October 22, 2026)
- **GitHub Actions successful build**: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39809232621; source SHA `234e0ace08fc206b3b33ead397cbaed686c39098`, run status `completed/success`. Artifact: `touhou-pocket-runtime-preview-apk` ID `12438758004`, archive `TouhouPocketLauncher-JP-IconFix.zip`.
- APK exported as `TouhouPocketLauncher-JP-IconFix.apk`, **222,028,184 bytes**, SHA256 `9a4c34e199183e8a029dc9d8dbef903c80d99cf70b6c82b6e317d3a4cb03c505`, ZIP integrity passed. APK includes `res/drawable/touhou_pocket_icon.xml`, Japanese add-on and Noto font SIL OFL license, and 35 native libraries.
- **App ID `com.touhouv2`**, label `Touhou Pocket Launcher` (separate install from prior `com.touhoujp` so old imported files not overwritten). This is a dedicated Touhou icon (purple pocket console + red shrine ribbon + yin-yang, cherry petals), distinct from detailed concept image generated in chat.
- Japanese font registry patch v2 (new alias keys under Wine\Fonts\Replacements and Japanese ACP 932/OEMCP 932) plus first-class `COPY SAFE ENGLISH INSTALL PATH` button. This copies `C:\\Touhou\\TPDP`. If old installer displays squares in editable Japanese path, user should replace it with this ASCII name, manually typing if Android clipboard can't paste into Wine.
- Old user screenshot: installer text readable Japanese but path `C:\\game\\FocasLens\\...` shows square glyphs. It is unsafe to assume those represent a valid path; encourage English-only name as temporary workaround.
- **Not yet tested on phone**. Need actual Galaxy S26 Ultra screenshot confirming edit control and installing TPDP to ASCII path / existing data. Future work: font issues, standalone English patch/SoD/Extended support. ChatGPT sole developer directly GitHub main.


## 2026-10-22 follow-up: Japanese path still appears as square blocks

User retested screenshot after previous CJK v2 font / codepage update: the installer body text is Japanese and readable, but its default folder edit field still shows square boxes following `C:\\game\\FocasLens\\`. User explicitly wants the blocks fixed, not just a manual ASCII workaround.

Source investigation: Microsoft documentation confirms **MS Shell Dlg** and **MS Shell Dlg 2** are the logical fonts used for Windows dialog controls including edit boxes. Our previous font aliases lacked these. Wine font fallback and dialog selection can differ from static labels.

Implementation now on `main` (commit `6979b572cdd2c6ffc0f5da8cd2996ce7a9fbbd14`):
- `runtime-preview/TouhouJapaneseSupport.java`: font registration marker v3 so existing prefix receives new rules; adds **MS Shell Dlg**, **MS Shell Dlg 2**, **Tahoma**, and **Microsoft Sans Serif** etc. aliases to Noto Sans CJK JP in both Wine user font replacements and Windows HKLM FontSubstitutes.
- Installs a Touhou-only Fontconfig alias under private rootfs `etc/fonts/conf.d/66-touhou-japanese.conf` preferring Noto Sans CJK JP for MS Shell Dlg / MS Shell Dlg 2 / Tahoma and generic sans-serif.
- Existing CP932 and ja_JP.UTF-8 settings retained.
- Separately, the direct ASCII path option / Inno Setup `/DIR` is now implemented in UI and Wine launch backend (earlier commits `5ca5293` and `1ba5f2`). This is a **fallback** for cases where the legacy installer cannot display its Japanese default path; not a substitute for trying the font fix.

References: https://learn.microsoft.com/en-us/windows/win32/Intl/using-ms-shell-dlg-and-ms-shell-dlg-2 ; https://learn.microsoft.com/en-us/globalization/fonts-layout/fonts

Build run: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39811685139 ; check status/artifact before asserting APK available. New test package `com.touhoudr` is separate from prior `com.touhouv2`; do not uninstall old APK or lose imported data. **On-device font result unverified**. If still squares, may be encoded source string rather than missing font; collect exact diagnostics and test ASCII/Inno destination. Do not promise guaranteed font fix.


### Latest Japanese dialog-font test artifact confirmed
GitHub Actions successful on 2026-10-22, run https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39811685139, commit `6979b572cdd2c6ffc0f5da8cd2996ce7a9fbbd14`.
Artifact `touhou-pocket-runtime-preview-apk` (ID `12440597508`), extracted APK `TouhouPocketLauncher-FontControlFix.apk` 222,029,800 bytes, SHA256 `23b906015794d1f2f735397144e40db9364c748ab652d068e51781371dfe4350`. Container ZIP test passed. Package `com.touhoudr` (separate from user's previous `com.touhouv2`), preserves old app data on device; requires importing user-owned game files again.

The new runtime patch specifically maps MS Shell Dlg / MS Shell Dlg 2 / Tahoma / Microsoft Sans Serif to Noto Sans CJK JP in registry and adds a Touhou-private fontconfig fallback. Dialog-box Japanese rendering is **not yet confirmed on Galaxy**, only compile/package. If the install path still renders squares, debug possible replacement characters in the actual ANSI string (not merely missing GDI glyphs) and leverage the validated `/DIR` ASCII override from native installer destination prompt as a temporary fallback. Do not state problem definitively solved until real screenshot shows it.


## October 22 — duplicate installer cards and unreadable install path

User supplied two screenshots: Touhou Pocket library contained **two separate entries both named "Windows installer: setup.exe"**, and the Windows Japanese installer continued to show squares in destination after `C:\\game\\FocasLens\\`. User explicitly wants **one installer once a path is chosen**.

### Root cause and fix committed to main
- `TouhouEntryActivity.saveEntry()` used to simply append every imported installer to JSON library. This caused all imports to accumulate. It now **replaces any previous installer entry with the newest selection** and preserves existing actual game entries. Older library versions are **migrated on load**, collapsing duplicate installer entries (keeping newest), but **without deleting private imported files**, to protect source game files and saves.
- Each installer now has **one "INSTALL" button**, not two separate installer actions. It opens an Android destination dialog, default `C:\\Touhou\\TPDP`, with **Install to this folder**, **Use installer's original path** (fallback), and Cancel. Installed game cards remain Play.
- `overlay.py` adds a quoted, validated `/DIR="C:\\Touhou\\TPDP"` option for compatible Inno Setup installers to override their original Japanese path *before* edit field appears, and records locally that an override was requested. Official Inno Setup documentation: https://documentation.help/Inno-Setup/topic_setupcmdline.htm .
- The screenshot shows body Japanese labels render while destination field stays boxes **despite Noto CJK + Wine GDI aliases**. This might be a legacy installer using damaged ANSI encoding, not simply missing glyphs; **do not promise /DIR fixes underlying Japanese text rendering.** Focus on preserving a valid ASCII installation path and verify installer actually accepts /DIR on the Galaxy.
- Current app package remains `com.touhoudr` to attempt in-place update; however GitHub debug signing can vary, so **avoid uninstalling app with valuable imported files** unless user has their originals/backups.
- Commit `a816ccd81dfca9f4ba2660226ab10ea0a83f33b7` dedupes, commit `4cfad6d2f19a4d36fb3267cb59686083d92af723` improves /DIR log/quoting. Latest active workflow run https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39813693166 ; **verify result and artifact before distributing APK**.

### Next device acceptance
1. Install/update successful APK and open library: exactly one installer entry despite two legacy setup.exe imports, existing TPDP game card still present.
2. Tap INSTALL, accept `C:\\Touhou\\TPDP`, verify destination field now displays ASCII rather than boxes and installation proceeds.
3. If still shows Japanese blocks, open View Last Launch Diagnostics and confirm the `Installer /DIR override requested` line; investigate whether installer supports Inno Setup /DIR and its launcher command assembly.
4. If user selects full install folder with multiple files, preserve installer resources; `Find Installed Touhou Games` should locate executable after install.
5. Keep next priority TPDP base gameplay, then Shard of Dreams, Extended, and English patches.


## Duplicate installers / verified build result (October 22, 2026)
- **One-installer library policy committed** `a816ccd81dfca9f4ba2660226ab10ea0a83f33b7`. Existing persisted libraries automatically collapse duplicate installer records to the latest one, retain game cards. Newly imported installer replaces prior installer listing. **No old game files or old staging files deleted automatically.** UI shows one button called INSTALL, destination popup has Install to this folder / Use installer's original path / Cancel.
- **Inno path workaround** command logging/quoting commit `4cfad6d2f19a4d36fb3267cb59686083d92af723`. Uses direct validated quoted `/DIR="C:\\Touhou\\TPDP"` before Inno Setup opens. Inno Setup supports /DIR (https://documentation.help/Inno-Setup/topic_setupcmdline.htm). Actual TPDP setup response on Galaxy requires testing; don't claim unreadable Japanese default fixed. If /DIR ignored, investigate whether executable is Inno Setup and how winhandler relays args.
- **GitHub Actions run** https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39813693166, job 119946896802 succeeded with APK artifact `touhou-pocket-runtime-preview-apk` (ID `12440369528`), source SHA `4cfad6d2f19a4d36fb3267cb59686083d92af723`. Extracted `TouhouPocketLauncher-OneInstaller.apk`, **222030924 bytes** SHA256 `7d7ad40e3ba23fbf4cf6a56e8c17d352eafae4ff150b3021038c8e8d1a080608`, APK and artifact ZIP CRC verification both passed, Japanese font pack & OFL license included.
- Android appId remains **com.touhoudr**, same as previous font fix. Debug-signing key might differ between GitHub Actions runners; if Android refuses to update, don't tell user to uninstall without first protecting existing game files/saves. An alternative side-by-side package or stable signing key is needed for future reliable upgrades.
- First device test: install new APK if possible, confirm library has one installer and existing game card; press INSTALL, accept `C:\\Touhou\\TPDP`, verify Windows destination field now shows exactly ASCII. Tap Next, complete installation, and press Find Installed Touhou Games. If still blocks, share View Last Launch Diagnostics to check `Installer /DIR override requested` log and note whether installer ignored option.


## 2026-10-22: user explicitly wants original installer destination, no overrides

User's most recent screenshot still showed boxed characters after `C:\\game\\FocasLens\\`. User explicitly stated: "**I only want installer to run original path**" — interprets as no custom ASCII install destination and no injected Inno Setup `/DIR` option. Respect this preference, do not suggest forced `C:\\Touhou\\TPDP` as standard flow.

Committed on `main`:
- `runtime-preview/TouhouEntryActivity.java` commit `3aaecdc269a45a7fc9d5d3684017ed8c0637d5ad`: removed `selectInstallerDestination` dialog, safe English copy-path button, overloaded `launchGame(path, destination)`, `touhou_setup_dir` extra. Each installer now has ONE Install button that starts original `setup.exe` unchanged. Installer duplicate collapse remains.
- `runtime-preview/overlay.py` commit `1d269ad5214ec391d378c361af5d13b4b063ac75`: removed previous injection of `/DIR=` option into Wine's `winhandler.exe` launch command. Original user/installer-specified default paths preserved.
- Latest GitHub Actions build from this commit: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39816320818 . Verify success before giving download link. Package remains `com.touhoudr`; debug-signature mismatch can prevent in-place update and old app's imported files must be protected.

**Important:** Japanese square glyph rendering in the installer destination remains unresolved. Do not equate preserved original destination with correctly decoded Unicode/CP932 path. Most other Japanese labels do display, suggesting specific legacy edit-control font/codepage issue. Do not keep reintroducing English-only forced destination contrary to user intent. Collect device diagnostics or investigate actual source ANSI string behavior if user requests character fix.

Next: Verify latest workflow passes, produce APK. Ask user to confirm no extra path prompt and only one installer entry, plus whether installation completes and preserves Japanese directory after clicking Next. Then continue TPDP game compatibility and expansions as requested.


## VERIFIED original-installer-path build — Oct 22, 2026
- User explicitly requested original installer's destination path. Implemented removing all custom ASCII overrides, Android destination prompts, and any /DIR command-line options; starts selected setup.exe unchanged with its own default installation directory. Existing one-installer library dedupe remains intact.
- Successful GitHub Actions run: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39816320818, SHA `1d269ad5214ec391d378c361af5d13b4b063ac75`.
- Artifact `touhou-pocket-runtime-preview-apk` ID `12442132651` exported as `TouhouPocketLauncher-Original-Path.apk`. Size `222029232` bytes, SHA256 `15c54bf080887f6c6740cda4e09dba0a4aeaa88e68ca2725f02d5eb84d0aeaf6`. ZIP CRC checked, contains Japanese support assets and 35 native .so files.
- Package ID remains `com.touhoudr` to attempt update over prior same-ID release. APK signature could differ between CI runners; if Android refuses update do NOT instruct immediate uninstall because app-private games and saves can be lost.
- The Japanese path glyph issue is **unresolved**; don't claim original characters are now displayed correctly. User should check whether the original folder path can install successfully while retaining Japanese directory naming. If failure, investigate Japanese CP932/ANSI code-page rather than restoring automatic /DIR workaround.


## Japanese rendering prioritized over all expansion work (2026-10-22)

User explicitly says: **"I want to fix Japanese rendering issues first."** Pause Shard of Dreams, Extended, English patches, and launcher design expansion until the *original installer default Japanese destination* renders legibly in Wine on Galaxy S26 Ultra. **Do not replace the original installation path with `C:\\Touhou\\TPDP`**: user explicitly rejected this. Preserve installer without custom `/DIR`. Keep library's single-installer deduplication.

Repeated screenshots show body/dialog text readable Japanese, but destination field after `C:\\game\\FocasLens\\` displays square glyphs. Previous Noto Sans CJK JP OTF + MS Gothic and MS Shell Dlg aliases + ja_JP.UTF-8 + CP932 failed on the real device.

Latest implementation targets true Japanese UI fonts, not just adding generic aliases:
- `runtime-preview/build_japanese_support.py` now retrieves official **IPA Gothic** `ipag.ttf` (fixed-width) and **IPA P Gothic** `ipagp.ttf` (proportional), from CTAN mirror, verifies MD5 checksums published by IPA font publisher for v003.03 (https://moji.or.jp/ipafont/fontspec00303/), includes IPA Font License 1.0. Keeps Noto Sans CJK JP and ja_JP.UTF-8. IPA fonts are TrueType outlines; Noto was OpenType CFF.
- `runtime-preview/TouhouJapaneseSupport.java` upgrades existing private Wine roots (checks IPA TTF existence even if Noto already installed), copies IPA TTF to C:\\windows\\Fonts, registers font names, maps MS Gothic / MS PGothic / MS UI Gothic / MS Shell Dlg and 2 / Tahoma / Japanese fullwidth font names to IPA or IPA P Gothic in Wine and Windows registry, switches Wine dialog font to IPA P Gothic, rewrites previously Noto-only Fontconfig fallback. Font marker v4; no game data intentionally deleted.
- `.github/workflows/runtime-preview.yml` checks IPA license and updated compressed font archive, adds license to legal bundle.
- Relevant commits: `3e03c46a5d047266a400558e52c64858aa2740c4`, `480ab98203343114e18ff3a80169133144fd128b`, `f81ea4d5460663023835a42d48d11156cfaad4ee`, `65743c4922606e8a9732a8b66ea454a2b17ec073`, `77191c9173ae3965b1f912877dade5cc2097db17`.
- Check workflow https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39818493950 before distributing an APK. CI passing does NOT establish legibility on actual phone. Package remains `com.touhoudr`; upgrading over earlier CI debug-signed package can fail and old app-private game/saves must not be deleted.
- If installer default remains blocks after v4 TrueType: **stop repeating registry font substitutions**; investigate whether installer input string is already replacement chars, Wine ANSI GetACP actually returns CP932, and font coverage/selection at runtime. Could add a small Windows-side codepage/glyph probe. Do not use forced ASCII destination workaround user rejected.


### Verified IPA Gothic Japanese-rendering APK build — October 22, 2026
- GitHub Actions **completed successfully**: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39818493950, source SHA `77191c9173ae3965b1f912877dade5cc2097db17`. Artifact `touhou-pocket-runtime-preview-apk` (ID `12444275240`), legal artifact `12443387246`.
- APK copied to `TouhouPocketLauncher-IPA-Japanese.apk` in local conversation container. Size `231424174` bytes, SHA256 `64f67a04f5aa3048ec73c70f1ef165450314eab7a7ef5d94c9594b2f8e6a495d`, ZIP integrity verified; addon includes `ipag.ttf`, `ipagp.ttf`, existing `NotoSansCJKjp-Regular.otf`, and `ja_JP.utf8`. APK includes both IPA Font License 1.0 and Noto OFL licenses.
- User device has **not** yet tested TrueType rendering. Request exactly whether *original Japanese destination after C:\\game\\FocasLens\\* appears as kanji/kana or squares; ask for screenshot if still blocks. Original path preserved—**no /DIR**. Do not claim confirmed fix merely because APK builds.
- App ID remains `com.touhoudr` (in-place upgrade attempted); Android debug signing may mismatch between CI runners. If upgrade is rejected, **do not uninstall existing app with imported games or saves without backups**.
- If still squares, investigate legacy ANSI/CP932 string values inside Wine's installer process with an actual Windows-side GetACP, GetLocaleInfo, GDI glyph diagnostic instead of another ungrounded registry alias attempt.

## Critical Japanese text regression — October 22, 2026
- User tested IPA TrueType APK and sent screenshot showing **much worse rendering**: almost all Japanese installer text (not only installation path) becomes square boxes / vertical bars. Clearly a regression versus earlier Noto APK. User: "Even more messed up".
- **Root cause verified with actual IPA TrueType files extracted from APK and FontTools name metadata**: `ipag.ttf` internal family/PostScript name is `IPAGothic`, and `ipagp.ttf` is `IPAPGothic` (**no spaces**). We had mistakenly registered Wine/Fontconfig aliases to nonexistent `IPA Gothic` and `IPA P Gothic`; they were used for all Windows dialog text, causing squares across the installer.
- Fix on main: in `runtime-preview/TouhouJapaneseSupport.java` replace font aliases/fallbacks with **exact** internal family names `IPAGothic`, `IPAPGothic`; upgrade per-prefix font registration marker from `v4` to `v5` to repair existing Wine installations *without deleting user games/saves*. The app preserves original installer path; there is no /DIR override. Commits `e73b3c4bfe753121c42b7b2e7c04d257ecdfdee9`.
- In `runtime-preview/build_japanese_support.py`, use `fc-scan --format %{postscriptname}` to verify real internal family names during GitHub build, fail CI on mismatch; make command mandatory in workflow. Commits `d9bbc8b70ce01e00fe34805a68b8ffd29e424235`, `d004ab7c0f22da2691cb475429ee13bb983a7729`.
- CI latest build https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39833614572 was queued when handoff written. **Do not claim new APK tested on device**; complete CI and inspect APK before delivering, then ask user to verify installer Japanese text on Galaxy. If **destination path alone** remains squares after text regression fixed, investigate CP932 GetACP + specific edit-control string instead of more speculative font substitutions.
- **Keep prior data**: package remains `com.touhoudr`; don't suggest uninstall unless they back up old imported files/saves. User explicitly requires original installer path unchanged, one installer entry, and no alternate ASCII /DIR workaround.


## Verified v5 IPA font-family name repair APK (2026-10-22)
- GitHub Actions succeeded: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39833614572; source commit `d004ab7c0f22da2691cb475429ee13bb983a7729`; artifact `touhou-pocket-runtime-preview-apk` ID `12450430881`. Output file `TouhouPocketLauncher-IPA-Family-Fix.apk`, 231423870 bytes, SHA256 `5330efa6ceffbc10c0c0fbe8de396d0e4ba682eb54469100e7981b1372578579`. APK outer and inner ZIP CRC verified; bundled Japanese addon, IPA and Noto licenses, 35 JNI shared libraries.
- Local fontTools verification of prior APK font files: `ipag.ttf` internal PostScript/font family `IPAGothic`; `ipagp.ttf` family `IPAPGothic`. Previous runtime registry/Fontconfig referenced **nonexistent** families with spaces `IPA Gothic` / `IPA P Gothic` for broad Windows dialog substitutions, causing user-reported widespread Japanese glyph blocks. This was a direct regression of our code.
- Fixed v5 source `TouhouJapaneseSupport.java`: exact `IPAGothic`, `IPAPGothic` family refs, including Fontconfig; v5 registration marker so *existing* Wine prefix upgrades without deleting saved game data. Build script now uses `fc-scan` to verify each pinned IPA font has exact expected PostScript family name. Existing Noto and ja_JP.UTF-8 support retained.
- No forced installer paths, /DIR changes, or extra installer entries. App package remains `com.touhoudr`. User should update existing if Android accepts signature, without uninstalling/clearing data. The **new APK has not yet been tested on the user's Galaxy**. A successful GitHub APK build does not prove actual Japanese installer rendering.
- First acceptance: screenshot of original TPDP installer welcome/destination after v5. We expect broad Japanese UI text to recover, but **original destination-path-only boxes may remain** (separate unresolved encoding/edit control question). If so, target CP932 GetACP / actual edit-control text and font selection with diagnostics, not repeated blind font guesses.


## 2026-10-22 — Japanese destination remains squares, diagnostic-first investigation

User screenshot `157033.jpg` shows **the broad Japanese dialog recovered** with v5 internal IPA font-family names, but the install path still shows boxes after `C:\\game\\FocasLens\\`. The user explicitly wants Japanese path rendering fixed, and wants **original installer path unchanged**. Previous speculative font alias changes didn't fix path. Do not repeat blind font replacements or introduce /DIR.

Latest milestone is **read-only diagnostics to determine whether the installer edit control actually contains Japanese characters or corrupted text**:
- New `runtime-preview/touhou_probe.c`: source-only original Windows x86_64 diagnostic, compiled with mingw-w64 during GitHub Actions, app asset `japanese/touhou_probe.exe`, installed as `C:\\touhou_probe.exe` in existing private Wine C drive. It opens no window, modifies no game paths, performs no network I/O. It reads `GetACP`, `GetOEMCP`, and the **UTF-16 hexadecimal code units** of installer EDIT controls via `EnumWindows`, `EnumChildWindows`, `SendMessageTimeoutW(WM_GETTEXT)`, and checks Japanese glyph coverage of selected GDI font using `GetGlyphIndicesW`. Writes `C:\\touhou_probe.log`.
- `runtime-preview/overlay.py` adds probe binary to assets at build time; instruments `GuestProgramLauncherComponent` to spawn the read-only tool within the *same Wine session* ~9s after setup.exe started, and kills process on stop.
- `runtime-preview/TouhouJapaneseSupport.java` copies probe to each Wine prefix and clears prior log. Existing v5 IPA font and Japanese locale remain, no original path override.
- `runtime-preview/TouhouEntryActivity.java` records log path for active installer launch; `TouhouDiagnostics.java` includes probe output in **View Last Launch Diagnostics -> Copy Report**, locally only. User chooses whether to paste report in chat.
- `.github/workflows/runtime-preview.yml` installs mingw-w64, compiles EXE, checks embedded MZ asset and derivative source/attribution.
- Source changes all committed on existing `main`; latest integrated workflow https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39840179331. Check the **latest CI status**, fix failures, and produce APK only after success. **No on-device probe report yet**, so cause of destination squares is unresolved.
- For first test: install/update APK preserving existing `com.touhoudr` data. Run original setup.exe, navigate to destination-page screenshot with boxes, leave it open ~15-30 seconds for probe, then return to launcher, **View Last Launch Diagnostics > Copy Report** and share. Look for `GetACP=932`, the destination UTF16 hex values (Japanese range U+3040..U+9FFF vs U+25A1/FFFD/003F), and selected font's glyph presence. If log missing, instrument file/path/pid rather than guess.
- Root cause discrimination: Japanese UTF-16 code units + selected font missing glyph -> font-selection; literal U+25A1/U+003F or non-Japanese values -> encoding/data corruption; GetACP !=932 -> code page/locale. Microsoft docs emphasize `GetWindowTextW` doesn't access another process's child EDIT field: must use `WM_GETTEXT` via `SendMessageTimeoutW`.


### Verified Japanese path diagnostic APK (October 22, 2026)

- GitHub Actions build job successful for workflow run https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39840722147, commit `defaffdf30d620b95abb200f3cf5ba76e0c56f5c`. Artifact `touhou-pocket-runtime-preview-apk`, ID `12452118939`; source/legal artifact `12453395986`. APK local artifact `TouhouPocketLauncher-Japanese-Path-Diagnostics.apk`, 231536652 bytes, SHA256 `e05124252f9d501fc53712362adb6c9625e021fa6916cd0ea279162693bfa285`, outer/inner archive ZIP CRC verified. Contains 259359-byte `assets/japanese/touhou_probe.exe`, IPA and Noto licenses, 35 JNI .so libraries.
- Current font rendering regression from wrong IPA families is fixed as of prior v5; user screenshot `157033.jpg` shows dialog readable but edit control path squares. The probe does NOT change original installer path. `com.touhoudr` continues as Android ID. User must protect app-private game data on updates, and avoid uninstall/clear data.
- First phone test: open current original `setup.exe`, move to destination path where blocks appear, leave screen there 15–25 seconds. Exit/return to Touhou Pocket and choose **View Last Launch Diagnostics -> Copy Report**, paste here. It should include `GetACP`, hex codepoints of edit field, and selected GDI font glyph coverage if Win32 probe runs; if report missing check `Read-only Japanese installer probe started (pid=...)` in process diagnostics, Wine filename, Wine prefix paths.
- Diagnose based on actual codepoints: Japanese actual values (U+3040-30FF, U+4E00-9FFF) and GDI missing glyphs -> font selection; literal U+25A1 squares, U+FFFD replacement, or U+003F question marks -> encoding already corrupted; GetACP not 932 -> Wine code page. No further speculative fonts or forced ASCII `/DIR` unless the user explicitly changes requirements.


## 2026-10-22: v2 diagnostic for Wine named-desktop installer text

User supplied diagnostic report from v1:
```
Game: setup.exe
Status: game window appeared
touhou-probe-v1 GetACP=932 GetOEMCP=932 GetUserDefaultUILanguage=0411 GetSystemDefaultUILanguage=0411
No supported installer destination edit control found in 60 seconds.
```
**Supported inference:** Japanese ANSI/OEM codepages and UI language are set as expected (932/932/0411), **but v1 missed the target field**, so cannot conclude whether source UTF-16 path is correct, corrupted, or merely missing glyphs. The user wants the *original Japanese install path* unchanged; NO `/DIR` override.

**New v2 source and successful APK build:** `runtime-preview/touhou_probe.c` rewritten to enumerate all visible Wine top-level windows without filtering Japanese titles, identify `Edit` and `Combo` classes, examine UTF-16 of candidate path fields, check the GDI font's Japanese glyph support, and crucially enumerate **all Wine virtual desktops** with `EnumDesktopsW`, `OpenDesktopW`, and `EnumDesktopWindows`. It logs window/desktop/child/edit counts when no path is found, so v2 failure is actionable. Does not call SetThreadDesktop or alter windows. CI compiles Win32 probe with mingw.

- GitHub Actions successful build: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39843184436 ; source commit `265050ffc77aa5fef426c98bbf768a2e9f922ba0`; artifact `touhou-pocket-runtime-preview-apk` id `12454600810`.
- Exported APK: `/mnt/data/TouhouPocketLauncher-Japanese-Desktop-Probe-v2.apk`, 230409216 bytes, SHA256 `cd64b057e327735609aec08e982ca19d4df2cf56af16ba46ec50ce597cc614fa`. Outer GitHub ZIP and inner APK CRC verified. Contains `assets/japanese/touhou_probe.exe` and both Japanese IPA and Noto font licenses. On-device operation **not tested**.
- User test: install over existing `com.touhoudr` if Android signature accepts **without uninstalling/clearing app data**. Open already-imported original `setup.exe` > page where Japanese default folder shows blocks; leave screen ~20–30 seconds (v2 polls up to 60 sec) > return to launcher > View Last Launch Diagnostics > Copy Report > paste full output.
- v2 output should contain `touhou-probe-v2`, `desktop: name=`, `pass=... desktops=... windows=... edit_candidates=...`, and hopefully `PATH FOUND class=...` codepoints and `font: name=... missing_known_japanese=...`. If absent, determine whether desktop enumeration failed or installer uses custom-drawn control; do not blindly add fonts again.
- If `GetACP=932`, path codepoints include real Japanese characters but font reports missing glyphs -> font selection; if stored codepoints are literal squares/question marks/replacement chars -> already-corrupted string; if path not visible through desktop, try attaching diagnostic to Wine virtual desktop `nogui` directly or targeted window inspection. Avoid user-game changes.


## 2026-10-22 latest probe report and direct fix (v3)
User provided the **full v2 report** showing `GetACP=932`, `GetOEMCP=932`, Japanese UI language `0411`; probe enumerated desktops `Default` (0 windows) and `nogui` (14 to 16 windows) and saw the actual installer top-level classes `TWizardForm`, `TMainForm`, `TApplication` with valid Japanese UTF-16 title, but every window had `visible=0`, `child_controls=0`, `edit_candidates=0`. This is **NOT** evidence the Japanese path is corrupted; the probe never inspected its EDIT control. It was skipping EnumChildWindows behind `IsWindowVisible(hwnd)` in `runtime-preview/touhou_probe.c`. The virtual desktop reports wizard invisibility even when displayed on user's phone.

### Changes on GitHub main
- Source commit `cf792081ca7c53d133036bc9d4ee68d806533b19`: probe v3 calls `EnumChildWindows` on EVERY enumerated top-level Wine window without `IsWindowVisible` filtering; still performs read-only `WM_GETTEXT` and selected font glyph tests. Changes no installer arguments or paths.
- Source commit `0db534bf265533de0e171a521556efd45fd540ce`: overlay changes upstream visible `Starting up...` resource to `Launching Touhou game...` and background notification text from Winlator to Touhou Pocket Launcher. This **does NOT** remove the Winlator-derived source/backend. User expressed frustration: \"I also noted that this is still a winlator application. Why? I thought we went away from winlator\". Honest answer: current project is a branded/repackaged source fork of Winlator retaining original engine, container/graphics/input; frontend is Touhou-specific. True removal of Winlator code requires replacement Android Wine/Box64 integration and isn't done. Avoid saying fully independent from Winlator or masking attribution.
- Latest combined CI run: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39845465950 (check complete/success/artifact before providing APK). Earlier run `39845387072` only has v3 probe, without branding text changes. Maintain APK ID `com.touhoudr` to attempt update, preserve user game data.

### Immediate next
Check latest GitHub Action run `39845465950`, fix build errors and extract APK. User installs without uninstalling/clearing data; opens original TPDP `setup.exe`, holds on destination field 20-30 seconds; return > View Last Launch Diagnostics > Copy Report. Expect `touhou-probe-v3` and `child_controls > 0` for `TWizardForm`, ideally `PATH FOUND` codepoint hex + selected GDI font. Then distinguish actual Japanese Unicode vs boxes/replacement and target only verified issue. No `/DIR` override allowed. User wants original Japanese folder unchanged and Japanese rendering fixed first, prior to expansions/translation. Keep Winlator fork status transparent and plan future backend replacement only after current compatibility stable or user explicitly directs.


### Verified v3 installer Unicode probe APK — October 22, 2026
- GitHub Actions completed successfully: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39845465950, commit `0db534bf265533de0e171a521556efd45fd540ce`; artifact `touhou-pocket-runtime-preview-apk`, ID `12455690527`.
- Exact verified APK path in this conversation's working container: `/mnt/data/TouhouPocketLauncher-Japanese-Path-Probe-v3.apk`, 231,538,108 bytes, SHA256 `072d863086034b3051225153c61e1eade854cc35dba94a9ff4e9f480f9fdd8fa`. APK ZIP integrity passed; bundled Win32 `touhou_probe.exe` 262,992 bytes includes literal `touhou-probe-v3`, IPA and Noto Japanese font packs and licenses, original Winlator LGPL license and notice.
- **Not yet tested on user's Galaxy.** In v3, all children of Wine's otherwise invisible `TWizardForm` are inspected without modifying installer controls. Test: update app preserving data, run original `setup.exe`, stay at destination field ~20–30 sec, return to launcher > View Last Launch Diagnostics > Copy Report. Expect `touhou-probe-v3`, `child_controls>0`, `PATH FOUND`, UTF-16 codepoints, selected font glyph counts if Wine permits reading that edit control. If `PATH FOUND` absent but `child_controls>0`, inspect class names and WM_GETTEXT errors; avoid speculative font patches.
- Winlator issue: user asks why app still Winlator; **be transparent** current APK is still built from pinned Winlator source with branded Touhou entry UI and displays, NOT a distinct Wine integration backend. Current changes reword inherited startup as `Launching Touhou game...` and background notification as Touhou Pocket Launcher. This branding change DOES NOT imply code has been replaced. Independent Android integration is a separate substantial refactor that should be scoped separately; preserve existing gameplay startup while Japanese rendering is prioritized.


## 2026-10-22 targeted Japanese edit-font repair (after v3 Unicode diagnosis)

User pasted v3 native Win32 diagnostic showing:
```
GetACP=932 GetOEMCP=932 GetUserDefaultUILanguage=0411
PATH FOUND class=TEdit utf16_units=24
codepoints=0043 003A 005C 0067 0061 006D 0065 005C 0046 006F 0063 0061 0073 004C 0065 006E 0073 005C 5E7B 60F3 4EBA 5F62 6F14 821E
font: name=System missing_known_japanese=6 gdi_error=0
```
**Confirmed:** The destination stores real Unicode `C:\\game\\FocasLens\\幻想人形演舞`, and code page 932 is correct. All six Japanese glyphs are absent in the font selected by diagnostic for the TEdit (System). This is a rendering/font-selection problem; the stored path is **not** corrupted. User wants original destination unchanged, no `/DIR` replacement.

**Code:** `runtime-preview/touhou_probe.c` now v4 additionally attempts scoped `WM_SETFONT` to set `IPAPGothic` only on the matching `TEdit` with Japanese in its path, after verifying the existing font lacks glyphs. It independently tests the IPA font has all six glyphs. It rereads original text after the font change and rolls back if the text changed or font change can't be verified. It retains the HFONT while the control exists and frees it on window destruction. It only changes the rendering font of the installer destination edit control, not its directory/path, locale, registry or game files. Logs `font-fix: SUCCESS`, `font-fix: verification failed`, `old-font-is-null`, `selected-font`, and other details.

**Status:** GitHub Actions run https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39849117398 at code SHA `7e7056b324a85f942ef9e79a5ad62ad979810355` **passed**. APK artifact `touhou-pocket-runtime-preview-apk` ID `12456622082`, extracted verified `/mnt/data/TouhouPocketLauncher-Japanese-Font-Repair.apk`, **231540216 bytes**, SHA256 `e2948c740959c41d9c4752f7e27f9d3896b8f8404ca48a4f11668b559c6bdd49`. ZIP integrity passed. Embedded Win32 probe contains v4 and `font-fix: SUCCESS` strings, IPA/Noto font licenses present, 35 native libraries.

**Device validation remains necessary**: Existing Android package `com.touhoudr`, intended in-place update but debug signing may vary; do not uninstall or clear previous app because imported game files/saves are app-private. User should install updated APK if Android permits, open original `setup.exe`, show Japanese destination page, keep it visible ~15-30 seconds; see whether original Japanese characters render. Return to launcher > View Last Launch Diagnostics > Copy Report and share lines beginning `font-fix:` plus screenshot if necessary. If `font-fix: SUCCESS` but squares remain, cross-process GDI font handle/rendering may be unsupported; do not claim success until screenshot. If new font not selected, consider in-process Wine GDI fix or Windows font-link registration, preserving original pathname; avoid restarting blind alias guessing.

**Architecture reminder:** APK remains an adaptation of Winlator for Wine/Box64 rendering. Do not misrepresent it as a fresh independent Wine stack; front-end is Touhou themed, backend still Winlator-derived. User previously requested a more Touhou themed icon; an illustrative mockup was generated but that artwork is not included in this font-repair build. The Japanese rendering issue is still prioritized.


## October 22, 2026 — v4 failure, v5 in-process font shim (CURRENT)

Actual user report:
```
touhou-probe-v4 GetACP=932 GetOEMCP=932 Japanese UILanguage=0411
PATH FOUND class=TEdit utf16_units=24 ... 5E7B 60F3 4EBA 5F62 6F14 821E
font: name=System missing_known_japanese=6 gdi_error=0
font-fix: failed to read current EDIT font; unchanged
```
This **definitively confirms only that v4 never attempted the font change** because external Win32 SendMessageTimeoutW(WM_GETFONT) failed. The codepage and original Japanese Unicode destination `C:\\game\\FocasLens\\幻想人形演舞` are correct. Do not alter the original installer destination or introduce ASCII `/DIR` override.

New v5 source uses in-process targeted Win32 GDI patch rather than cross-process HFONT (MS docs: handles and hooks are process/desktop/bitness sensitive):
- `runtime-preview/touhou_font_hook.c`: a thread-only WH_GETMESSAGE DLL hook running on the original installer's GUI thread; enumerates only TWizardForm's TEdit child whose text matches the untouched full Japanese path. Creates `IPAPGothic` HFONT **inside installer process**, checks all Japanese glyphs and exact face, sends WM_SETFONT, verifies WM_GETFONT == new HFONT and GetWindowTextW identical, reverts if mismatched. Logs `hook-v1: SUCCESS` or failures to `C:\\touhou_font_hook.log`. Does not touch installer folder, files, registry or install arguments.
- `runtime-preview/touhou_font_helper.c`: opens Wine's `nogui` desktop and attaches **thread-specific**, not global, WH_GETMESSAGE hook to installer GUI TID, wakes thread with WM_NULL, unhooks after ~18 seconds. Paired 32/64 bit DLL and helper builds for bitness compatibility. Logs to `C:\\touhou_font_helper.log`.
- `runtime-preview/touhou_probe.c` upgraded v5: safely detects target installer GUI thread and process bitness, starts only matching 32/64 font helper exe instead of attempting unsafe cross-process WM_SETFONT; logs `font-fix: launched in-process helper`. Still records codepage, path codepoints, selected font GDI probe.
- `runtime-preview/TouhouJapaneseSupport.java`: bundles helpers from APK to private Wine C drive and clears old logs at installer startup; `TouhouDiagnostics.java` shows all three files in Copy Report.
- `runtime-preview/overlay.py` copies helper exe and dll assets to package. `.github/workflows/runtime-preview.yml` compiles with both `gcc-mingw-w64-i686` and x86_64 and verifies APK includes each.
- Hooks are localized to TPDP setup.exe when user explicitly runs it in existing launcher; no stock Wine files patched or global Windows hooks. Users must keep originals/backups; don't suggest uninstalling old app due to app-private saves/imports.
- Relevant commits in order: `07226684857535da7eb1792cf8b277ac1928414d`, `78a63a24f6cae759f0169c5d9a89077455b7ad6c`, `2fe993029ac691c5ffda8ad6bda948064d4a6beb`, `6c64983dfd00172f41b1d192043e1885558c1139`, `ae91da92ba5f05e5a06c099ff0d8904df1567229`, `b39dca9154859f332000e2d6a7048404deefaa71`, `28e9b6f99a9fc7ef19e1e335adae9d31fe6873bd`, `257f98d49c89cac1d9828dea24e438a984bdef57`.
- Latest CI run: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39852815210 . **Confirm completed/success and artifact extraction** before presenting build to user. This is an experimental fix: **do not claim on-device success** before screenshot and hook log.
- Test: after successful APK installed (same `com.touhoudr` may have debug-signing update issues), open original `setup.exe`, navigate to Japanese original destination; stay ~20-30 sec, check if blocks now rendered. Back to launcher > View Last Launch Diagnostics > Copy Report. Look for `touhou-probe-v5`, `font-fix: launched...32bit=`, `helper-v1: thread-specific hook installed`, `hook-v1: SUCCESS`, or failure code. If hook fails, investigate Wine cross-desktop SetWindowsHookEx and bitness instead of guessing fonts again.
- User also asked earlier for a more Touhou-specific launcher icon; no icon changes in v5, focus remains Japanese rendering.
- Architecture remains **Winlator-derived** (Wine/Box64/Winlator XServer and controls beneath Touhou launcher). Be transparent.


### Verified Android APK artifact for targeted installer-thread font repair (Oct 22, 2026)
- GitHub Actions **completed/success** run https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39852815210 at source commit `257f98d49c89cac1d9828dea24e438a984bdef57`, `touhou-pocket-runtime-preview-apk` artifact ID `12459025794`. APK extracted to `/mnt/data/TouhouPocketLauncher-Installer-Font-Hook.apk`; size `231971812` bytes, SHA256 `1babe0104e3a7acd2741712f39aae1c48c3c2128178e12587c3baf18e9b36938`; both GitHub artifact ZIP and APK passed CRC verification.
- The APK contains `assets/japanese/touhou_probe.exe` v5 (314907 bytes), `touhou_font_helper32.exe` (241945 bytes), `touhou_font_helper64.exe` (256053), `touhou_font_hook32.dll` (220448), and `touhou_font_hook64.dll` (224846). Both IPA and Noto license notices present; 35 native Android shared objects.
- **NOT YET ON-DEVICE VALIDATED.** Do not claim the original Japanese path now renders correctly; Wine might reject thread-specific hook, desktop switch, or PE bitness. User must install over previous `com.touhoudr` without uninstalling/clearing data (Android debug signature may differ; protect imported games/saves).
- Exact device test: launch original `setup.exe`, go to default destination field `C:\\game\\FocasLens\\幻想人形演舞` previously showing squares, keep open ~25 sec, observe whether kanji appear; then back to Touhou launcher > View Last Launch Diagnostics > Copy Report. Look for `touhou-probe-v5`, `font-fix: launched in-process helper`, `helper-v1: thread-specific hook installed`, and `hook-v1: SUCCESS applied IPAPGothic...`. If hook fails, use error logged to choose next fix rather than another blind font swap.


## 2026-10-22 confirmed font hook success, latency follow-up

User ran the in-process (thread-specific WH_GETMESSAGE) Japanese font hook APK and explicitly confirmed: **"It works but the blocks were delayed in changing to the right characters."** This is the first confirmed working Japanese rendering fix! User report:
- `touhou-probe-v5 GetACP=932`, original path still `C:\\game\\FocasLens\\幻想人形演舞`.
- `font-fix: launched in-process helper (32bit=1,targetThread=232)`
- `helper-v1: selected Wine nogui desktop`
- `helper-v1: thread-specific hook installed; waking installer thread`
- `hook-v1: callback executing within installer GUI thread`
- `hook-v1: target TEdit found in original installer thread`
- `hook-v1: SUCCESS applied IPAPGothic to path edit; original Unicode destination unchanged`.
Thus the actual font fix works, original Japanese path is preserved, and installing additional fonts or rewriting path is not needed. Remaining issue is the visible delay.

### Startup-timing optimization on main
- Commit `58c94e67e8d1f7acd1d270d67daf28c7a2179c31`: `runtime-preview/overlay.py` starts the Wine font monitor **750ms after EXE process launch instead of 9000ms**. Scope remains original `setup.exe`; no other game/installer changes.
- Commit `7ca9660030959bce26f20a2b35022521326bc8e3`: `runtime-preview/touhou_probe.c` v6 polls original path TEdit every **300ms** for first ~minute, then **850ms** for several more minutes (previously every 2000ms for only 60 sec). Allows user to navigate installer while hook is ready, minimizing visible block delay. Suppresses repetitive desktop logs. In-process bitness-matched font helper/hook unchanged.
- Latest workflow run at time of writing: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39859088115 . Check **completed/success** and collect artifact before delivering an APK; latest run 39859012781 for first commit was auto-canceled by workflow concurrency.
- Preserve package ID `com.touhoudr`, original path, single installer entry, legitimate user-owned games. Debug APK signatures may differ; never instruct uninstall/clear data with imported files.
- Ask user to check that Japanese destination displays correctly without waiting several seconds in the new APK and report delay, if any. If still slow, profile Windows Wine side process creation/WM_GETMESSAGE wakeup rather than tinkering with working font registration. Continue focus on rendering latency until satisfied.
- Reminder: app still uses Winlator-derived Wine/Box64 display/backend; no false claims of fully independent backend. More Touhou-themed launcher icon is an outstanding separate request.


### Verified low-latency Japanese font hook APK — 2026-10-22
- User's on-device v5 report showed **successful IPAPGothic hook**, unchanged Japanese path and delayed switch from blocks to correct glyphs. This is a confirmed functional fix; only latency remains.
- Source changes (main): `runtime-preview/overlay.py` moves helper startup from `Thread.sleep(9000)` to `Thread.sleep(750)`; `runtime-preview/touhou_probe.c` v6 polls every 300ms during first minute and 850ms subsequently, monitoring for up to ~4 minutes, while preserving original path. Hook DLL/font registry and 32-bit installer behavior unchanged.
- GitHub Actions **success**: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39859088115 at commit `7ca9660030959bce26f20a2b35022521326bc8e3`; artifact `touhou-pocket-runtime-preview-apk` ID `12461321643`.
- Verified APK local path `/mnt/data/TouhouPocketLauncher-Japanese-Font-Faster-Startup.apk`, 231,971,672 bytes, SHA256 `50f50640c88ef3a2a50dd8c2bd40390f2d6c6eddbdac5dfb1b93c5ee97f0df73`; APK ZIP CRC passes. Includes `touhou-probe-v6`, four 32/64 bit font hook/helper assets, Japanese font addon and font license notices.
- **Not verified yet on Galaxy after timing changes.** Ask user to update app *without uninstalling/clearing user data*, reopen original setup.exe and check whether original Japanese folder now displays correctly much sooner. If still visible delay, check v6 diagnostics / hook-v1 log; profile Wine EXE process spawn and in-process hook response. Avoid repeating font substitutions because font repair is known working.


## 2026-10-22 — Touhou OS rebrand, mobile dashboard, automatic engine setup

User confirmed the prior Japanese destination font hook **works well now**. Preserve that known-good Wine/Box64 engine and fast startup monitor. New project direction: rename the branded app to **Touhou OS**, redesign the launcher, and make `Set Up Game Engine` an **automatic first-launch process** rather than a routine manual action. Do NOT change the internal Android package `com.touhoudr` (must preserve access to previously imported games/saves and same-length binary path rewriting). Underlying Wine/Box64/Winlator-derived backend remains as-is and must be attributed honestly.

Changes on existing repo `main`:
- `runtime-preview/TouhouEntryActivity.java` commit `b6ea428284108354284968f420432f64085bdcf6`: redesigned native Java dashboard with shrine-red/ink-purple/sakura/gold palette, title `TOUHOU OS` / `東方 • 幻想郷`, **Library**, **Import**, **System** navigation. Library displays existing game/install cards and Play/Install; Import groups complete folder, standalone EXE, and scan installed games; System groups game engine status, compatible graphics, local diagnostics, and an explanation of setup. No changes to game paths, library data format, Wine startup/hook, dedupe or storage.
- `runtime-preview/overlay.py` commit `311b9f622b599955283b302f55f7b812a3c2cceb`: Android app label and background notification now say `Touhou OS`; Java package stays `com.winlator` internal for JNI compatibility, Android package remains `com.touhoudr`.
- `runtime-preview/TouhouEntryActivity.java` commit `9e1b811871f3f4dba3a5460981712daec0381e82`: in `onCreate`, after UI render and ready-state check, `initializeEngineOnFirstLaunch()` calls existing `startSetup()` only when `RootFS` missing/old or no game container. Existing roots and containers skip setup; during automatic setup show status, hide manual button, disable play/import until ready; manual **Retry Game Engine Setup** appears only when initialization fails. Existing setup logic extracts bundled rootfs and creates a game environment with correct graphics/audio; no games or translations are downloaded.
- `runtime-preview/touhou_pocket_icon.xml` commit `8c24dfd05e88a68330843b00dd08592e1549a139`: replaced handheld-console motif with original Touhou-inspired moonlit torii, yin-yang, cherry petals and shrine colors; retains resource filename to avoid breaking overlay.
- `runtime-preview/NOTICE.md` commit `f048157563efc4b746f3ddd7e2592aeebf56f955`: changed launcher name and clarified derivative LGPL Winlator runtime and automatic setup.

Important to validate latest GitHub Actions build (workflow `.github/workflows/runtime-preview.yml`, fetch latest run by SHA `f0481575`, early run ID `39864023604`; older commit builds cancel automatically). Inspect full compilation errors and fix if needed, then download / verify APK. First-run automatic extraction should be tested on a clean install only when data safety permits; user has imported files/saves, so should update the existing app without uninstalling/clearing data, and confirm normal ready-state skips initialization. Must never casually recommend uninstalling app as that may erase its private Wine prefix and game files.


## Touhou OS APK verified — Oct 22 2026 (successful CI after MinGW timeout fix)
- Build workflow run https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39865725869, Git source SHA `13d1809574e2bfad2da20b964a671cb6f2ff5fdc`, status **completed / success**. Artifact `touhou-pocket-runtime-preview-apk` ID `12463852428`. Source includes Touhou OS UI (Library / Import / System), automatic first-launch setup, Touhou OS label/notifications, moonlit shrine vector icon, and existing fast Japanese path-font hook.
- Downloaded, extracted, and verified APK: `/mnt/data/Touhou-OS-Android.apk` (231,975,728 bytes), SHA256 `c1d93c1ac8639521b4eb3dd82b37543b4c2a815cbfd5a12a382ab41fe98ce858`. ZIP CRC passed, 35 JNI shared libs, all Japanese assets, IPA/Noto and Winlator license notices, 32/64-bit font hook DLLs and helpers bundled.
- Binary package sanity: Android resources include `Touhou OS` label, old `Touhou Pocket Launcher` label is absent; compiled manifest retains Android package `com.touhoudr` for in-place upgrade/data continuity.
- Earlier run `39864023604` stalled on MinGW build dependencies. Commit `13d1809574e2bfad2da20b964a671cb6f2ff5fdc` capped apt-get update/install time and checks for existing compilers; new run successfully built full APK.
- **Not yet physically tested on the user's Galaxy**: UI responsive navigation, automatic engine setup path (new installs), engine reuse (existing installs), icon visual quality, font timing, library install/play. Avoid claiming phone tested. Recommend install **over existing app without uninstalling or clearing data**; test Library/Import/System, Japanese install directory exact default, imported titles, graphics toggle, startup diagnostics. If Android update rejected due to signing, ask before doing anything that could erase user data.
- Current implementation remains a *Touhou OS branded fork of Winlator* with Wine/Box64 backend, not a wholly independent engine. License attribution remains mandatory; complete runtime rewrite is future work only.


## 2026-10-22 — Touhou OS rebrand, UI redesign, automatic first-launch engine, successful APK

**User-confirmed prior success:** The rapid Japanese installer font helper fixed the original Windows TPDP installation path's boxes. User explicitly said "Works well now." This must remain working and original path `C:\\game\\FocasLens\\幻想人形演舞` must not be overridden. The fast font monitor (roughly 750ms initial start; roughly 300ms polling) is retained unchanged.

**Name and architecture:** App user-facing name is now **Touhou OS**, Charoite Games. It is *not* an Android OS replacement; it is a dedicated Android Touhou launcher. Android package `com.touhoudr` is deliberately unchanged to preserve in-place upgrades and app data. The compatibility/runtime backend is **still a modified, LGPL-licensed Winlator source** with Wine and Box64; do not claim the codebase is independent of Winlator. Licensing/attribution retained.

**New UI in `runtime-preview/TouhouEntryActivity.java`:**
- Shrine-red/ink-purple/sakura mobile dashboard; Touhou OS hero heading and Japanese Gensokyo label.
- Three sections: **Library** (existing game/installer cards and Play/Install actions), **Import** (complete game-folder picker, single-file EXE picker, scan previously installed games), and **System** (engine state, optional retry, compat graphics, last launch diagnostics, "What does setup do?" explainer).
- The previous cluttered setup/import/debug button list is replaced by sections. New vector Android icon `runtime-preview/touhou_pocket_icon.xml` is Touhou-inspired moonlit shrine and yin-yang, without the handheld console. Installed application label, runtime notification branding updated to **Touhou OS**.
- Existing library preferences, single installer slot, import data, game saves and original Wine prefix unchanged.

**Automatic engine initialization:**
- On activity creation the launcher checks `RootFS.find(...)`, `RootFSInstaller.LATEST_VERSION` and active container. If already ready, it opens directly into Library and **does not reinstall**. If runtime missing/outdated or no container exists, it opens System and calls `startSetup()` automatically.
- Setup extracts the bundled rootfs only if needed and creates the game environment (Wine/Box64, compatible graphics/audio settings). No game download, translation, installer path overrides or automatic game installation.
- Manual engine setup hidden when ready or busy; shown as **Retry Game Engine Setup** if engine is not ready after a failure. The System explainer describes first-launch behavior.
- Important unresolved QA: test fresh install and in-place update on Android; ensure automatic setup does not touch existing imported game data or break callback/UI states.

**Latest successful build:** GitHub Actions https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39865725869 , workflow `.github/workflows/runtime-preview.yml`, code commit `13d1809574e2bfad2da20b964a671cb6f2ff5fdc`, **completed successfully**. An earlier run `39864023604` stalled at the MinGW dependency step and was cancelled when the new run started; compilation step now checks tool availability, bounds apt-update/install time. No need to chase cancelled run.
- APK artifact ID `12463852428` name `touhou-pocket-runtime-preview-apk`.
- Legal artifact ID `12464041905` name `touhou-pocket-runtime-legal`.
- Verified APK from successful build: `Touhou-OS-Android.apk`, **231,975,728 bytes**, SHA256 **`c1d93c1ac8639521b4eb3dd82b37543b4c2a815cbfd5a12a382ab41fe98ce858`**. Archive CRC valid, bundled Japanese support `japanese-support.tzst` (22,309,132 bytes), `touhou_probe.exe` (v6), 32-bit/64-bit matched Wine font helper EXEs and hook DLLs, 35 native libraries and LGPL license. Output accessible in current chat working container at `/mnt/data/Touhou-OS-Android.apk`.
- The GitHub **build** passed, but the redesigned UI and first-run flow **have not yet been user-tested on device**. Do not claim verified functionality on Galaxy until user reports test.

**Installation/testing:** Install the APK over current Touhou Pocket Launcher without uninstalling or clearing data. Because Android app ID remains `com.touhoudr`, current game data is intended to remain available, but OS signature acceptance must still be checked. Open Touhou OS: existing installed engine should display Library without setup or data loss. Verify imported game(s) and installer still listed, Japanese original default installer destination instantly renders `幻想人形演舞`, System works, Import works, and first-launch auto setup on a separate clean install/device when possible. No forced `/DIR` / ASCII path. Do not ask user to uninstall existing app to test from scratch.

**Development workflow:** ChatGPT directly modifies GitHub `rgarn023/TouhouPocketLauncher` on **main** using connector tools under `mcp__GitHub__` accessed through `functions.exec`. Do not recommend other coding agents. Changes under `runtime-preview/**` or runtime workflow trigger GitHub Actions; `docs/HANDOFF.md` edits alone do not. Future improvements: refine touch UI/device QA, ensure launch resume and game selection are stable, expand Shard of Dreams/Extended support later. UI remains customized Winlator-derived Wine/Box64 stack; own completely independent runtime would be a separate major project.

## Oct 22, 2026 — Library/Setup separation and installer handoff

User requested Library contain **only playable games**, and former **Import** tab become **Setup** to select a game folder/installer and handle installation. Source commit `ad9440afc76fc107ab74b7f60c24f897f88e648a` changes only `runtime-preview/TouhouEntryActivity.java`:
- Three tabs: **Library / Setup / System**. Installer entry remains safely stored in existing `game_library` preferences but does **not** render in Library. No existing imported files, installer paths, Wine prefix or saves were deleted/migrated.
- Setup offers complete game/installer folder, standalone .exe, and installed-game scanning. Selecting an installer now **automatically launches the original Windows installation GUI** after copying required files. A **Current Installer / Run Installer Again** card remains under Setup. A directly playable game folder is added to Library without invoking an installer.
- After the Windows installer closes and Touhou OS resumes, it automatically scans the container's C drive for supported executable names (`gn_enbu.exe`, `enbu_ap.exe`, named `thNN.exe`); discovered games appear in Library. The user still must complete any original Windows wizard prompts; never override its Japanese installation directory. Manual re-scan remains in Setup.
- Physical C drive under Android: `/data/user/0/com.touhoudr/files/rootfs/home/xuser-<container ID>/.wine/drive_c/` (equivalent `/data/data/com.touhoudr/files/...`; ID is selected container). Import staging stays under `C:\\TouhouPocket\\game-<timestamp>`. User's original installer destination remains `C:\\game\\FocasLens\\幻想人形演舞`.
- Visible mouse pointer is normal for the original Windows installer, rendered within bundled Wine/Box64 and Winlator-derived `XServerDisplayActivity`, where cursor visibility is turned on when a Windows window appears. Touhou OS does not delegate to another separately installed app. Touch/gameplay cursor redesign is future work; do not hide installer controls prematurely.
- Workflow: `.github/workflows/runtime-preview.yml`, auto-triggered by push to `main`. **Verify its final build status and artifact before offering the updated APK**. On-device correctness still unverified. Do not uninstall or clear app data.


### Verified new UI build and Android signing blocker
- UI commit `ad9440afc76fc107ab74b7f60c24f897f88e648a` passed workflow run `39880357298`: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39880357298 .
- APK artifact ID `12469993976` (`touhou-pocket-runtime-preview-apk`). Extracted `app-debug.apk` is **231,976,660 bytes**, SHA256 `256967d7733ba77781c05a9636db2d1019da0435f451f9c88aaac06d2e8984d0`. ZIP CRC and 35 JNI libraries verified; Japanese font hook assets present. On-device behavior not verified.
- **CRITICAL UPGRADE BLOCKER:** Examined Android APK Signing Block v2 certificate DER hashes. Prior working Touhou OS APK (workflow 39865725869, artifact 12463852428) signer SHA256 `e1674b954e91ebe83cd5631e177dc269bbd8a49d8c5d239bfa7dad3ea7f22d0d`. New UI build signer SHA256 `b0c84f96fd77ac8c18377d04fe1c2913fa26785a0b09d613014a78e842cdc7b4`. Android **will reject upgrade** across these signing identities, despite unchanged `com.touhoudr`. Existing debug key from prior workflow was not available in the new CI build. Do not suggest uninstalling/replacing existing app or clearing data: imported games/saves may be lost. Need develop a non-destructive testing or data migration plan, or recover the actual original signing key if available. A new stable signing key alone will not upgrade a previously installed different-signature APK.


## Oct 22, 2026 evening — Galaxy-inspired launcher + APK-triggered engine refresh

**User clarification:** The user has not been installing or saving games yet. They want the game engine to install/refresh **automatically whenever Touhou OS APK is installed or upgraded**, and want the native app UI to feel more like a modern Samsung Galaxy/One UI interface.

Source commits on existing `main`:
- `02b109762813df3c37feee80f035d94eb1fc7baa`: redesign `runtime-preview/TouhouEntryActivity.java` with a Samsung One UI-inspired, original Touhou OS presentation. Large header, readable One UI-like typography, responsive padded cards and curved surfaces, fixed bottom navigation tabs `Library / Setup / System`, 54+ dp touch targets, dark/light palette matching Android device preference, lilac/pink Touhou color accents. No Samsung assets or trademarks are copied into the UI.
- `eb452d588511f799682183a6809dc587457b1723`: engine refresh now checks Android `PackageInfo.lastUpdateTime` against a successfully prepared APK marker in local preferences. On every new APK install/update, Touhou OS automatically re-extracts the bundled `rootfs.tzst` to update Wine/Box64 environment components even if upstream RootFSInstaller version stays the same. Removes stale cached Box64 version marker to allow engine runtime reconciliation. On subsequent launches of the same APK with a valid container, setup is skipped. Marker is recorded only once a valid existing/new container is identified. On setup failure it is left stale so the next launch retries automatically (manual Retry remains under System when not ready).
- Preserve imported games/saves and Wine prefix: the pinned `rootfs.tzst` archive contains `./home/` directory entry but no files below it; no container deletion or re-creation on update. Existing `home/xuser-N/.wine/drive_c` remains intact. Never assume this remains true if changing pinned upstream: verify archive before updating upstream build.
- Library only shows playable game entries. Setup stores/re-runs the imported Windows installer and automatically searches for games after its original installer wizard is closed.
- **Signing caveat:** GitHub Actions currently builds a debug-signed APK; consistent Android in-place upgrades require the same signing certificate across builds. Auto-refresh logic runs once an APK can be installed or updated, but it cannot bypass Android's signature verification. User says no valuable installed game data yet, but do not tell them to delete data without explicitly ensuring backups if circumstances change. Set up secure persistent signing for long-term updates.
- **Latest workflow:** check run for code commit `eb452d588511f799682183a6809dc587457b1723`; never offer the new APK until GitHub Actions build has succeeded and APK artifact is verified. On-device Galaxy UI and engine upgrade remain untested.

### Successful Galaxy-style Touhou OS APK — 2026-10-22

GitHub Actions completed **success**: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39889854340, build source SHA `726e92d2aca7f2cddc197fce1e1d958a3ba14a0a`. APK artifact name `touhou-pocket-runtime-preview-apk`, artifact ID `12474566719`; legal/source artifact ID `12473804653`. Extracted APK `Touhou-OS-Galaxy-Edition.apk` is **231,978,204 bytes**, SHA-256 `94b81084634b9cd5eb637b349cf600ae0cf048901965036a0924628e48acea4e`. Both downloaded artifact ZIP and extracted APK passed ZIP integrity verification, includes 35 native JNI libraries and both architectures of Japanese installer font hook/helper assets. New CI change `726e92d2aca7f2cddc197fce1e1d958a3ba14a0a` caches Windows Japanese font helpers by source hash and installs narrow MinGW win32 packages, fixing prior run `39888584953` which had timed out on apt. This new build has **not been tested on user's Galaxy yet**, so do not claim installed or running.

Installation caveat: because GitHub Actions builds debug-signed APKs and may generate a new signing cert per runner, Android upgrade may require uninstalling an older debug APK. User currently states no games have been installed or saved; nevertheless uninstall erases internal Wine containers, imported installers, and future saved games. Long-term secure persistent signing key must be configured for seamless in-place upgrades.

## Touhou OS Galaxy Library UI refinement — October 22/23 2026

User explicitly requested: remove **Set Up a Game** button from Library; leave only a note directing users to Setup. Remove the **game engine info** display and explanation. Permit rearranging installed game icons freely on the Library page, with positions saved across app restarts.

Code commit `99fa1566a73a6ae363a4d5ebbfe27e16add93b63` on existing `main` updates only `runtime-preview/TouhouEntryActivity.java`:
- Library no longer has a Setup shortcut button. A note reads “To install a game, open the Setup tab below.”
- Top engine strip removed; engine status, and retry only when needed, remain on **System**. Removed the “What does game engine setup do?” explanatory button and its dialog. `statusText` now refers to the System runtime label, preserving existing diagnostics/status calls.
- Library presents playable games as a native Android `GridLayout` of three columns on phones (four if screen width at least 600 dp). Each has a rounded colored original vector-like letter tile and a truncated title. Tap to launch (when installed/ready); long-press then drag-and-drop on another tile to rearrange; drag between tiles to move to last position.
- Drag target highlights; reordered game records persist in the existing `game_library` preference via a synchronously committed JSON array reorder. **Only entry order changes**: no file, path, EXE, installer entry, saves or Wine prefix is renamed, moved, cleared, or removed. Reopening Library reproduces the new order. Installers never appear as Library icons.
- This implementation uses generated text glyph/color icons (not real extracted Windows executable icons or artwork). Icon display/drag correctness requires physical Galaxy testing; future optional enhancements could extract EXE icons and support folder/grid edit mode.
- Existing Winlator-derived backend, Android application ID `com.touhoudr`, APK-triggered engine refresh, TPDP original Japanese installation path and scoped IPAPGothic Windows font fix untouched.
- GitHub Actions run for `99fa1566`: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39893224437 ; verify successful completion and APK artifact before distributing new APK. GitHub CI debug key signing may not match earlier installed build; never casually uninstall an app containing user games/saves.

### Verified APK — draggable game icons

- GitHub Actions **success**: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39893443118, source SHA `c1df3f93da8343274deb18131df0e43fa59047a3` (fixes Android `LinearLayout.setMinHeight` compile error to `setMinimumHeight`).
- Artifact `touhou-pocket-runtime-preview-apk` ID `12475916999` contains `app-debug.apk`, extracted as `Touhou-OS-Game-Library-Update.apk` (231,979,996 bytes), SHA256 `58000d0f9a250e04d3037368475e2f52d8ef60eb4c83358e8cbb0a2ca5`. Artifact ZIP CRC and APK CRC pass; 35 JNI libraries and both architecture pairs of Japanese font hooks/helpers present.
- **Not Galaxy-tested yet**: drag/drop tile reordering, device layouts, light/dark mode, and actual game launch still require user device validation. No installed game files or saves changed by GitHub source edits. New app APK may be signed with different temporary debug key than previously installed; require Android signature match for an in-place update. Do not uninstall without confirming user has no irreplaceable private data.


## Samsung DeX desktop / external-monitor support — Oct 23, 2026

**User request:** Make Touhou OS work in Samsung DeX with resizable window UI, external mouse/keyboard and monitor-adapted game resolution. Continue `main` only. Preserve Japanese game compatibility and mobile behavior.

**Implementation committed:**
- `5ed0e4b6c2ef86354aa9ab2fbd976fecd79e2899`, `runtime-preview/TouhouEntryActivity.java`:
  - On Android configuration changes (size, orientation, dark mode), re-render native launcher WITHOUT recreating the activity/import worker or resetting active Library/Setup/System tab. Launcher content max width ~940dp centered on desktop, three-column game tiles on phones and four columns for width >=600dp.
  - Detect external display via `Display.getDisplayId() != DEFAULT_DISPLAY` or multi-window via `isInMultiWindowMode()` (not a Samsung-private API). New System card **External display & DeX**, auto/preset Wine resolution choices `1280x720`, `1600x900`, `1920x1080`, `800x600`. Auto defaults to `1280x720` on phone, uses 1600x900 or 1920x1080 based on current desktop window bounds when large enough, and honors compatibility graphics 800x600.
  - Free DeX pointer by default; toggle **DEX MOUSE: CAPTURE IN GAME** for apps needing relative mouse control. Regular phone launch preserves existing Winlator pointer capture preference.
  - On game launch pass intent extras `touhou_desktop_window`, `touhou_display_size`, `touhou_pointer_capture`. Do NOT overwrite `container.screenSize` or make irreversible Wine prefix changes when switching displays.
- `071ca8ffd7dbf53bd6d9f46ca64683aed6f55c06`, `runtime-preview/overlay.py`:
  - Set Android application, Touhou entry activity, and XServer activity resizeable. Launcher `configChanges` includes desktop window dimensions, orientation, keyboard changes, density, and `uiMode`. Remove manifest forced landscape from XServer; request sensor-landscape at runtime on phone, keep XServer unrestricted in external/DeX windows.
  - For external desktop sessions do not call immersive `AppUtils.hideSystemUI`, leaving DeX window decorations in place.
  - Inject per-session XServer `screenInfo = resolveScreenInfo(requested)` for trusted specific resolutions from intent and override `capturePointerOnExternalMouse` from intent; existing Winlator `dispatchKeyEvent` and `dispatchGenericMotionEvent` continue handling keyboard and mouse.
- Desktop resizing can scale an already running GL display. The internal Windows X screen resolution is selected **when the game launches**; to pick a new guest resolution after resizing, relaunch game. No hot virtual desktop resolution switching has been implemented.
- Do not claim fully tested DeX compatibility without actual S26 Ultra + external monitor verification. Also no physical validation yet of all input paths or resizable Wine graphics.
- Build workflow run for `071ca8ff`: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39941688879 . Confirm success, artifact and extracted APK integrity before handing out.


### Verified DeX APK artifact (2026-10-23)

GitHub Actions run **39941688879** completed **success**; code build SHA `071ca8ffd7dbf53bd6d9f46ca64683aed6f55c06`. The working `main` branch also includes this documentation update. APK artifact `touhou-pocket-runtime-preview-apk`, ID `12495829292`, checksum for artifact ZIP as reported by GitHub `sha256:442560e9b7bf452dfae3c61ba4acd9f8d03e5ed2e6cca9eeaf7fbdd42136ccc6`.
- The one-file ZIP artifact contained `app-debug.apk`, extracted to `/mnt/data/Touhou-OS-DeX-Edition.apk` for sharing. APK size **231,982,272 bytes**, SHA-256 `0651c9659d743d646d9ee7b3ec1d6c860aeb7493de6ff7b4b099082d79d62803`. Both archive ZIP and extracted APK passed CRC integrity checks; 35 native JNI libraries present; Japanese probe, 32- and 64-bit font hooks and helpers included.
- Resizable-window, pointer-capture, and virtual-resolution code compiled successfully. **No external Samsung DeX hardware testing has occurred**; physical mouse/keyboard routing, DeX window resizing, graphics scaling and launching Japanese game installers in desktop mode need device confirmation.
- App ID remains `com.touhoudr`. Temporary GitHub Actions debug APK signatures can differ between workflow builds, so Android might reject an in-place upgrade due to signature mismatch. Never recommend uninstalling if user has irreplaceable app-private game files/saves without backup.


## Oct 23, 2026 — Touhou Launcher + Charoite Core v0.1 implemented

**User's latest agreed roadmap:** Do NOT create/replace Android/One UI with Charoite OS. Rename Touhou OS to **Touhou Launcher for Android** and develop reusable **Charoite Core** alongside it, starting from existing Wine/Box64 functionality in the same repo and Android APK. The user then said "Let's continue," so these changes have now been directly implemented and built on existing `main`.

**Source changes:**
- `23d5b0fd94132f3c7a16da6b868fbc16df07de68`: created `runtime-preview/charoite-core/CharoiteCore.java` in package `com.charoitegames.core`. Shared runtime API `VERSION=0.1`: `getDisplayModeIndex`, `setDisplayMode`, `isDesktopWindow`, `automaticGameResolution`, `chosenGameResolution`, `isDesktopPointerCaptured`, `setDesktopPointerCaptured`, `shouldCapturePointer`, `installedApkTimestamp`, `engineRefreshRequired`, `markEnginePrepared`, `prepareBundledEngine`, `applyGraphicsProfile`, `createContainerProfile`. Preserves existing activity-pref key names and private paths.
- `0742c57ac8426b3d8cd974fe927d7be3142c6345`: `runtime-preview/TouhouEntryActivity.java` now uses CharoiteCore for actual engine extraction/refresh, graphics profile, new container defaults, DeX resolution/mouse prefs and game launch. UI title now `Touhou Launcher`, tagline `For Android • Powered by Charoite Core`, System footer shows core version. Existing Library, Setup, game files, Japanese font hook and DeX interface preserved. The former `Touhou OS` text replaced. **Do not rename `C:\TouhouPocket\` staging path**: it is user storage, not a product label.
- `9635c3895a8d5d9b89fa83343c10f0a52f919a3b`: `runtime-preview/overlay.py` now explicitly copies core source into the pinned Winlator Android Java tree and sets app label `Touhou Launcher`. Keeps `com.touhoudr` package ID and upstream LGPL notices.
- `010b08865132212c4dc239880408f422ace43389`: changes remaining launch-failure dialogs from `Touhou Pocket` to `Touhou Launcher`.
- `f9337fc5a61c43085cee4279592d076901126a37`: `runtime-preview/charoite-core/README.md` documents API, integration, architecture, legal boundaries and preservation contract.
- `eb4cb85f77952310ea43d3da2fe86c37909a0123`: project README updated to accurately describe current install workflow, DeX, package ID, data-preservation caveat, compiled Core module and tested/untested scope.
- `a59489e9f4bf034ede49eb1ea2d43cb98764262b`: `runtime-preview/NOTICE.md` preserves attribution and describes the Core layer, without claiming a custom Wine fork.

**Successful build / APK:**
- GitHub Actions run **39946264062** https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39946264062 finished `completed/success` for build code commit **`a59489e9f4bf034ede49eb1ea2d43cb98764262b`**.
- APK artifact: `touhou-pocket-runtime-preview-apk`, ID **12498930298**, artifact ZIP SHA256 `3467bc41ffc37f1d00200753ffc0e93bb5ee4d52cdb47e3ab352ea6059fba85e`.
- Downloaded/extracted `app-debug.apk` to **`/mnt/data/Touhou-Launcher-Charoite-Core-Android.apk`**, size **231,982,928 bytes**, SHA-256 **`6fc09e0c1af99334a7709a648fd1c2eb7bd7d1eae045f27dc0e0f946763066a8`**.
- ZIP/APK passed CRC integrity tests; 990 APK entries, 35 JNI shared libraries, `classes.dex` has `com/charoitegames/core/CharoiteCore`, `Touhou Launcher`, `Charoite Core`; Japanese `touhou_probe.exe`, `touhou_font_hook32.dll`, `touhou_font_hook64.dll`, `touhou_font_helper32.exe`, `touhou_font_helper64.exe` all present. This is genuine compiled integration, not just docs.
- **Still not tested on physical Galaxy after integration**, so Android UI/gameplay/DeX behavior need validation. **Debug CI signing** might differ between installed builds; Android may reject in-place upgrade. Never suggest uninstalling an app containing valuable game files or saves without backup. Same Android ID `com.touhoudr` and preserved storage policies.

**Next suggested work:** verify install/gameplay on Galaxy with Touhou Puppet Dance Performance; then add Charoite Core regression tests for display profiles and APK-upgrade safety, develop persistent APK release signing, and extract further *genuinely reusable* runtime services (not game-specific UI) without breaking the Japanese installer or Wine compatibility. A separate `CharoiteCore` repo/SDK is NOT yet built or needed.


## 2026-10-23 — Galaxy bottom navigation + Charoite Core Wallpaper

**User provided Galaxy launcher screenshot** showing bottom Library/Setup/System tabs too low near Android navigation. User asked to move tabs up a little and add System settings to choose a saved phone image as app wallpaper, with fit or crop options. During implementation user explicitly asked whether the wallpaper function will be part of Charoite Core. **Confirmed yes** for reusable wallpaper storage/fit/crop policy, while the native Touhou Launcher owns picker and UI.

Changes on existing `main`:
- `b5c2480537d227b82862c20bf2f4446a6e172ee2` / `a2036ec07e11a0c8009da4c3c24b79310bcaa9db`: `runtime-preview/TouhouEntryActivity.java`: 14dp higher navigation buttons by increasing nav height 74→88dp and bottom padding 7→21dp; full-screen wallpaper layer behind transparent scroll content with a semiopaque theme-tinted readability overlay; System card **Launcher wallpaper** with Choose Image From Phone, preview, **Crop to Fill** or **Fit Whole Image**, Remove. `ACTION_OPEN_DOCUMENT` with `image/*`, ActivityResult import, toast confirmation or error. Wallpaper is separate from Samsung system wallpaper and Wine game output.
- `c8a008116dda4bb0f806f3eab37d323c75e4c92a` / `5e96f0272692ae70c31b8caca1a47a37f00e17e0`: added `runtime-preview/charoite-core/CharoiteWallpaper.java` (reusable Android module). Safely copies image at most 50MiB to app-private temporary file, checks source type and image decoding, atomically replaces previous image; bitmap downsampling to avoid RAM pressure; persists fit/crop preference in existing Activity prefs; removal does not touch source photo. Core has no launcher UI and does not change One UI.
- `cfd18da67a359b1b2c99072faafa404f4773102c`: overlay copies new Core class to packaged Winlator-derived Android source tree, with original Wine/Box64 and Japanese installer components unchanged.
- `66d8e7fe8101838634a8f1edc55c31b2d7f2aaf9`: Core README updated with wallpaper API and test details.

**Verified build:** GitHub Actions [39948092801](https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39948092801), code SHA `a2036ec07e11a0c8009da4c3c24b79310bcaa9db`, completed **success**. APK artifact `touhou-pocket-runtime-preview-apk`, ID `12499890025`, downloaded to `/mnt/data/Touhou-Launcher-Wallpaper-Galaxy-Build.zip`; extracted APK `/mnt/data/Touhou-Launcher-Galaxy-Wallpaper-Update.apk`, **231,986,364 bytes**, SHA-256 **`b702c5be1b62bf529934acbb5abd322d1df41faf9f729cc89120bfd9d7886502`**. ZIP and APK CRC tests succeeded; 35 JNI libraries; DEX includes `CharoiteWallpaper`, Fit/Crop, `CharoiteCore`, wallpaper picker strings; Japanese font diagnostic EXE, 32/64-bit hook DLLs and helper EXEs present.

**Caveats:** No physical Galaxy or DeX wallpaper rendering/URI chooser testing yet. Android in-place upgrades may fail due to ephemeral GitHub Actions debug signing certificate. Do not uninstall an app with important private games/saves without a backup. App ID remains `com.touhoudr`, Wine container paths and installation behavior unchanged. Do not confuse app-private wallpaper with OS wallpaper. Future custom crop-position/zoom gesture controls are not implemented; current Crop scales to fill and automatically trims edges.


## Oct 23, 2026 — Wallpaper label & connected page tabs

User corrected prior assistant's mistaken GitHub-access claim: **GitHub connector IS available via `functions.exec`, `tools.mcp__GitHub__*`**. Continue developing directly, no third-party coding-agent prompts.

User requested: (1) System card title **Wallpaper** (not “Launcher wallpaper”); (2) Library, Setup, System bottom tabs should resemble connected **page/file tabs**, not separate rounded floating buttons; (3) asked “Has the core been updated as well?”

Changes to `runtime-preview/TouhouEntryActivity.java` on existing `main`:
- `a936cca4f97f5bc5ee7ffbf1763767fa560d8a33`: Wallpaper heading / visible success-removal messages renamed. Bottom nav now three *attached*, same-width page tabs with rounded **top** corners and **flat bottoms**, selected tab slightly raised (no independent pill shadows) using `GradientDrawable`; uses simple Library/Setup/System names and selected accent colors. Touch sizes preserved.
- `c0cb8f97d1d23e1b8bcf93cba29604aef7762f5a`: retained 88dp bottom-nav height and 21dp bottom padding, keeping tabs raised above Android's navigation bar.
- **Charoite Core source was intentionally NOT changed** for the above purely launcher-specific UI work. Already-integrated `CharoiteWallpaper.java` is the shared image-storage + Fit/Crop engine and stays packaged in the APK with `CharoiteCore.java`; Wine/Box64, C: drive and installed games untouched.

**Verified build:** GitHub Actions run https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39951145792 succeeded (source SHA `c0cb8f97d1d23e1b8bcf93cba29604aef7762f5a`). Artifact `touhou-pocket-runtime-preview-apk` ID **12500592042**, downloaded as `/mnt/data/Touhou-Launcher-Page-Tabs-Artifact.zip`; extracted APK `/mnt/data/Touhou-Launcher-Page-Tabs-Android.apk`, size **231,986,504 bytes**, SHA256 `5718430786a16792ee443b3b7a8fda7174fcebf1fb1eb888378d517ef6335307`. ZIP and APK CRC checks passed, 990 entries, `classes.dex` contains CharoiteCore and CharoiteWallpaper, Japanese font hooks/helpers all present. Physical Galaxy UI still requires verification. Debug signing can block in-place upgrade; uninstall may delete private games/saves.


## October 23, 2026 — Charoite Core v0.2 shared page tabs

User explicitly requested that the connected **Library / Setup / System** page tabs belong to **Charoite Core**, not merely Touhou Launcher's UI. Implemented directly in GitHub on the existing `main` branch (no new branch).

- New reusable source: `runtime-preview/charoite-core/CharoitePageTabs.java` (`com.charoitegames.core.CharoitePageTabs`), introduced in commit `382712b423681748ac84154d7380ac875452d0b6`. This Android `LinearLayout` control owns equal-width attached page-tab buttons, flat bottom/rounded top styling, raised/selected state, dark/light theme palette, touch target sizes, accessibility descriptions, host-supplied arbitrary page names and callbacks, and 88dp bottom navigation height/21dp clearance.
- `runtime-preview/overlay.py` copies this compiled Core source into upstream Android build, commit `43f3f6bef19244a5baf97a7751837e04348590cd`.
- `runtime-preview/TouhouEntryActivity.java` now instantiates `new CharoitePageTabs(this, new String[]{"Library", "Setup", "System"}, this::showSection)`, passes palette, updates selection with `pageTabs.setSelectedIndex(section)`, and **removes old duplicated tab button and styleTab methods**; commit `43c430f537da86f402efabffe9c0411b54dfa3dd`.
- Charoite Core VERSION bumped to **0.2** (`17fdd8532e19f29169d9dd3952a2bc9190773673`). Core README updated (`d8a6687647486b8e8157b2ec3b5216e048b052b2`).
- The user's follow-up, “Is there anything unique to the Charoite core and the touhou launcher,” was answered: Core modules and Touhou-focused integration are authored here, but Wine/Box64/graphics backend remain attributed to upstream sources; no proprietary replacement engine or actual Proton integration. Auto per-game profile selection is a *future* differentiator, not implemented.

**Successful build:** GitHub Actions https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39952839692 completed SUCCESS with source head `d8a6687647486b8e8157b2ec3b5216e048b052b2`. APK artifact `touhou-pocket-runtime-preview-apk`, ID **12501865514**, downloaded ZIP `/mnt/data/Touhou-Launcher-Charoite-Core-v02-Artifact.zip`. Extracted **`/mnt/data/Touhou-Launcher-Charoite-Core-v0.2.apk`** of **231,987,256 bytes**, SHA256 **`d2226260adbd93bdd1eceb1e75a2b5f1e2e8c1653a14b71180eadcb2d4ff3499`**. ZIP and APK CRC tests passed, 990 APK members and 35 JNI libraries; packaged `classes.dex` contains `CharoitePageTabs`, `CharoiteWallpaper`, `CharoiteCore`; scoped Japanese probe and 32/64-bit font hook and helper executables included.

Existing `com.touhoudr` Android package ID, Wine/Box64 assets, rootfs/Puppet Dance Performance installer behavior, wallpaper data and game saves are unchanged. **New UI widget not yet physically validated on Galaxy/DeX**. Debug signer may differ from installed APK; don't uninstall if private game data needs preservation without a backup.


## 2026-10-23 — Charoite Portal v0.3 built; Touhou Realm migrated without moving user data

User confirmed approved rebrand: **Charoite Portal**, Windows gaming environment manager built on **Charoite Core**, with original Touhou Launcher now the first *Touhou Realm* environment. User approved a general-purpose cosmic charoite-purple *C*-shaped crystal gateway image for the new Android icon, explicitly **no Japanese/Touhou imagery in the app icon**. Their repeated request to actually implement the recommended changes (rather than generate only artwork) was completed directly on GitHub `main`.

**Successful combined APK build:** GitHub Actions run **39965865218** (<https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39965865218>), code/document commit **`db1078c4a4efcf27a002b76cbabb49e10c8699fe`**, conclusion **success**. Artifact `touhou-pocket-runtime-preview-apk` ID **12507041997**; downloaded ZIP `/mnt/data/Charoite-Portal-Core-v03-Build.zip`; extracted APK **`/mnt/data/Charoite-Portal-Core-v0.3.apk`**, **231,997,595 bytes**, SHA256 **`8e660463759e44acd465bae1da7ffccc8b192ce673aa0f69fd0bb2a8df27e296`**. ZIP/APK CRC tests passed. 990 APK members including 35 JNI libs, JPEG `res/drawable-nodpi-v4/charoite_portal_icon.jpg`, `CharoiteEnvironments`, `CharoiteThemes`, `CharoiteWallpaper`, `CharoitePageTabs`, and prior Japanese 32/64-bit font monitor components.

**Commits/features:**
- `265aba457a2a8559bb02ffe4d83fbd3202f2f2c0`: `runtime-preview/charoite-core/CharoiteEnvironments.java` Core registry. On first run registers existing Touhou as id `touhou-realm`, with original `touhou_container` or first existing container. Stores registry JSON under Activity prefs `charoite_environments_v1`, active ID `charoite_active_environment_v1`. Switch/Install preset `general-gaming`/Create named custom environment (max 20) and attach distinct Wine container IDs. Touhou's original `game_library` and `C:\TouhouPocket\` staging path are not migrated/deleted. New envs use `charoite_library_<id>` and `C:\CharoitePortal\` inside distinct prefixes.
- `665f1d9bcf53740955d3decdd9419657fbefd8b8`, `3d684c3483217ffa11c7c98256ce00fe5b34aeaa`: Android overlay compiles registry/themes and rebrands app label `Charoite Portal`, keeping Android package ID **`com.touhoudr`** to preserve data.
- `71bf8607819d499ae2e42365b2ab8ab11f68e9ef`: `CharoiteWallpaper.java` supports independent environment image files and Fit/Crop settings; existing Touhou wallpaper filename/keys preserved.
- `8b40d278db55d8c3b6f8cd87222d1d71af2ca040`: `CharoiteThemes.java` renders original sakura/petals/branch art for Touhou and cosmic ring/stars for others; default when custom wallpaper not selected.
- `42908146e0ddb890f3245cc54d6b78844c1befe5`, `ecf6d791ae5f9ce594eab99f294b6a185e45d830`: Portal header, System > Environments card with **Switch Environment**, **Install Environment** (currently only built-in offline General Gaming template), **Create Environment** (name wizard); preserve Touhou selected container and create new Wine containers as needed, context-aware UI colors and wallpaper, keep Core-owned connected page tabs.
- `8c35082940b78af12a969516591e720b7194a998`: all Library read/write/reorder/scan operations are environment-scoped; generic environment scanner accepts noninstaller Windows EXEs with bounded traversal; Touhou scanner stays Touhou-focused. Touhou staging path preserved and new environments use their own `CharoitePortal` folder in their own prefixes.
- `482af96d27dd7e8b5fc337347688b89d9d380838`, `012ada6d55a3730bee6402d919946ee7279ea4d9`: Core **v0.3**, per-environment DeX resolution, pointer and graphics preference keys; keeps old Touhou keys for upgrades.
- `fc06af8d3673848354c96190c094e6c07341098e`: selected approved non-Touhou purple crystal gateway icon JPEG (128x128 compressed home-icon asset) in repo at `runtime-preview/charoite_portal_icon.jpg`; `86ed94a4dc506b3f3e5b796b10b4c4de33841f43`, `d669d18e257a39a4ea5302bef4082bcae74e8bc1`: new icon in APK manifest and Portal hero header.
- `dcb6a1cadaba9c7575367caa1c7a7822528de5ca` and `6c3c8c8ba2308f99c3c98799990ee017fe67b68b`: scope Japanese guest locale, font setup and special installer probe to Touhou Realm; standard/general environment receives English default.
- `7b68546ee9bcaad721d1b7e268b6399088a3e2e6`, `9491e6e7f42d2d0811d06bfb926a640330b231be`, `db1078c4a4efcf27a002b76cbabb49e10c8699fe`: project README, Core README and LGPL notice updated.

**Important honest scope:** New multi-environment UI, registration/creation/selection, Core themes and new icon are source-complete and **compiled**, but have **not yet been run or visually checked on Galaxy S26 Ultra or DeX**. No online environment catalog, arbitrary importable packages, Wine compatibility autodetection, backup/export, engine version installer, or stable APK signing are implemented. Install means curated **offline built-in General Gaming** template now. Physical tests must verify Touhou migration and system panels before trusting new environments with saves. Debug signing may prevent in-place APK upgrade; never uninstall a working app with unbacked-up Wine game data or saves. All operations intentionally leave historical `com.touhoudr` package and private Wine prefixes unchanged.


## 2026-10-23 — Critical Charoite Portal Android icon repair

User reported: despite approving the purple/non-Touhou cosmic-crystal icon, the installed app displayed the **generic Android symbol**. GitHub was available and direct changes were requested.

Root-cause evidence: source `runtime-preview/charoite_portal_icon.jpg`, committed earlier via a base64 tool call, was **malformed**, with 12 repeated JPEG quantization bytes omitted at offset 108. The prior APK packaged the JPEG without actual image decoding; Pillow couldn't open the image. The earlier Android manifest also used `@drawable/charoite_portal_icon` while upstream Winlator `mipmap-anydpi-v26/ic_launcher.xml` and `ic_launcher_round.xml` were still default icon resources.

**Fix committed directly on `main`:**
- `da7183bd9bbdc39c176cfabfca95a7d7e24aabcb`: `runtime-preview/overlay.py` repairs the known, pinned damaged source JPEG by inserting exactly 12 `0x82` bytes at offset 108 and asserts the SHA256 of the now valid, user-approved original 128px JPG `28668d5426e7d7977880b6e8406c14a47972565a7f637a8c16fcd1cde2788aa5`. Build-time patched image decodes correctly; **source JPG still carries the original damaged bytes**, so always run through overlay or replace in repository with correct decoded image in future. Writes icon under `res/drawable-nodpi/charoite_portal_icon.jpg`; sets manifest `android:icon="@mipmap/ic_launcher"`, `android:roundIcon="@mipmap/ic_launcher_round"`; replaces both upstream adaptive icon XMLs in `res/mipmap-anydpi-v26`, with `res/drawable/charoite_portal_foreground.xml` (10dp inset) and `charoite_portal_background.xml` (dark charoite purple). Also creates bitmap alias resources in `mipmap-anydpi` for pre-26 fallback, though those XML files did not materialize as distinct APK entries in the modern build; older Android appearance is not verified.
- `68fe9ec7110243b0a7a2527a645480a5859996b2`: CI verifies approved image digest and modern/round adaptive icon resource packaging. `aapt dump badging` confirms **application-label:'Charoite Portal'**.

**Successful GitHub Actions run:** https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39972891688, run ID `39972891688`, conclusion `success`, code SHA `68fe9ec7110243b0a7a2527a645480a5859996b2`. APK artifact `touhou-pocket-runtime-preview-apk`, artifact ID `12509424533`, downloaded zip `/mnt/data/Charoite-Portal-Icon-Fix-Build.zip`. Extracted APK `/mnt/data/Charoite-Portal-Icon-Fixed.apk`, **231,998,725 bytes**, SHA256 **`a480c8479fb8078bfe6c7fc4a5179389f3a300a442346e38aba40164c955464b`**. ZIP & APK CRC checks passed; packaged `res/drawable-nodpi-v4/charoite_portal_icon.jpg` actually decoded through Pillow as 128×128 RGB; foreground/background XML and v26 mipmap icons present. Existing games and the Android package ID `com.touhoudr` unchanged.

**Still untested physically on Galaxy:** whether One UI now updates the home icon; launcher may cache an icon. If installed APK doesn't replace an older one because debug key changed, **do not tell user to uninstall with important private Wine saves**, back up first. Future improvement: replace the source JPEG directly with a valid larger-resolution image rather than applying a known checksum repair, improve legacy fallback icon assets and stable signing, validate app icon on phone.


## October 23, 2026 — Compact Portal header + full-width themed realm banner

The user confirmed the Charoite Portal app icon now works, then **requested a layout change and insisted future development be directly implemented in GitHub, never handed off to them to code**. Continue using connected GitHub tools from `functions.exec`, branch `main`. Avoid repeating a false claim that GitHub is unavailable.

**Exact requested UI:** small, bold **Charoite Portal** at the top, **Charoite Core** directly beneath; large, bold current realm name on top of a full-width **themed background behind the text**, NOT an icon beside it.

Implemented:
- `c8128a781a17b9bb0ae52711c8943365450bd647`: `runtime-preview/charoite-core/CharoiteThemes.java` adds reusable `realmBanner(template)` drawable with right-weighted original cherry blossoms for Touhou Realm, violet cosmic portal rings/stars for general/custom realms, masked rounded corners and left-side darkened text area. Existing per-realm wallpaper remains independent.
- `56b3806c1ccd209118e8e83a0f01579259f9c041`: `runtime-preview/TouhouEntryActivity.java` removes large Portal title, logo next to banner and old `heroBackground()` implementation. Places bold `Charoite Portal` at 17sp, subtitle `Charoite Core` at 12sp, then 164dp-tall full-width banner with `CURRENT REALM` caption and active environment name at 34sp, bold white text with truncation for longer names. The banner updates automatically when switching the active environment. The connected page tabs and all Windows game UI remain unchanged.
- `5fba1b3e8ac0456d8a5d7cf1c6693ea7f7ae1d77`: Core architecture README updated, including banner styles and preserving personal wallpapers.

**Verified Android build:** [GitHub Actions 39976065944](https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39976065944) completed **success**, source SHA `5fba1b3e8ac0456d8a5d7cf1c6693ea7f7ae1d77`. APK artifact `touhou-pocket-runtime-preview-apk` id `12512026858`, downloaded ZIP `/mnt/data/Charoite-Portal-Realm-Banners-Build.zip` and extracted `/mnt/data/Charoite-Portal-Realm-Banner-Update.apk`. 231,999,769 bytes, SHA256 `f8b6a090299fe0cd2a79962a1591be33492d1537206f9068b0381fa721f7f1dc`. ZIP/APK CRC verified, 992 APK members and 35 JNI libs, DEX contains `CURRENT REALM`, `realmBanner`, Charoite Portal/Core. The previous working Charoite Portal adaptive icon is still bundled.
**Not physically tested** on a Galaxy S26 Ultra or DeX; Android debug signing may prevent in-place upgrades, so don't suggest uninstalling if app-private saves or installed games have not been backed up.


## October 23, 2026 — Charoite Core v0.4: environment labels, compact realm banner, swipeable tabs

**User feedback from testing custom environments:** Empty library said “Your Gensokyo library awaits” even after switching into a newly created non-Touhou environment. System page still included Touhou Realm description. Current Realm banner too tall. User requests left/right swipe navigation in addition to connected bottom tabs. User expressly requires direct GitHub coding and APK releases (do not give them manual coding instructions).

**Changes implemented in existing `main`:**
- `ec7342c923585c6214c0516fa24e760f9c449386`: New reusable `runtime-preview/charoite-core/CharoiteSwipePager.java`, a ScrollView that recognizes horizontal finger/stylus swipes with slop+direction+minimum-distance requirements, preserves vertical scroll behavior and does not interpret Samsung DeX mouse drags as swipes.
- `23a35de9f93d67d084665668bc842ecaf24a00a0`: `runtime-preview/overlay.py` now compiles `CharoiteSwipePager.java` into Android `com.charoitegames.core`.
- `362fad04fb441d9b8fc75d0644a50b5240375773`: `TouhouEntryActivity.java` replaced native `ScrollView` with `CharoiteSwipePager`; swipe left = next Library→Setup→System, right = previous System→Setup→Library; no wrap; Core connected tabs remain selected through existing `showSection`. Empty library caption is realm-specific: **only Touhou Realm** says Gensokyo, custom/general show the active environment name. Generic System environment description no longer mentions Touhou Realm in other environments; General Gaming already-installed modal no longer claims Touhou-specific context. Setup original Touhou storage reminder only appears in Touhou Realm; other realms see their own independent C: drive description. Realm banner shrunk **164dp → 120dp**, inner paddings/title size/spacings reduced while keeping large bold realm text and themed backgrounds.
- `a7cb053ddef31c10b322473b684aabdd949ffd43`: `CharoiteCore.VERSION = "0.4"`.
- `5c9c1b159e2ad39dcb1ad631b08fa921cbf7320e`: Core README documents swipe and UI behavior.

**Verified GitHub Actions APK:** build run [39980807125](https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39980807125), conclusion **SUCCESS**, head `5c9c1b159e2ad39dcb1ad631b08fa921cbf7320e`. Artifact ZIP `/mnt/data/Charoite-Portal-Swipe-Tabs-Build.zip`, `touhou-pocket-runtime-preview-apk` artifact ID `12512429370`, extracted **`/mnt/data/Charoite-Portal-Swipe-Tabs-v0.4.apk`**, **232,001,065 bytes**, SHA256 **`2729a04ece3387d139c1ee52fd2a669e72dfaa4105f2b893fe8e288f12a3f4e9`**. ZIP and APK CRC checks clean; DEX includes `CharoiteSwipePager`, `CharoitePageTabs`, `CharoiteEnvironments`, `CharoiteWallpaper`, Portal branding; 35 native JNI libraries; adaptive launcher icon XML + approved Charoite image + Japanese 32/64-bit hooks present. Actual horizontal swipe/scroll interplay and banner dimensions still need physical Galaxy/DeX testing.

**Safety:** Existing `com.touhoudr` Android package ID, separate Wine C drives, saved game libraries, Touhou game storage, and wallpaper files are unchanged. Debug-signing key may mismatch installed APK; never suggest uninstalling the installed app without backed-up game data/saves. No game data migration or deletion performed.


## October 23, 2026 — Charoite Core v0.5: reliable swipe + portable .cenv environment files

User tested v0.4: left/right swipes did not reliably navigate Library/Setup/System. "Install Environment" incorrectly offered automatic General Gaming template installation instead of selecting a previously downloaded profile. Creating a new environment must save a shareable file on the user's phone. **User explicitly requires all source modifications to be done directly in GitHub**; do not give coding tasks for user to implement.

**Implemented on existing `main`:**
- `b463e2489b94c40933b697c5730b067f9311ccb2` revises `runtime-preview/charoite-core/CharoiteSwipePager.java`. It observes descendant touch streams in `dispatchTouchEvent()` rather than relying on `ScrollView.onInterceptTouchEvent()`, which skipped horizontal swipes when children consumed events. Identifies clear single-finger/stylus left/right gestures, leaves vertical scrolling/Android edge-back/DeX mouse and long-press tile drags alone, and requests page switch after Android child event delivery. Does not wrap the tabs. **Android compile passed but needs real hardware gesture testing**.
- `7c93e08140add41a761bc9e285ed7d4c907ad94d`: New Core `CharoiteEnvironmentFiles.java`. Portable extension **`.cenv`**; human-readable UTF-8 JSON schema v1 with `format: "com.charoitegames.portal.environment"`, `version: 1`, `name` (1–48 chars), `theme` (`cosmic` or `sakura`), and `settings` containing `compatibilityGraphics`, `displayMode`, `capturePointer`. Maximum 16 KiB, strict primitive types and JSON keys. Profile does **not** include games, saved data, Wine prefixes, installed Windows software, wallpapers, executable code, personal paths or credentials.
- `6ee6a1d70769c395cced33dc8224b867d153c689`: `CharoiteEnvironments.create(host, name, theme)` and `installFromFile()`; re-import creates an isolated Wine container and a new unique name if necessary, never overwriting existing environments.
- `88b0de5eae14eb5ff969fda405a58068c85b3464`: `CharoiteThemes` supports the portable `sakura` theme on custom/imported realms without enabling the Touhou-only installer hooks.
- `798ce24294d4da07f64dc54649cab3c7e4a15cd5`: `runtime-preview/overlay.py` packages new portable Core class.
- `0a86b1f13fb877954987937868ba70940da73695` and `e45d1c3933167a45bd0c0d43246241b389e02b38`: `TouhouEntryActivity` adds **Install Environment** using Android `ACTION_OPEN_DOCUMENT` and `.cenv` extension/schema checks, with a name/theme confirmation; no auto-install presets. **Create Environment** asks name then `ACTION_CREATE_DOCUMENT` ("Save As") with `.cenv` filename, writes profile to selected phone folder, and only registers a local realm after successful write; canceled Save As doesn't create a realm. **Export Environment (.CENV)** saves existing active realm settings for reuse. Saves/exported profiles use app-safe `ContentResolver` stream providers and Android's file picker; no blanket storage permissions.
- `7be6dbb8ee6b9d5b079b1ee553e9bd294362c59c`: Profile-import confirmation dialog before provisioning a new independent environment, and guard on export if current selected realm changed.
- `9381ce607a9813e37ee2de22467c0c77ef208c56`: `CharoiteCore.VERSION = "0.5"`.
- `b89137f38216ceb9fa9f3048413402f98629c8ed`: Example downloadable `environment-profiles/General-Gaming.cenv` in repo. `deec0285b0dc19c75bf523dfbc089bfa5ceb2b10`, `b492fecca1e423aea5ec17b0ea2986233ca17fdb`, `65d278e8f4e2960fdd788aab766b2649de618b37` update format docs and Core/README.

**Verified build:** GitHub Actions [run 39984272284](https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39984272284), head `b492fecca1e423aea5ec17b0ea2986233ca17fdb` (later README-only head is `65d278e8f4e2960fdd788aab766b2649de618b37`), conclusion **SUCCESS**. Artifact `touhou-pocket-runtime-preview-apk`, ID `12514458011`, downloaded ZIP `/mnt/data/Charoite-Portal-v0.5-Portable-Environments.zip`; extracted APK `/mnt/data/Charoite-Portal-v0.5.apk`, **232,004,905 bytes**, SHA256 **`449c7ab665a8c6bcc145115da88df0b177deb8bbb3f80c90a953587c24b7d167`**; ZIP/APK CRC integrity tests passed; classes `CharoiteEnvironmentFiles` and `CharoiteSwipePager` and `.cenv` format string found in dex; working Charoite adaptive icon and 35 JNI native libraries still present. Also local test file `/mnt/data/General-Gaming.cenv` available for download, same manifest as sample in repository.

**Important safety:** Keep Android package ID `com.touhoudr`; preserve game data and prior Wine prefixes. `.cenv` is a small declarative settings profile, **not** a self-contained Windows environment backup or game save archive. Android Files Save As dialog lets user choose storage location. Debug APK signing may prevent in-place update, **never suggest uninstalling** a version with unbacked-up game data. Real S26 Ultra and DeX testing still needed for swipe, SAF provider behavior and user-experience validation.


## October 23, 2026 — Charoite Core v0.6: no visible legacy Winlator branding; game auto-rotation

User's feedback: "Why is there still winlator underneath. Winlator should be gone completely" and "Also I need to be able to rotate the screen not just for the Charoite portal but also when installing games or playing games. Should auto rotate and adjust screen when I rotate phone." Continue **direct GitHub changes on `main`**, ChatGPT sole developer. Preserve game data and existing Android package `com.touhoudr`.

**Implemented in GitHub:**
- `1178eef84aaa5989f0decb61be7ea49d3c3a161d`: Main Portal System footer no longer refers to Winlator as visible app branding; bundled legal notices still credit upstream.
- `877dee8c129857581a8b9f239df837b2483c73fc`: `runtime-preview/overlay.py` patches translated `values-pt` and `values-ru` app labels and foreground service messages (previously displayed Winlator via Android locale override) and explicit Android application `@string/app_name`.
- `7c1fae858de1bebe21db37f5bf39fdaf85222ae6`: Portal + Windows game/installer activities use `android:screenOrientation="fullSensor"`, game activity `configChanges` handles orientation/screen/density/UI mode; removed forced `SCREEN_ORIENTATION_SENSOR_LANDSCAPE` in XServer setup, allowing physical rotation of installation and gameplay activities.
- `685f38fb505d15baeb6ce43131f72e9294773fdb`: Winlator-derived `XServerDisplayActivity` retains live Wine process through `onConfigurationChanged`; requests updated Android XServer rendering and touch overlay layout. The upstream GLSurfaceView calls GLRenderer.onSurfaceChanged automatically and remaps framebuffer to new surface size.
- `36668f8b8588048863234946c11e05e31f590cae`: ForegroundService notification was still explicitly titled "Winlator" and when no session active routed to hidden old MainActivity. Now "Charoite Portal" and notification taps target the Portal activity. New foreground channel ID `charoiteportal.FGS` so old OS channel title isn't reused; wake lock label updated. The optional upstream AboutDialog no longer advertises winlator.org as the app homepage. Third-party attribution and LGPL notices are explicitly preserved in APK.
- `b2cb38185456fba65814364072b2d705590ad2b5`: Charoite Core `VERSION="0.6"`, adaptive Wine startup resolution (portrait: 600×800/720×1280/900×1600/1080×1920; landscape: existing 800×600/1280×720/1600×900/1920×1080) for future installer/game launches. Respects DeX screen geometry and per-environment graphics/display settings.
- `bc77f33d73945536c5c56ae32adbac5ab90dbdc6`: Overlay whitelist allows corresponding portrait Wine virtual desktop sizes and all XServer exit paths return to Charoite Portal instead of restarting the legacy Winlator UI.
- `97b7f477d74e8efd29e839b2c540f4676be8f431`: README updated for v0.6; `68c70c8288702380cbaecfcc81717ea90112f699`: Core README v0.6 documentation.

**Verified APK:** GitHub Actions run [40004236613](https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/40004236613), branch main runtime source SHA `bc77f33d73945536c5c56ae32adbac5ab90dbdc6`, conclusion **success**. Artifact `touhou-pocket-runtime-preview-apk` ID `12524100560`; downloaded ZIP `/mnt/data/Charoite-Portal-v0.6-Auto-Rotate-Build.zip`; extracted installer **`/mnt/data/Charoite-Portal-v0.6-Auto-Rotate.apk`**, size **232,006,137 bytes**, SHA256 **`abf18dfb8d942d253eb40c098423c178dad51ca837b2226a7bafb898309e0672`**. ZIP/APK CRC checks pass; 992 APK members, 35 native .so files, correct Charoite icon JPEG and modern adaptive icon resources, old Touhou Japanese font hooks and CharoiteCore/SwipePager/EnvironmentFiles classes intact. CI also checks app label.

**Limits/caveat:** This removes **visible Winlator branding and legacy launcher routing**, not the Winlator-derived Wine/Box64 implementation itself. Retain legal attribution to upstream open-source code in bundled notices. Native Wine/X11 root resolution is **fixed when a guest session starts**, so during mid-game phone rotation the display adapts its Android viewport and live game view, but the actual Wine desktop resolution isn't dynamically renegotiated until the next launch (fixed aspect ratio games may letterbox). Do not claim seamless in-session Wine desktop resizing. Real Samsung Galaxy S26 Ultra portrait/landscape and DeX tests still needed. APK debug signing may block in-place upgrade; don't suggest uninstalling while Wine saves aren't backed up.


## October 23, 2026 — Charoite Portal v0.7: Inno Setup Additional Tasks Japanese glyph issue

**User screenshot:** `/mnt/data/157103.jpg` displays TPDP/幻想人形演舞 Inno Setup **Select Additional Tasks** page with legible Japanese title/headings/buttons but corrupted checkbox/task label glyphs. User says additional characters didn't convert to Japanese. Confirmed screenshot is not uniformly lacking Japanese support. Prior CP932 probe showed `GetACP=932`, and `TouhouJapaneseSupport.java` already registers Noto CJK + IPA Gothic fonts. Previous helper only fixed original Japanese game install path `TEdit`, not owner-drawn wizard task controls.

**Direct GitHub changes on existing main:**
- `48fd021102d4cdcf4f812a9d9a670278247668e4` modifies `runtime-preview/touhou_font_hook.c` (v2): in-process, thread-local WH_GETMESSAGE hook now scans later `TWizardForm` pages at 500ms intervals and installs Japanese IPAPGothic/SHIFTJIS_CHARSET GDI fonts for deficient text controls and checklist/listbox widgets. It verifies unchanged UTF-16 text before retaining the font; no edits to installer code, translated strings, games, paths or saves. Logs bounded task-list raw UTF-16 hex units locally for diagnosing already-broken strings.
- `adf3c28a788a6c979c913e4cf06262d12038abeb`: `runtime-preview/touhou_font_helper.c` (v2) keeps the installer-scoped thread hook active up to 5 minutes or until the original installer GUI thread exits, instead of prior 18 seconds. Controls on later pages can therefore receive the fix.
- `ad9b562b41102ab7c61ed9e223925bef780e1f1c`, `f25bffaf720f92d91ad0b7203b4cbd2ac6519fb1`: `runtime-preview/TouhouJapaneseSupport.java` refreshes app-bundled Windows helper EXEs/DLLs in **existing** Touhou Wine prefix using new `.touhou-japanese-helpers-v2` marker. This is essential: old path copied helpers only if files missing, so updated APK wouldn't update helper code. Underlying user-owned Wine prefix and game installations are preserved.
- `279c8144e93015a30fe4ac48bc4840df72ee8d4d`: scope task-list diagnostic codepoint logging to actual CheckListBox control.
- `82624c11a355a2275b8a704f5c4f458fa7ed2bcf`: `CharoiteCore.VERSION="0.7"`.
- `42d7e79cddb584cb33ac1dfb1c33a839f72479da`: Core README documents compatibility and diagnostic limitations.

**Successful GitHub Actions build:** https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/40006398200, conclusion `success`, runtime build SHA `279c8144e93015a30fe4ac48bc4840df72ee8d4d`. Artifact `touhou-pocket-runtime-preview-apk`, artifact ID `12523878056`; downloaded ZIP `/mnt/data/Charoite-Portal-v0.7-Japanese-Task-Fix-Build.zip`; extracted installable APK **`/mnt/data/Charoite-Portal-v0.7-Japanese-Font-Fix.apk`**, **232,008,941 bytes**, SHA256 **`48d349d46f0422db4a973bd4aefb50715bb095d4990e6d282d5b2ca9a8479610`**. ZIP+APK CRC tests passed, native libraries count 35, app icon assets, new 32-/64-bit font helpers, and v2 marker present.

**Important limitation:** GUI font changes can fix missing Japanese glyphs in ownerdrawn controls; if the optional-task strings were **already converted incorrectly** into Unicode, fonts alone cannot recover them. In that case ask user to open **System > Launch Diagnostics** and copy the `touhou_font_hook.log` section, particularly the `task-0 utf16` and `task-1 utf16` lines to identify the original mis-decoding safely before doing a narrowly scoped repair. Do not claim proven corrected on Galaxy until user tests. Don't replace original game EXE or alter target install folder, saves, existing `com.touhoudr` APK identity. Debug APK signing caveat remains.


## October 23, 2026 — Charoite Portal folder-import auto-execution fix (Core v0.7)

**User report:** Pressing Setup → Select Game Folder → Android Files "Use this folder" automatically opened the Windows EXE/setup.exe. **Expected:** Folder selection only imports files and registers game in active environment; running any executable requires another explicit user action. The user consistently expects ChatGPT to implement directly via connected GitHub rather than asking them to change code.

**Cause:** In `runtime-preview/TouhouEntryActivity.java` `importGame(uri, folder)`, after copying/detecting an EXE, the UI called `if (launchInstaller) launchGame(selectedPath, true)` for both folder imports and explicit standalone installer imports whenever `isLikelyInstaller(executable)` matched. `detectExe` also prioritized setup.exe over playable game EXEs for non-Touhou-preferred names.

**Direct GitHub changes on existing `main`:**
- Commit `c4ae6dc146ace1f7c03dda98224418ed6aac64e1`: Distinguishes `standaloneExeSelection = !folder`. Folder imports, regardless of the chosen EXE or installer flag, **never call launchGame**; game EXE appears as a tappable Library tile, installer-only folder appears on Setup with explicit **RUN INSTALLER** button. Explicit **Select Installer .EXE** retains its intentionally auto-starting Windows setup wizard. `detectExe` prefers noninstaller candidates over setup.exe when a folder has both. Card copy/button clarified, "RUN INSTALLER AGAIN" changed to "RUN INSTALLER" because the imported folder may not have run yet. Does not delete prior game data.
- Commit `a34844ad420db672618ba0d923ea1cdd0ae0f212`: `runtime-preview/tests/test_folder_import_contract.py` contains regression checks for folder-import no-launch, playable EXE preference, manual installer control and explicit Library tile launches.
- Commit `e03d226589241c4bd3473c754b411a973db7ac6e`: GitHub Actions now runs regression tests right after checkout, before the Android build.
- Commit `0ad40a0f6ccb5ad2337d3f4015e13c2f3e9ea9b4`: README documents the distinct flows.

**Verified build:** GitHub Actions [40009067024](https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/40009067024), conclusion **SUCCESS**, source SHA `e03d226589241c4bd3473c754b411a973db7ac6e`; import regression tests **passed**; Android build succeeded. Artifact `touhou-pocket-runtime-preview-apk` ID `12526215429`, downloaded ZIP `/mnt/data/Charoite-Portal-Folder-Import-Fix-Build.zip`, extracted verified APK **`/mnt/data/Charoite-Portal-Folder-Import-Fix.apk`**, **232,009,413 bytes**, SHA256 `f3cff2fc16bb98abe0a9c74f8406ad65150d6fdf681b73df1ff9f7ba349e38b2`. ZIP and APK CRC checks pass; APK contains 992 files, 35 JNI libraries, DEX includes installer-folder import message, RUN INSTALLER, Portal/Core classes. Existing Core version is **v0.7**. On-device behavioral verification still needed on Galaxy phone.

**Update safety:** Android ID `com.touhoudr` and Wine/game save paths unchanged. No intentional changes to native engine, Japanese installer glyph fix, wallpaper, environments or user data. Debug signature mismatch can prevent update; don't suggest uninstalling without backups.


## 2026-10-23 — Charoite Core v0.8: mandatory Core ownership refactor

**User explicitly directed:** "These changes should have been applied to the Charoite core" (about game-folder importing not starting EXEs), followed by "All japanese character fixes should have been also applied to the core". ChatGPT must make all code changes directly in connected GitHub on **existing `main`**. No manual coding prompts, no alternative developer. Preserve historical package **`com.touhoudr`** and existing user-owned game data.

**Implementation now Core-owned:**
- `runtime-preview/charoite-core/CharoiteGameImport.java`: New reusable SAF folder & standalone installer selection/copy, bounds (max 6 GiB, 12k files, depth 12), filename/canonical checks, failure cleanup **limited to new import directory**, Touhou EXE preferences, generic preference for playable EXE over `setup.exe`, and centralized `shouldLaunchAfterImport(Selection)` policy. Folder selection **NEVER** autoruns Windows code; only an explicitly selected standalone installer launches automatically. Preserve Touhou's original `C:\TouhouPocket\` staging and other realms' `C:\CharoitePortal\` inside independent Wine prefixes. Source first added commit `5e36a138192b8f83fc78b12e634a739784f9bd13`.
- `runtime-preview/TouhouEntryActivity.java`: Refactored old copyFolder/writeFile/detectExe/isLikelyInstaller/deleteTree implementation out of Portal. It now delegates to `CharoiteGameImport.importSelected` and follows Core's `shouldLaunchAfterImport`. Portal still owns Library UI and saves tile metadata, as intended. Committed `c0d0381232d0f0c0e3f4043bae2556d23afd12e3`.
- `runtime-preview/charoite-core/CharoiteJapaneseSupport.java`: Moved complete Japanese support code (Noto/IPA Gothic fonts, locale, Wine ACP/OEMCP=932, font substitutions, existing-prefix v2 helper refresh) into Core package. `runtime-preview/charoite-core/japanese/` now holds `build_japanese_support.py`, `touhou_probe.c`, `touhou_font_helper.c`, `touhou_font_hook.c`. The old duplicate root-level source files were **deleted** to prevent divergence; helper asset names remain as before for on-device migration. The scoped 32/64-bit task-list font fix remains part of this Core source; it only runs against the known Touhou setup.exe, not arbitrary Windows games.
- `runtime-preview/charoite-core/CharoiteCore.java`: `VERSION="0.8"`, new `japaneseCompatibilityEnabled(Context)` and `setJapaneseCompatibilityEnabled(AppCompatActivity, boolean)` per-environment policy. **Touhou Realm defaults ON**, other realms default OFF; user can opt in under **System → Japanese Text Support**. `useTouhouInstallerFontProbe` still scopes the original TPDP in-process helper to Touhou. Commit `83bde54c8983e224a8d51910b63d8cc57db9ef10`.
- `runtime-preview/overlay.py`: Packages new Core Java modules; sets Japanese Wine LANG/LC_ALL via Charoite Core policy; calls `CharoiteJapaneseSupport.ensure`; sources Win32 helper binaries from Core tree and limits Touhou font monitor to Core policy. Commit `7fdd5176f7c6163ab64792b5461192f893a43123`.
- `.github/workflows/runtime-preview.yml`: Builds licensed Japanese fonts/locale and C helper binaries from Core's owned paths; stages legal attribution copies from those same sources. Commit `e41287918ec3ce0b0b3ee348751d702dc400d46d`.
- `runtime-preview/charoite-core/CharoiteEnvironmentFiles.java` adds optional boolean `settings.japaneseText` to backward-compatible schema v1; `TouhouEntryActivity` imports/exports per-realm Japanese support through `.cenv`. Earlier profiles lacking the optional key remain valid.
- `runtime-preview/tests/test_folder_import_contract.py` now verifies Core—not Portal—owns no-autolaunch policy, file copying and Japanese support; Python tests run as an early Android Actions gate. Commit `7dc746a61b485b770ab0380b87cef032dccf9ff4`.
- Docs updated in `runtime-preview/charoite-core/README.md`, root README, `environment-profiles/README.md`.

**Verified build:** GitHub Actions run **40016435916** (https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/40016435916), conclusion **SUCCESS**, build SHA **`a1d619ce84a40d025d5e20639d79b517ee1318b5`**. Artifact `touhou-pocket-runtime-preview-apk` ID **12528133561**; ZIP `/mnt/data/Charoite-Portal-v0.8-Core-Refactor-Build.zip`; extracted direct install APK **`/mnt/data/Charoite-Portal-v0.8-Core-Refactor.apk`**, **232,010,589 bytes**, SHA256 **`d977156bfaa968353081b593a8659b341e65c70da19425bb40c60af82aec570c`**. ZIP/APK CRC tested clean; DEX contains `CharoiteGameImport`, `CharoiteJapaneseSupport`, Core locale key and both selection policies; 35 native libs plus four x86 Win32 Japanese helper DLL/EXEs and working Charoite icon present. No error in Actions compile.

**Known limitation:** Compiled but not physically verified on the Samsung Galaxy S26 Ultra. Japanese optional-task checkbox text may remain corrupt if upstream installer data was originally decoded incorrectly; the font hook logs raw task-control UTF-16 for future diagnosis. Existing Wine ACP registry may persist if Japanese support later toggled off in a prefix that had previously enabled it (toggle governs future launcher env overrides/font provisioning). Debug APK signing may prevent in-place upgrade—**do not uninstall existing app containing games/saves without a backup**.

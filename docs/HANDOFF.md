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

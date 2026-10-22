# Touhou Pocket Launcher — direct-launch APK test

**Latest build:** [Touhou runtime GitHub Actions](https://github.com/rgarn023/TouhouPocketLauncher/actions/workflows/runtime-preview.yml) — use the most recent **successful** run. Choose artifact `touhou-pocket-runtime-preview-apk`, extract `app-debug.apk`.

Primary device: Samsung Galaxy S26 Ultra. The Android/graphics stack is not yet confirmed on this phone.

## First run

1. Install the new APK. The splash/home screen should say **Touhou Pocket**, **Game Engine**, and **Your Touhou Library**. **There should be no Winlator container-manager screen.**
2. Tap **Set Up Game Engine**, and confirm the engine eventually says ready. The app extracts a substantial private Windows runtime and creates a game environment. It may require several GB of free storage.
3. Tap **Import Game Folder** and choose your unpatched TPDP **base game** folder. Android's file selector cannot always select Downloads root; choose a subfolder.
4. Once the import finishes, select **Play**. The app launches a detected EXE through its internal Wine display without opening Winlator's container manager.
5. If you have an EXE *installer* instead, choose **Import Windows Game Installer (.EXE)**. Run it from the library. After installation, press **Find Installed Touhou Games** and Play the identified game.

## What to report

- Does the APK install and show the native Touhou library?
- Does **Set Up Game Engine** finish successfully, or report an error?
- Does a complete TPDP base-game folder import successfully?
- On Play, does the game's window appear? Is the sound/input working and gameplay smooth?
- If it fails, share **exact** screen/error message, a screenshot or short video, and whether failure occurred during setup, import, or Play.

## Scope and caveats

- **No separate Winlator installation is required.** Existing Winlator installations can remain, since the APK uses its own package name.
- The underlying Windows renderer and its emergency control overlay still use upstream runtime components. The separate *Winlator launcher/container manager* is not part of the user-facing flow.
- No English-patch automation or Extended DLL override has been implemented yet. The Kotlin `notkey` symlink helper is tested but not hooked into this integrated APK.
- Tests on GitHub confirm APK compilation only. They **do not** verify game execution on Android.
- Save files and imported games live in the APK's app-private directory. Uninstalling or clearing app data can remove them; avoid saving irreplaceable data yet.
- Debug APK updates may cause signature problems if signing differs; keep backups.


## Box64 EACCES correction test
Earlier app was packaged as games.charoite.touhoupocket.runtime but embedded ARM64 Box64 and some libraries still pointed to /data/data/com.winlator. This mismatch caused launch failure before setup.exe.
New build from the latest successful Touhou Wine Runtime Preview workflow uses Android ID com.touhoupk and label Touhou Pocket Test. It rewrites runtime native binary paths, including the Box64 ELF loader and graphics cache paths.
Keep the previous APK installed; the new ID installs separately and does not migrate old app-private files or saves. Install the new APK, Set Up Game Engine, import your original complete game or installer folder, and press Play or Run Installer.
If it fails again, open View Last Launch Diagnostics > Copy Report and share full text. Report should include Box64 native exists/execute and glibc loader status. CI build success is not device success.


## Japanese text support test (October 22, 2026)
Once a newer `Touhou Pocket Test` APK with the Japanese language pack has successfully built:
1. Keep a copy of imported games/saves before replacing any debug-signed APK. If the Android update fails due to signature conflict, **do not immediately uninstall**.
2. Run `Set Up Game Engine` if asked. Existing prefixes should receive the Japanese locale/font addon without deleting game content.
3. Select the imported full Puppet Dance Performance installer and press `Run Installer`.
4. Verify the installer's **Japanese kana/kanji**, dialog buttons, and Japanese folder names display and install correctly rather than mojibake/squares.
5. If display is still garbled, provide a screenshot and `View Last Launch Diagnostics` report. This helps distinguish codepage mismatch from missing glyphs.
6. Do not apply translations or Shard of Dreams/Extended until unpatched base-game installation is stable.

The font is Noto Sans CJK JP, SIL OFL 1.1, sourced from a pinned official revision and distributed with its license in the APK. Wine is configured for `ja_JP.UTF-8` and the Windows font faces MS Gothic / Meiryo alias to Noto; native Android app labels remain English.


### Current Japanese-language APK installs separately

Current test package: `com.touhoujp`, label **Touhou Pocket JP Test**. It can coexist with the working `com.touhoupk` Box64 test app, avoiding debug signing conflicts and protecting existing imported files. After installing the new app, tap **Set Up Game Engine**, reimport the complete original TPDP installer files, run setup and check that Japanese text displays correctly. Once tested, report what appears and share screenshots if glyphs are still garbled. Wine and Box64 are still bundled and the interface stays Touhou-focused.

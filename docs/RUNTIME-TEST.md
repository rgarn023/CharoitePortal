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

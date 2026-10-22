# Runtime preview: Android device test checklist

**Build:** [Touhou Wine Runtime Preview Actions run 39787333874](https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39787333874)

**Test device:** Samsung Galaxy S26 Ultra / Android 17 (primary target). The APK is an experimental source-based adaptation of Winlator, not a full TPDP launcher yet.

## Verify installation

1. Download the GitHub Actions artifact `touhou-pocket-runtime-preview-apk` and extract `app-debug.apk`.
2. Install the debug APK. Do not uninstall a separate Winlator installation; this preview has its own package ID: `games.charoite.touhoupocket.runtime`.
3. Open the app. The first page should say "Touhou Pocket Launcher" with an **Open Windows Runtime** button.
4. Tap the button; Winlator's unmodified setup/UI should open. Allow its unpack/setup to finish. The preview includes source-built Wine/Box64/graphics resources.
5. Verify the runtime can create a container, show its display, and exit cleanly.

## Game compatibility smoke test

Use your own legally obtained **TPDP base game**, without patches or expansions.

- Import files through a folder accessible to the Winlator container (typically a bound Downloads/storage location).
- Attempt its Windows setup/launch. Note whether the installer window or game opens.
- Verify stable input and audio and observe game speed on actual hardware.
- Save and close; re-open and verify save persistence.
- Only after the base game passes, attempt **Shard of Dreams** in the *same compatible Wine environment*.
- Only after the expansion passes, attempt compatible **standalone English patches** and **Extended** separately.
- Record the actual Windows error messages and log/screenshot/video when something fails.
- The `notkey` workaround is available as a tested helper in the Kotlin starter but is **not yet wired into the runtime preview**. Older Wine versions may need it; don't create a fake file or overwrite an existing `notkey` entry.

## Report
- Did the APK install and did its first-launch rootfs installation finish?
- Was the initial runtime container creatable?
- Which exe was launched and did game/installer open?
- Any black screen, missing fonts, audio trouble, bad controls, game crash, or thermal throttling?
- Which Wine/graphics renderer was active, if known?
- Screenshots/logs are optional; never upload game installers/content into the public GitHub repository.

## Technical identity

The runtime overlay is in `runtime-preview/`; the pinned, upstream LGPL source revision is `8077f374ef2d54127b088de9e8cd7b4af14d9c8b` of `brunodev85/winlator-app`. **GitHub Actions success proves Android build and packaging, not successful phone execution.**

## Future acceptance criteria

- One APK combines the dedicated game library with its Wine runtime.
- App checks base-game and expansion version, install order, portable EXE and installers.
- Restorable backups before English patch writes, no thcrap dependency.
- Shard of Dreams starts without missing base-game path or `notkey` error.
- Extended custom `dxgi.dll` is loaded with the appropriate Wine override.
- Touch controls and Bluetooth controller work; native-rate frame pacing and correct audio.
